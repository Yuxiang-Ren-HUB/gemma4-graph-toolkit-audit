"""Shared utilities for the offline audit of the Gemma 4 Developer Agent
code-graph toolkit.

All analyses run offline on the competition data release:
  DATA_DIR/tasks.jsonl        129 SWE-bench-style task records
  DATA_DIR/graphs/*.json      per-(repo, base_commit) call graphs (node-link JSON)
  DATA_DIR/embeddings/*.npz   per-(repo, base_commit) node-name -> vector archives
  DATA_DIR/snapshots/*.tgz    repository trees at base_commit

The audited implementation is the official `swegemma` wheel shipped in the
competition wheelhouse.  We import its graph modules unmodified (bypassing the
package __init__, which pulls in evaluation-only dependencies) so every number
reported reflects the exact shipped code path.
"""

from __future__ import annotations

import ast
import importlib
import io
import json
import keyword
import os
import re
import sys
import tarfile
import types
import zipfile

PAPER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PAPER_DIR)                     # F:/kaggle/gemma_agent
DATA_DIR = os.environ.get("AUDIT_DATA_DIR", os.path.join(BASE_DIR, "data"))
GRAPH_DIR = os.path.join(DATA_DIR, "graphs")
EMB_DIR = os.path.join(DATA_DIR, "embeddings")
SNAP_DIR = os.path.join(DATA_DIR, "snapshots")
TASKS_PATH = os.path.join(DATA_DIR, "tasks.jsonl")
WHEELHOUSE = os.environ.get("AUDIT_WHEELHOUSE", os.path.join(BASE_DIR, "wheelhouse"))
VENDOR_DIR = os.environ.get("AUDIT_VENDOR_DIR", os.path.join(PAPER_DIR, "analysis", "vendor"))
RESULTS_DIR = os.environ.get("AUDIT_RESULTS_DIR", os.path.join(PAPER_DIR, "results"))

SWEGEMMA_WHEEL_GLOB = "swegemma-" + os.environ.get("AUDIT_SWEGEMMA_VERSION", "")


def ensure_vendor() -> str:
    """Unzips the official swegemma wheel into analysis/vendor (idempotent)."""
    marker = os.path.join(VENDOR_DIR, "swegemma", "graph", "graph_utils.py")
    if os.path.exists(marker):
        return VENDOR_DIR
    wheel = None
    for name in sorted(os.listdir(WHEELHOUSE)):
        if name.startswith(SWEGEMMA_WHEEL_GLOB) and name.endswith(".whl"):
            wheel = os.path.join(WHEELHOUSE, name)
    if wheel is None:
        raise FileNotFoundError("swegemma wheel not found in wheelhouse")
    os.makedirs(VENDOR_DIR, exist_ok=True)
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(VENDOR_DIR)
    return VENDOR_DIR


def load_swegemma():
    """Imports swegemma.graph.{graph_utils,embedding_utils,retrieval_utils}
    from the vendored wheel without executing swegemma/__init__.py."""
    root = ensure_vendor()
    if "swegemma" not in sys.modules:
        pkg = types.ModuleType("swegemma")
        pkg.__path__ = [os.path.join(root, "swegemma")]
        sys.modules["swegemma"] = pkg
        gpkg = types.ModuleType("swegemma.graph")
        gpkg.__path__ = [os.path.join(root, "swegemma", "graph")]
        sys.modules["swegemma.graph"] = gpkg
    graph_utils = importlib.import_module("swegemma.graph.graph_utils")
    embedding_utils = importlib.import_module("swegemma.graph.embedding_utils")
    retrieval_utils = importlib.import_module("swegemma.graph.retrieval_utils")
    return graph_utils, embedding_utils, retrieval_utils


