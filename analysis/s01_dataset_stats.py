"""s01: Dataset-level statistics over the 129 public tasks."""

import re
import statistics

from common import load_tasks, parse_patch, extract_identifiers, save_json


def main():
    tasks = load_tasks()
    per_repo: dict[str, int] = {}
    rows = []
    for t in tasks:
        files = parse_patch(t["patch"])
        py_files = [f for f in files if f["path"].endswith(".py")]
        new_files = [f for f in files if f["is_new"]]
        mod_files = [f for f in files if not f["is_new"]]
        stmt = t.get("problem_statement") or ""
        idents = extract_identifiers(stmt)
        per_repo[t["repo"]] = per_repo.get(t["repo"], 0) + 1
        rows.append({
            "instance_id": t["instance_id"],
            "repo": t["repo"],
            "n_files": len(files),
            "n_py_files": len(py_files),
            "n_new_files": len(new_files),
            "n_mod_files": len(mod_files),
            "adds_only": len(mod_files) == 0,
            "added": sum(f["added"] for f in files),
            "removed": sum(f["removed"] for f in files),
            "stmt_chars": len(stmt),
            "stmt_words": len(re.findall(r"\S+", stmt)),
            "n_identifiers": len(idents),
            "has_backtick": "`" in stmt,
            "has_hints": bool((t.get("hints_text") or "").strip()),
        })

    n = len(rows)
    summary = {
        "n_tasks": n,
        "per_repo": per_repo,
        "adds_only_tasks": sum(r["adds_only"] for r in rows),
        "tasks_with_new_file": sum(r["n_new_files"] > 0 for r in rows),
        "median_files": statistics.median(r["n_files"] for r in rows),
        "median_added": statistics.median(r["added"] for r in rows),
        "median_removed": statistics.median(r["removed"] for r in rows),
        "median_stmt_words": statistics.median(r["stmt_words"] for r in rows),
        "tasks_with_ge1_identifier": sum(r["n_identifiers"] >= 1 for r in rows),
        "tasks_with_backtick": sum(r["has_backtick"] for r in rows),
        "median_identifiers": statistics.median(r["n_identifiers"] for r in rows),
        "tasks_with_hints": sum(r["has_hints"] for r in rows),
    }
    path = save_json("s01_dataset.json", {"summary": summary, "tasks": rows})
    print("wrote", path)
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
