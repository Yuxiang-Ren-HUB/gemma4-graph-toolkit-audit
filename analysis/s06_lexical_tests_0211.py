"""0.2.11 only: how often do free-text queries through the tool wrapper return test functions (which an agent may not edit)?"""
import json, os, re, sys, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor"))
from common import load_tasks, GRAPH_DIR, EMB_DIR, save_json
from swegemma.tools import graph as tg

TEST = re.compile(r"(^|\.)(tests?|testing)\.|(^|\.)test_|_test(\.|$)|\.conftest\.")
rows = []
for t in load_tasks():
    ctx = types.SimpleNamespace(task={"repo": t["repo"], "base_commit": t["base_commit"]}, repo=t["repo"],
                                graph_dir=GRAPH_DIR, embeddings_dir=EMB_DIR, max_stdout_chars=5000,
                                check_budget=lambda **kw: None)
    for shape, q in (("full", t["problem_statement"][:500]), ("line", next((l for l in t["problem_statement"].splitlines() if l.strip()), ""))):
        r = json.loads(tg.search_similar_code(ctx, q))
        names = [x["node_name"] for x in r.get("results", [])]
        rows.append({"id": t["instance_id"], "shape": shape, "status": r.get("status"), "n": len(names),
                     "n_test": sum(bool(TEST.search(n)) for n in names), "top1_test": bool(names) and bool(TEST.search(names[0]))})
summ = {}
for shape in ("full", "line"):
    rs = [r for r in rows if r["shape"] == shape and r["n"]]
    summ[shape] = {"tasks_nonempty": len(rs), "status_ok": sum(r["status"] == "ok" for r in rows if r["shape"] == shape),
                   "results": sum(r["n"] for r in rs), "test_results": sum(r["n_test"] for r in rs),
                   "tasks_top1_test": sum(r["top1_test"] for r in rs), "tasks_any_test": sum(r["n_test"] > 0 for r in rs)}
save_json("s06_lexical_tests_0211.json", {"summary": summ, "rows": rows})
print(json.dumps(summ, indent=1))
