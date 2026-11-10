"""s05: Renders script-generated fact tables (material input for the paper),
derived union metrics, and diagnostic figures.  Every table cell and every
universal claim below is computed from the s01-s04 result files; nothing is
hand-written."""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import RESULTS_DIR

FIG_DIR = os.path.join(RESULTS_DIR, "figs")


def load(name):
    with open(os.path.join(RESULTS_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def pct(x, y):
    return f"{100.0 * x / y:.1f}%" if y else "n/a"


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    s01, s02, s03, s04 = (load(n) for n in
                          ("s01_dataset.json", "s02_graphs.json",
                           "s03_gold.json", "s04_audit.json"))
    ok = [r for r in s04["tasks"] if "error" not in r]
    loc = [r for r in ok if r["gold_in_graph"]]
    n_loc = len(loc)
    n_all = len(ok)

    conds = ["nl_full", "nl_line", "snippet", "keywords", "shim", "oracle"]
    labels = {
        "nl_full": "Full problem statement (NL)",
        "nl_line": "First line of statement (NL)",
        "snippet": "Gold-patch code snippet",
        "keywords": "Top-5 content keywords",
        "shim": "Extracted identifiers (shim)",
        "oracle": "Gold bare names (oracle)",
    }
    cond_rows = []
    for c in conds:
        nonempty = sum(1 for r in ok if r["cond"][c]["n_nonempty"] > 0)
        res_hit = sum(1 for r in loc if r["cond"][c]["resolve_hits_gold"])
        topk_hit = sum(1 for r in loc if r["cond"][c]["topk_hits_gold"])
        union = sum(1 for r in loc if r["cond"][c]["resolve_hits_gold"]
                    or r["cond"][c]["topk_hits_gold"])
        cond_rows.append((c, nonempty, res_hit, topk_hit, union))

    shim_any = sum(1 for r in loc if r["cond"]["shim"]["resolve_hits_gold"]
                   or r["cond"]["shim"]["topk_hits_gold"]
                   or r["neighbors_hit_gold"])
    nb_hit = sum(1 for r in loc if r["neighbors_hit_gold"])
    ef = s04["summary"]["edge_filter_neighbor_totals"]
    efn = s04["summary"]["edge_filter_nodes_probed"]
    ec = s02["summary"]["edge_type_census_all_graphs"]

    lines = []
    w = lines.append
    w("# Script-generated fact tables (do not edit by hand)")
    w("")
    w("Source: s01_dataset.json / s02_graphs.json / s03_gold.json / s04_audit.json,")
    w("produced by analysis/s01..s04 on the official competition data release.")
    w("")

    w("## Table A — Public task set")
    w("")
    w("| Quantity | Value |")
    w("|---|---|")
    su1 = s01["summary"]
    w(f"| Tasks | {su1['n_tasks']} |")
    for repo, cnt in sorted(su1["per_repo"].items(), key=lambda kv: -kv[1]):
        w(f"| — {repo} | {cnt} |")
    w(f"| Median files changed by gold patch | {su1['median_files']} |")
    w(f"| Median lines added / removed | {su1['median_added']} / {su1['median_removed']} |")
    w(f"| Tasks whose patch creates >=1 new file | {su1['tasks_with_new_file']} |")
    w(f"| Tasks whose patch only adds new files | {su1['adds_only_tasks']} |")
    w(f"| Median problem-statement length (words) | {su1['median_stmt_words']} |")
    w(f"| Statements containing >=1 extractable identifier | {su1['tasks_with_ge1_identifier']} ({pct(su1['tasks_with_ge1_identifier'], su1['n_tasks'])}) |")
    w(f"| Statements containing backticked code | {su1['tasks_with_backtick']} ({pct(su1['tasks_with_backtick'], su1['n_tasks'])}) |")
    w(f"| Tasks with non-empty hints_text | {su1['tasks_with_hints']} |")
    w("")

    w("## Table B — Shipped graphs and embeddings (census of all graphs)")
    w("")
    su2 = s02["summary"]
    w("| Quantity | Value |")
    w("|---|---|")
    w(f"| (repo, base_commit) pairs / graphs found / embedding archives found | {su2['n_graph_commit_pairs']} / {su2['graphs_found']} / {su2['embeddings_found']} |")
    w(f"| Total nodes / total edges | {su2['total_nodes']} / {su2['total_edges']} |")
    w(f"| Edge types present (census over every edge) | {ec} |")
    w(f"| Mean isolated-node fraction per graph | {su2['mean_isolated_frac']*100:.1f}% |")
    w(f"| Mean fraction of nodes with missing/placeholder body text | {su2['mean_degenerate_text_frac']*100:.1f}% |")
    w(f"| Nodes with an exact-key embedding (mean per graph) | {su2['mean_node_emb_exact_cover']*100:.1f}% |")
    w(f"| Embedding dimensions observed | {su2['embedding_dims_observed']} |")
    w("")

    w("## Table C — Gold edit symbols and graph coverage")
    w("")
    su3 = s03["summary"]
    su4 = s04["summary"]
    w("| Quantity | Value |")
    w("|---|---|")
    w(f"| Tasks with >=1 gold function/class symbol | {su3['tasks_with_ge1_gold_sym']} / {su3['n_tasks']} |")
    w(f"| Tasks whose gold edits are module-level only | {su3['tasks_module_level_only']} |")
    w(f"| Total gold symbols across tasks | {su3['total_gold_syms']} |")
    w(f"| Tasks with >=1 gold symbol present in graph (qualified match) | {su4['n_tasks_gold_in_graph_qual']} / {su3['n_tasks']} ({pct(su4['n_tasks_gold_in_graph_qual'], su3['n_tasks'])}) |")
    w("")

    w(f"## Table D — Tool behavior by query shape (129 tasks; localization over the {n_loc} tasks with gold symbols in graph)")
    w("")
    w("| Query shape | Tasks with any non-empty result (/129) | Resolve hits gold (/{n}) | Top-10 hits gold (/{n}) | Either (/{n}) |".replace("{n}", str(n_loc)))
    w("|---|---|---|---|---|")
    for c, nonempty, res_hit, topk_hit, union in cond_rows:
        w(f"| {labels[c]} | {nonempty} ({pct(nonempty, n_all)}) | {res_hit} ({pct(res_hit, n_loc)}) | {topk_hit} ({pct(topk_hit, n_loc)}) | {union} ({pct(union, n_loc)}) |")
    w("")
    w(f"Neighbor lookups on extracted identifiers reach a gold symbol in {nb_hit} / {n_loc} tasks ({pct(nb_hit, n_loc)}).")
    w(f"Union of all shim channels (resolution, top-10 similarity, neighbors): {shim_any} / {n_loc} tasks ({pct(shim_any, n_loc)}).")
    w("")

    w("## Table E — edge_type filter audit (get_code_neighbors)")
    w("")
    w(f"Probed {efn} connected nodes (up to 5 per graph). Total neighbors returned:")
    w("")
    w("| Filter | Neighbors returned |")
    w("|---|---|")
    w(f"| no filter | {ef['none']} |")
    w(f"| edge_type='calls' (actual data value) | {ef['calls']} |")
    w(f"| edge_type='CALLS' (docstring example) | {ef['CALLS']} |")
    w(f"| edge_type='DEFINED_IN' (docstring example) | {ef['DEFINED_IN']} |")
    w(f"| edge_type='IMPORTS' (docstring example) | {ef['IMPORTS']} |")
    w("")

    w("## Computed universal claims (each generated from the result files)")
    w("")
    nl0 = [r for r in cond_rows if r[0] in ("nl_full", "nl_line", "snippet")]
    if all(r[1] == 0 for r in nl0):
        w(f"- CLAIM-1: In all {n_all} tasks, querying search_similar_code with the full problem statement, its first line, or a gold-patch code snippet returned zero results; every call returned a well-formed success response with an empty result list.")
    total_edges = sum(ec.values())
    if list(ec.keys()) == ["calls"] and ef["CALLS"] == 0 and ef["DEFINED_IN"] == 0 and ef["IMPORTS"] == 0:
        w(f"- CLAIM-2: Every one of the {total_edges} edges across all {su2['graphs_found']} shipped graphs has type 'calls'; the docstring-advertised filters 'CALLS', 'DEFINED_IN' and 'IMPORTS' match zero edges (exact string comparison in the shipped code).")
    orc = next(r for r in cond_rows if r[0] == "oracle")
    if orc[2] == n_loc:
        w(f"- CLAIM-3: Given the bare name of a gold symbol, resolution succeeded in {n_loc} of {n_loc} localizable tasks — when the query is an existing symbol name, the lookup machinery works.")
    kw = next(r for r in cond_rows if r[0] == "keywords")
    w(f"- CLAIM-4: Plain-keyword queries returned plausible-looking non-empty results in {kw[1]} of {n_all} tasks, yet their results reach a gold symbol in only {kw[4]} of {n_loc} localizable tasks ({pct(kw[4], n_loc)}).")
    sh = next(r for r in cond_rows if r[0] == "shim")
    w(f"- CLAIM-5: Identifier extraction alone (no model, no new embeddings) recovers direct resolution to a gold symbol in {sh[2]} of {n_loc} localizable tasks ({pct(sh[2], n_loc)}), and {shim_any} of {n_loc} ({pct(shim_any, n_loc)}) via any shim channel.")

    out_path = os.path.join(RESULTS_DIR, "tables.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out_path)

    # ---- diagnostic figures ----
    fig, ax = plt.subplots(figsize=(7.5, 4))
    names = [labels[c] for c, *_ in cond_rows]
    unions = [u for *_, u in cond_rows]
    ax.barh(names[::-1], [100 * u / n_loc for u in unions][::-1], color="#4878a8")
    ax.set_xlabel(f"% of {n_loc} localizable tasks where results reach a gold symbol")
    ax.set_title("Localization by query shape (resolve or top-10)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig1_localization_by_query_shape.png"), dpi=150)

    fig, ax = plt.subplots(figsize=(6, 4))
    fr = [g["isolated_frac"] * 100 for g in s02["graphs"] if "isolated_frac" in g]
    ax.hist(fr, bins=20, color="#4878a8", edgecolor="white")
    ax.set_xlabel("Isolated-node fraction per graph (%)")
    ax.set_ylabel("Graphs")
    ax.set_title("Connectivity of shipped call graphs")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig2_isolated_fraction.png"), dpi=150)

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = {"fastapi/fastapi": "#4878a8", "Textualize/rich": "#a85448",
              "psf/requests": "#6a9a58", "encode/httpx": "#8868a8"}
    for g in s02["graphs"]:
        if "n_nodes" in g:
            ax.scatter(g["n_nodes"], g["n_edges"], s=14, alpha=0.7,
                       color=colors.get(g["repo"], "gray"))
    for repo, c in colors.items():
        ax.scatter([], [], color=c, label=repo)
    ax.set_xlabel("Nodes"); ax.set_ylabel("Edges (calls)")
    ax.legend(fontsize=7)
    ax.set_title("Shipped graph sizes")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig3_graph_sizes.png"), dpi=150)
    print("wrote 3 figures to", FIG_DIR)


if __name__ == "__main__":
    main()
