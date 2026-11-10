# Script-generated fact tables (do not edit by hand)

Source: s01_dataset.json / s02_graphs.json / s03_gold.json / s04_audit.json,
produced by analysis/s01..s04 on the official competition data release.

## Table A — Public task set

| Quantity | Value |
|---|---|
| Tasks | 129 |
| — fastapi/fastapi | 67 |
| — Textualize/rich | 48 |
| — psf/requests | 13 |
| — encode/httpx | 1 |
| Median files changed by gold patch | 1 |
| Median lines added / removed | 8 / 2 |
| Tasks whose patch creates >=1 new file | 11 |
| Tasks whose patch only adds new files | 1 |
| Median problem-statement length (words) | 58 |
| Statements containing >=1 extractable identifier | 120 (93.0%) |
| Statements containing backticked code | 76 (58.9%) |
| Tasks with non-empty hints_text | 0 |

## Table B — Shipped graphs and embeddings (census of all graphs)

| Quantity | Value |
|---|---|
| (repo, base_commit) pairs / graphs found / embedding archives found | 127 / 127 / 127 |
| Total nodes / total edges | 367985 / 452588 |
| Edge types present (census over every edge) | {'calls': 452588} |
| Mean isolated-node fraction per graph | 38.3% |
| Mean fraction of nodes with missing/placeholder body text | 11.3% |
| Nodes with an exact-key embedding (mean per graph) | 100.0% |
| Embedding dimensions observed | [256] |

## Table C — Gold edit symbols and graph coverage

| Quantity | Value |
|---|---|
| Tasks with >=1 gold function/class symbol | 121 / 129 |
| Tasks whose gold edits are module-level only | 7 |
| Total gold symbols across tasks | 522 |
| Tasks with >=1 gold symbol present in graph (qualified match) | 115 / 129 (89.1%) |

## Table D — Tool behavior by query shape (129 tasks; localization over the 115 tasks with gold symbols in graph)

| Query shape | Tasks with any non-empty result (/129) | Resolve hits gold (/115) | Top-10 hits gold (/115) | Either (/115) |
|---|---|---|---|---|
| Full problem statement (NL) | 129 (100.0%) | 0 (0.0%) | 37 (32.2%) | 37 (32.2%) |
| First line of statement (NL) | 127 (98.4%) | 0 (0.0%) | 41 (35.7%) | 41 (35.7%) |
| Gold-patch code snippet | 124 (96.1%) | 0 (0.0%) | 43 (37.4%) | 43 (37.4%) |
| Top-5 content keywords | 129 (100.0%) | 7 (6.1%) | 36 (31.3%) | 39 (33.9%) |
| Extracted identifiers (shim) | 118 (91.5%) | 31 (27.0%) | 41 (35.7%) | 54 (47.0%) |
| Gold bare names (oracle) | 115 (89.1%) | 115 (100.0%) | 48 (41.7%) | 115 (100.0%) |

Neighbor lookups on extracted identifiers reach a gold symbol in 15 / 115 tasks (13.0%).
Union of all shim channels (resolution, top-10 similarity, neighbors): 54 / 115 tasks (47.0%).

## Table E — edge_type filter audit (get_code_neighbors)

Probed 645 connected nodes (up to 5 per graph). Total neighbors returned:

| Filter | Neighbors returned |
|---|---|
| no filter | 1866 |
| edge_type='calls' (actual data value) | 1866 |
| edge_type='CALLS' (docstring example) | 1866 |
| edge_type='DEFINED_IN' (docstring example) | 0 |
| edge_type='IMPORTS' (docstring example) | 0 |

## Computed universal claims (each generated from the result files)

- CLAIM-3: Given the bare name of a gold symbol, resolution succeeded in 115 of 115 localizable tasks — when the query is an existing symbol name, the lookup machinery works.
- CLAIM-4: Plain-keyword queries returned plausible-looking non-empty results in 129 of 129 tasks, yet their results reach a gold symbol in only 39 of 115 localizable tasks (33.9%).
- CLAIM-5: Identifier extraction alone (no model, no new embeddings) recovers direct resolution to a gold symbol in 31 of 115 localizable tasks (27.0%), and 54 of 115 (47.0%) via any shim channel.