def load_tasks() -> list[dict]:
    tasks = []
    with open(TASKS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


# ---------------------------------------------------------------------------
# Patch parsing
# ---------------------------------------------------------------------------

def parse_patch(patch_text: str) -> list[dict]:
    """Parses a unified diff into per-file records.

    Returns a list of {path, is_new, src_lines (set of base-file line numbers
    that are removed or serve as insertion anchors), added, removed}.
    A file is `is_new` when its first hunk source range is `-0,0`.
    """
    import unidiff

    files = []
    ps = unidiff.PatchSet(io.StringIO(patch_text))
    for pf in ps:
        src_lines: set[int] = set()
        added = removed = 0
        is_new = pf.is_added_file
        for hunk in pf:
            if hunk.source_start == 0 and hunk.source_length == 0:
                is_new = True
            anchor = max(hunk.source_start, 1)
            pure_insert = True
            for line in hunk:
                if line.is_removed:
                    src_lines.add(line.source_line_no)
                    removed += 1
                    pure_insert = False
                elif line.is_added:
                    added += 1
            if pure_insert and added and not is_new:
                # insertion-only hunk: anchor to surrounding context lines
                ctx = [l.source_line_no for l in hunk if l.is_context and l.source_line_no]
                if ctx:
                    src_lines.add(ctx[len(ctx) // 2])
                else:
                    src_lines.add(anchor)
        files.append({
            "path": pf.path,
            "is_new": bool(is_new),
            "src_lines": sorted(src_lines),
            "added": added,
            "removed": removed,
        })
    return files


# ---------------------------------------------------------------------------
# Snapshot access + AST symbol mapping
# ---------------------------------------------------------------------------

def snapshot_read(instance_id: str, rel_path: str) -> str | None:
    """Reads one file from the task's base-commit snapshot tarball."""
    tgz = os.path.join(SNAP_DIR, f"{instance_id}.tgz")
    if not os.path.exists(tgz):
        return None
    with tarfile.open(tgz) as tf:
        for cand in (f"./{rel_path}", rel_path):
            try:
                member = tf.getmember(cand)
            except KeyError:
                continue
            fobj = tf.extractfile(member)
            if fobj is None:
                return None
            return fobj.read().decode("utf-8", errors="replace")
    return None


def enclosing_symbols(source: str, lines: list[int]) -> list[dict]:
    """Maps base-file line numbers to their innermost enclosing def/class.

    Returns unique records {qualname, bare, kind} ordered by first line hit.
    Lines outside any def/class map to kind='module'.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    spans: list[tuple[int, int, str, str]] = []  # (start, end, qualname, kind)

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qual = f"{prefix}.{child.name}" if prefix else child.name
                kind = "class" if isinstance(child, ast.ClassDef) else "function"
                spans.append((child.lineno, child.end_lineno or child.lineno, qual, kind))
                walk(child, qual)
            else:
                walk(child, prefix)

    walk(tree, "")
    out, seen = [], set()
    for ln in lines:
        best = None
        for start, end, qual, kind in spans:
            if start <= ln <= end:
                if best is None or (start >= best[0] and end <= best[1]):
                    best = (start, end, qual, kind)
        if best is None:
            rec = ("<module>", "module")
        else:
            rec = (best[2], best[3])
        if rec not in seen:
            seen.add(rec)
            out.append({"qualname": rec[0], "bare": rec[0].split(".")[-1], "kind": rec[1]})
    return out


def module_dotted(path: str) -> str:
    """Converts a repo-relative .py path to a dotted module path."""
    p = path[:-3] if path.endswith(".py") else path
    return p.replace("/", ".").replace("\\", ".")


# ---------------------------------------------------------------------------
# Identifier extraction from problem statements (this doubles as the shim)
# ---------------------------------------------------------------------------

_STOP = set(keyword.kwlist) | {
    "self", "none", "true", "false", "print", "return", "import", "test",
    "tests", "python", "error", "issue", "example", "file", "files", "line",
    "code", "type", "types", "value", "values", "object", "objects", "using",
    "with", "this", "that", "should", "would", "could", "have", "will",
}

_BACKTICK = re.compile(r"`([^`\n]{2,120})`")
_DOTTED = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b")
_SNAKE = re.compile(r"\b[a-z_][a-z0-9]*_[a-z0-9_]+\b")
_CAMEL = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+\b")


def _clean_token(tok: str) -> str | None:
    tok = tok.strip().strip('.,;:!?"\'')
    tok = re.sub(r"\(.*\)$", "", tok)          # drop call args
    tok = tok.strip("()[]{}<>")
    if not tok or " " in tok or "\n" in tok:
        return None
    tok = tok.rstrip(".")
    if len(tok) < 3 or tok.lower() in _STOP:
        return None
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", tok):
        return None
    return tok


def extract_identifiers(text: str, cap: int = 40) -> list[str]:
    """Extracts code-like identifiers from free text, best-first:
    backticked spans, dotted paths, snake_case, CamelCase."""
    out: list[str] = []
    seen: set[str] = set()

    def add(tok):
        cleaned = _clean_token(tok)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            out.append(cleaned)

    for m in _BACKTICK.finditer(text):
        span = m.group(1)
        for sub in re.split(r"[\s,]+", span):
            add(sub)
    for rx in (_DOTTED, _SNAKE, _CAMEL):
        for m in rx.finditer(text):
            add(m.group(0))
    return out[:cap]


def content_keywords(text: str, n: int = 5) -> list[str]:
    """Most frequent plain English content words (len>=4), the query shape the
    harness prompt suggests ('by keyword')."""
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w in _STOP:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:n]]


# ---------------------------------------------------------------------------
# Gold-hit predicates (strict, two tiers)
# ---------------------------------------------------------------------------

def node_matches_symbol(node_id: str, qualname: str, bare: str) -> str | None:
    """Returns 'qual' for a qualified-suffix match, 'bare' for a bare-name
    boundary match, else None.  Deliberately stricter than the toolkit's own
    resolve_node_name (no substring tier)."""
    if qualname != "<module>":
        if node_id == qualname or node_id.endswith("." + qualname):
            return "qual"
    if node_id == bare or node_id.endswith("." + bare):
        return "bare"
    return None


def save_json(name: str, obj) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return path
