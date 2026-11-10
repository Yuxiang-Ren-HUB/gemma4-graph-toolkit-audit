"""End-to-end probe of the 0.2.11 tool wrapper: a free-text query through tools.graph.search_similar_code."""
import json, sys, os, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor"))
from common import load_tasks, GRAPH_DIR, EMB_DIR
from swegemma.tools import graph as tg

tasks = load_tasks()
for t in tasks[:3]:
    ctx = types.SimpleNamespace(task={"repo": t["repo"], "base_commit": t["base_commit"]}, repo=t["repo"],
                                graph_dir=GRAPH_DIR, embeddings_dir=EMB_DIR, max_stdout_chars=5000,
                                check_budget=lambda **kw: None)
    q = t["problem_statement"].strip().splitlines()[0][:200]
    r = json.loads(tg.search_similar_code(ctx, q))
    print(t["instance_id"], "| query:", q[:70], "| status", r.get("status"), "count", r.get("count"),
          "| keys", sorted(r), "| first", [(x["node_name"], x["similarity"]) for x in r.get("results", [])[:3]])
