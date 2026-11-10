"""s04: Behavioral audit of the shipped code-graph toolkit, executed through
the official swegemma code path (get_similar_nodes / get_neighbor /
resolve_node_name) on all 129 tasks.

Query conditions per task:
  nl_full   : the task's problem statement (docstring invites snippets/NL)
  nl_line   : first non-empty line of the statement
  snippet   : first added lines of the gold patch (a literal 'code snippet')
  keywords  : top-5 plain-language content words ("by keyword", as the
              harness system prompt suggests)
  shim      : code-like identifiers extracted from the statement (the
              symbol-grounding rewrite we propose)
  oracle    : bare names of the gold symbols themselves (upper bound)

Localization hit = a returned node (or the resolved query node itself)
matches a gold edit symbol under the strict two-tier predicate.
Also audits the edge_type filter of get_code_neighbors against the
docstring's advertised 'CALLS'/'DEFINED_IN'/'IMPORTS' examples.
"""

import json
import os

from common import (RESULTS_DIR, GRAPH_DIR, EMB_DIR, load_tasks,
                    load_swegemma, extract_identifiers, content_keywords,
                    node_matches_symbol, save_json)

K = 10
CAP_QUERIES = 15


def match_gold(node_id: str, gold_syms) -> str | None:
    best = None
    for gsym in gold_syms:
        m = node_matches_symbol(node_id, gsym.get("qualname", ""), gsym.get("bare", ""))
        if m == "qual":
            return "qual"
        if m == "bare":
            best = "bare"
    return best


