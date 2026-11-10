# Code-graph toolkit audit (Gemma 4 Developer Agent)

Scripts and outputs for the writeup *Silent failures in the Gemma 4 Developer Agent code-graph toolkit* (Kaggle, Gemma 4 Developer Agent paper track).

The audit checks the three code-graph tools of the competition's `swegemma` toolkit on all 129 public tasks. It runs offline and statically, with no model inference. It runs against two versions of the toolkit:
- **0.2.7**, the version audited in the first version of the writeup;
- **0.2.11**, published in the competition wheelhouse on 12 October 2026.

| Path | Contents |
|---|---|
| `analysis/common.py` | Data loading, gold-symbol extraction and query builders. Imports the official graph modules unmodified. |
| `analysis/s01`–`s04` | Task statistics, graph census, gold edit symbols, and the query-shape and `edge_type` audit. |
| `analysis/s05_render.py` | Renders every table from the JSON outputs. |
| `analysis/s06_lexical_tests_0211.py` | Counts the test functions among 0.2.11's free-text results, called through the tool wrapper. |
| `analysis/probe_tool_0211.py` | End-to-end probe of the 0.2.11 tool wrapper. |
| `results_0.2.7/`, `results_0.2.11/` | JSON outputs, rendered tables (`tables.md`) and figures for each version. |
| `plot_cover_v2.py`, `cover_fig_v2.png` | The cover figure, which compares the two versions. |

## Running

Requirements:
- the competition's public data release, with `tasks.jsonl`, `graphs/`, `embeddings/` and `snapshots/`;
- the competition wheelhouse;
- Python 3.12 with numpy, networkx, unidiff and matplotlib.

The `s06` and `probe` scripts import the full toolkit, so they also need the wheelhouse's `adk_eval_core`.

```bash
export AUDIT_DATA_DIR=/path/to/competition/data AUDIT_WHEELHOUSE=/path/to/wheelhouse
for v in 0.2.7 0.2.11; do
  export AUDIT_SWEGEMMA_VERSION=$v AUDIT_VENDOR_DIR=$PWD/vendor_$v AUDIT_RESULTS_DIR=$PWD/rerun_$v
  (cd analysis && for s in s01_dataset_stats s02_graph_stats s03_gold_symbols s04_audit s05_render; do python $s.py; done)
done
```

Each rerun reproduces the JSON files and `tables.md` in `results_<version>/` exactly.

## License

Apache 2.0, see `LICENSE`. The competition data and the `swegemma` wheel are not redistributed here.
