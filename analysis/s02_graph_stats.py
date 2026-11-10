"""s02: Census of all shipped graphs and embedding archives.

Verifies, across every (repo, base_commit) pair referenced by the 129 tasks:
  - node/edge counts, edge-type set (docstring advertises CALLS/DEFINED_IN/
    IMPORTS filters; what do the data actually contain?)
  - isolated-node fraction (nodes unusable by neighbor/subgraph tools)
  - degenerate node bodies (text missing or placeholder-truncated)
  - embedding key coverage in both directions (graph node <-> npz key)
"""

import collections
import json
import os

import numpy as np

from common import GRAPH_DIR, EMB_DIR, load_tasks, save_json


def graph_file(repo: str, commit: str) -> str | None:
    short = repo.rsplit("/", 1)[-1]
    slug = repo.replace("/", "_")
    for cand in (f"{short}_{commit}.json", f"{slug}_{commit}.json"):
        p = os.path.join(GRAPH_DIR, cand)
        if os.path.exists(p):
            return p
    return None


def emb_file(repo: str, commit: str) -> str | None:
    short = repo.rsplit("/", 1)[-1]
    slug = repo.replace("/", "_")
    for cand in (f"{short}_{commit}.npz", f"{slug}_{commit}.npz"):
        p = os.path.join(EMB_DIR, cand)
        if os.path.exists(p):
            return p
    return None


def main():
    tasks = load_tasks()
    pairs = sorted({(t["repo"], t["base_commit"]) for t in tasks})
    edge_type_census: collections.Counter = collections.Counter()
    rows = []
    dims = set()
    for repo, commit in pairs:
        gp, ep = graph_file(repo, commit), emb_file(repo, commit)
        rec = {"repo": repo, "commit": commit,
               "graph_found": gp is not None, "emb_found": ep is not None}
        if gp:
            g = json.load(open(gp, encoding="utf-8"))
            nodes, edges = g["nodes"], g["edges"]
            ids = [str(n.get("id")) for n in nodes]
            deg = collections.Counter()
            for e in edges:
                deg[str(e["source"])] += 1
                deg[str(e["target"])] += 1
                edge_type_census[str(e.get("type", e.get("relation", "?")))] += 1
            texts = [str(n.get("text") or "") for n in nodes]
            degenerate = sum(
                1 for tx in texts
                if not tx.strip() or tx.rstrip().endswith("None")
            )
            rec.update({
                "n_nodes": len(nodes),
                "n_edges": len(edges),
                "isolated_frac": round(
                    sum(1 for i in ids if deg[i] == 0) / max(len(ids), 1), 4),
                "degenerate_text_frac": round(degenerate / max(len(nodes), 1), 4),
            })
            if ep:
                z = np.load(ep)
                keys = set(z.files)
                dims |= {z[k].shape[-1] for k in z.files[:3]}
                idset = set(ids)
                rec.update({
                    "n_emb_keys": len(keys),
                    "nodes_with_emb_exact": sum(1 for i in idset if i in keys),
                    "emb_keys_not_in_graph": len(keys - idset),
                })
        rows.append(rec)

    with_g = [r for r in rows if r.get("graph_found")]
    summary = {
        "n_graph_commit_pairs": len(pairs),
        "graphs_found": len(with_g),
        "embeddings_found": sum(1 for r in rows if r.get("emb_found")),
        "edge_type_census_all_graphs": dict(edge_type_census),
        "embedding_dims_observed": sorted(dims),
        "total_nodes": sum(r.get("n_nodes", 0) for r in rows),
        "total_edges": sum(r.get("n_edges", 0) for r in rows),
        "mean_isolated_frac": round(
            sum(r["isolated_frac"] for r in with_g) / max(len(with_g), 1), 4),
        "mean_degenerate_text_frac": round(
            sum(r["degenerate_text_frac"] for r in with_g) / max(len(with_g), 1), 4),
        "mean_node_emb_exact_cover": round(
            sum(r["nodes_with_emb_exact"] / r["n_nodes"]
                for r in with_g if r.get("n_emb_keys")) / max(len(with_g), 1), 4),
    }
    path = save_json("s02_graphs.json", {"summary": summary, "graphs": rows})
    print("wrote", path)
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
