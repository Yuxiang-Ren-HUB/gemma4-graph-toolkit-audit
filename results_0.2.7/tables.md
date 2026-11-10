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
| Full problem statement (NL) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| First line of statement (NL) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Gold-patch code snippet | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Top-5 content keywords | 123 (95.3%) | 7 (6.1%) | 27 (23.5%) | 30 (26.1%) |
| Extracted identifiers (shim) | 73 (56.6%) | 31 (27.0%) | 20 (17.4%) | 36 (31.3%) |
| Gold bare names (oracle) | 115 (89.1%) | 115 (100.0%) | 45 (39.1%) | 115 (100.0%) |

Neighbor lookups on extracted identifiers reach a gold symbol in 15 / 115 tasks (13.0%).
Union of all shim channels (resolution, top-10 similarity, neighbors): 37 / 115 tasks (32.2%).

## Table E — edge_type filter audit (get_code_neighbors)

Probed 645 connected nodes (up to 5 per graph). Total neighbors returned:

| Filter | Neighbors returned |
|---|---|
| no filter | 1866 |
| edge_type='calls' (actual data value) | 1866 |
| edge_type='CALLS' (docstring example) | 0 |
| edge_type='DEFINED_IN' (docstring example) | 0 |
| edge_type='IMPORTS' (docstring example) | 0 |

## Computed universal claims (each generated from the result files)

- CLAIM-1: In all 129 tasks, querying search_similar_code with the full problem statement, its first line, or a gold-patch code snippet returned zero results; every call returned a well-formed success response with an empty result list.
- CLAIM-2: Every one of the 452588 edges across all 127 shipped graphs has type 'calls'; the docstring-advertised filters 'CALLS', 'DEFINED_IN' and 'IMPORTS' match zero edges (exact string comparison in the shipped code).
- CLAIM-3: Given the bare name of a gold symbol, resolution succeeded in 115 of 115 localizable tasks — when the query is an existing symbol name, the lookup machinery works.
- CLAIM-4: Plain-keyword queries returned plausible-looking non-empty results in 123 of 129 tasks, yet their results reach a gold symbol in only 30 of 115 localizable tasks (26.1%).
- CLAIM-5: Identifier extraction alone (no model, no new embeddings) recovers direct resolution to a gold symbol in 31 of 115 localizable tasks (27.0%), and 37 of 115 (32.2%) via any shim channel.