def main():
    graph_utils, embedding_utils, retrieval_utils = load_swegemma()
    tasks = load_tasks()
    gold_data = json.load(open(os.path.join(RESULTS_DIR, "s03_gold.json"),
                               encoding="utf-8"))
    gold_by_id = {r["instance_id"]: r for r in gold_data["tasks"]}

    rows = []
    edge_filter_counts = {"none": 0, "calls": 0, "CALLS": 0,
                          "DEFINED_IN": 0, "IMPORTS": 0}
    edge_filter_nodes = 0

    for ti, t in enumerate(tasks):
        iid, repo, commit = t["instance_id"], t["repo"], t["base_commit"]
        stmt = t.get("problem_statement") or ""
        try:
            g = graph_utils.get_graph(repo, graph_dir=GRAPH_DIR,
                                      embeddings_dir=EMB_DIR, base_commit=commit)
        except Exception as e:
            rows.append({"instance_id": iid, "error": str(e)})
            continue

        gold_syms = [s for s in gold_by_id[iid]["gold_symbols"]
                     if s["kind"] in ("function", "class")]
        node_ids = [str(n) for n in g.nodes()]
        gold_nodes_qual, gold_nodes_bare = set(), set()
        for nid in node_ids:
            m = match_gold(nid, gold_syms)
            if m == "qual":
                gold_nodes_qual.add(nid)
            elif m == "bare":
                gold_nodes_bare.add(nid)
        gold_nodes = gold_nodes_qual | gold_nodes_bare
        gold_emb = sum(
            1 for nid in gold_nodes_qual
            if embedding_utils.embed(nid, repo, embeddings_dir=EMB_DIR,
                                     base_commit=commit) is not None)

        def sim(q):
            try:
                return retrieval_utils.get_similar_nodes(
                    q, repo_name=repo, k=K, graph_dir=GRAPH_DIR,
                    embeddings_dir=EMB_DIR, base_commit=commit)
            except Exception:
                return []

        def run_condition(queries):
            """Returns metrics over a list of query strings."""
            nonempty = 0
            resolve_gold = topk_gold = False
            resolved_any = 0
            for q in queries:
                res = sim(q)
                if res:
                    nonempty += 1
                rn = graph_utils.resolve_node_name(q, g)
                if rn is not None:
                    resolved_any += 1
                    if match_gold(str(rn), gold_syms):
                        resolve_gold = True
                for item in res:
                    if match_gold(str(item["node_name"]), gold_syms):
                        topk_gold = True
            return {"n_queries": len(queries), "n_nonempty": nonempty,
                    "n_resolved": resolved_any,
                    "resolve_hits_gold": resolve_gold,
                    "topk_hits_gold": topk_gold}

        # snippet: first 3 added lines of gold patch
        added_lines = [ln[1:] for ln in t["patch"].splitlines()
                       if ln.startswith("+") and not ln.startswith("+++")][:3]
        snippet = "\n".join(added_lines)

        idents = extract_identifiers(stmt, cap=CAP_QUERIES)
        kws = content_keywords(stmt, 5)
        oracle_names = [nid.split(".")[-1] for nid in sorted(gold_nodes_qual)][:5]

        cond = {
            "nl_full": run_condition([stmt[:500]] if stmt else []),
            "nl_line": run_condition(
                [next((l for l in stmt.splitlines() if l.strip()), "")]
                if stmt.strip() else []),
            "snippet": run_condition([snippet] if snippet else []),
            "keywords": run_condition(kws),
            "shim": run_condition(idents),
            "oracle": run_condition(oracle_names),
        }

        # neighbor-based localization via shim identifiers
        nb_gold = False
        for q in idents:
            try:
                nbs = graph_utils.get_neighbor(q, graph=g)
            except Exception:
                nbs = []
            if any(match_gold(str(nb), gold_syms) for nb in nbs):
                nb_gold = True
                break

        # edge_type filter audit on up to 5 connected nodes per graph
        connected = [n for n in g.nodes() if g.degree(n) > 0][:5]
        for n0 in connected:
            edge_filter_nodes += 1
            for et in ("calls", "CALLS", "DEFINED_IN", "IMPORTS"):
                nbs = graph_utils.get_neighbor(n0, graph=g, edge_type=et)
                edge_filter_counts[et] += len(nbs)
            edge_filter_counts["none"] += len(graph_utils.get_neighbor(n0, graph=g))

        rows.append({
            "instance_id": iid,
            "repo": repo,
            "n_gold_syms": len(gold_syms),
            "n_gold_nodes_qual": len(gold_nodes_qual),
            "n_gold_nodes_bare_extra": len(gold_nodes_bare),
            "gold_in_graph": bool(gold_nodes_qual),
            "gold_emb_present": gold_emb,
            "n_identifiers": len(idents),
            "neighbors_hit_gold": nb_gold,
            "cond": cond,
        })
        if (ti + 1) % 20 == 0:
            print(f"  ...{ti + 1}/{len(tasks)} tasks audited")

    ok = [r for r in rows if "error" not in r]
    with_gold_sym = [r for r in ok if r["n_gold_syms"] >= 1]
    localizable = [r for r in ok if r["gold_in_graph"]]

    def agg(cset, key, pred):
        return sum(1 for r in cset if pred(r["cond"][key]))

    summary = {
        "n_tasks_audited": len(ok),
        "n_tasks_with_gold_syms": len(with_gold_sym),
        "n_tasks_gold_in_graph_qual": len(localizable),
        "nl_full_nonempty_tasks": agg(ok, "nl_full", lambda c: c["n_nonempty"] > 0),
        "nl_line_nonempty_tasks": agg(ok, "nl_line", lambda c: c["n_nonempty"] > 0),
        "snippet_nonempty_tasks": agg(ok, "snippet", lambda c: c["n_nonempty"] > 0),
        "keywords_nonempty_tasks": agg(ok, "keywords", lambda c: c["n_nonempty"] > 0),
        "shim_nonempty_tasks": agg(ok, "shim", lambda c: c["n_nonempty"] > 0),
        # localization among tasks whose gold symbols exist in the graph
        "loc_keywords_resolve": agg(localizable, "keywords", lambda c: c["resolve_hits_gold"]),
        "loc_keywords_topk": agg(localizable, "keywords", lambda c: c["topk_hits_gold"]),
        "loc_shim_resolve": agg(localizable, "shim", lambda c: c["resolve_hits_gold"]),
        "loc_shim_topk": agg(localizable, "shim", lambda c: c["topk_hits_gold"]),
        "loc_shim_resolve_or_topk": sum(
            1 for r in localizable
            if r["cond"]["shim"]["resolve_hits_gold"] or r["cond"]["shim"]["topk_hits_gold"]),
        "loc_neighbors_hit": sum(1 for r in localizable if r["neighbors_hit_gold"]),
        "loc_oracle_resolve": agg(localizable, "oracle", lambda c: c["resolve_hits_gold"]),
        "oracle_nonempty_tasks": agg(localizable, "oracle", lambda c: c["n_nonempty"] > 0),
        "edge_filter_nodes_probed": edge_filter_nodes,
        "edge_filter_neighbor_totals": edge_filter_counts,
    }
    path = save_json("s04_audit.json", {"summary": summary, "tasks": rows})
    print("wrote", path)
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
