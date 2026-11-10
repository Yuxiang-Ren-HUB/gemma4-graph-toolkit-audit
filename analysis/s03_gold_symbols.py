"""s03: Derives gold edit symbols for every task from the gold patch plus the
base-commit snapshot (AST mapping of changed base lines to enclosing
functions/classes).  New files contribute no base symbols by construction."""

from common import (load_tasks, parse_patch, snapshot_read, enclosing_symbols,
                    module_dotted, save_json)


def main():
    tasks = load_tasks()
    rows = []
    for t in tasks:
        files = parse_patch(t["patch"])
        gold = []
        n_new_py = n_mod_py = n_non_py = 0
        for f in files:
            if not f["path"].endswith(".py"):
                n_non_py += 1
                continue
            if f["is_new"]:
                n_new_py += 1
                continue
            n_mod_py += 1
            src = snapshot_read(t["instance_id"], f["path"])
            if src is None:
                gold.append({"file": f["path"], "qualname": "<file-missing>",
                             "bare": "", "kind": "missing"})
                continue
            for sym in enclosing_symbols(src, f["src_lines"]):
                gold.append({
                    "file": f["path"],
                    "module": module_dotted(f["path"]),
                    "qualname": sym["qualname"],
                    "bare": sym["bare"],
                    "kind": sym["kind"],
                })
        rows.append({
            "instance_id": t["instance_id"],
            "repo": t["repo"],
            "base_commit": t["base_commit"],
            "n_new_py": n_new_py,
            "n_mod_py": n_mod_py,
            "n_non_py": n_non_py,
            "gold_symbols": gold,
            "n_gold_syms": sum(1 for g in gold if g["kind"] in ("function", "class")),
            "module_level_only": bool(gold) and all(
                g["kind"] == "module" for g in gold),
            "adds_only": n_mod_py == 0 and n_new_py > 0 and not gold,
        })

    n = len(rows)
    summary = {
        "n_tasks": n,
        "tasks_adds_only_py": sum(r["adds_only"] for r in rows),
        "tasks_with_ge1_gold_sym": sum(r["n_gold_syms"] >= 1 for r in rows),
        "tasks_module_level_only": sum(r["module_level_only"] for r in rows),
        "tasks_file_missing": sum(
            any(g["kind"] == "missing" for g in r["gold_symbols"]) for r in rows),
        "total_gold_syms": sum(r["n_gold_syms"] for r in rows),
    }
    path = save_json("s03_gold.json", {"summary": summary, "tasks": rows})
    print("wrote", path)
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
