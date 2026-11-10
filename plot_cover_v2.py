"""Cover figure for the revised writeup: gold-site localization by query shape, swegemma 0.2.7 vs 0.2.11."""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
SRC = {v: HERE / f"results_{v}" / "s04_audit.json" for v in ("0.2.7", "0.2.11")}
SHAPES = [("nl_full", "Full problem statement"), ("nl_line", "First line of statement"), ("snippet", "Gold-patch code snippet"),
          ("keywords", "Top-5 content keywords"), ("shim", "Extracted identifiers (rewriting)")]
EXPECT = {"0.2.7": [0, 0, 0, 30, 36], "0.2.11": [37, 41, 43, 39, 54]}   # Table 4 of the writeup


def hits(path):
    tasks = json.load(open(path, encoding="utf-8"))["tasks"]
    loc = [t for t in tasks if str(t["gold_in_graph"]) == "True"]
    assert len(loc) == 115
    out = []
    for key, _ in SHAPES:
        out.append(sum(bool(t["cond"][key]["resolve_hits_gold"] or t["cond"][key]["topk_hits_gold"]) for t in loc))
    return out


H = {v: hits(p) for v, p in SRC.items()}
assert H == EXPECT, H
fig, ax = plt.subplots(figsize=(7.0, 3.5), layout="constrained")
y = range(len(SHAPES))
for off, (v, color) in zip((-0.2, 0.2), (("0.2.7", "#b0b0b0"), ("0.2.11", "#2f6f9f"))):
    vals = [h / 115 * 100 for h in H[v]]
    ax.barh([i + off for i in y], vals, height=0.38, color=color, label=f"swegemma {v}")
    for i, (val, h) in enumerate(zip(vals, H[v])):
        ax.text(val + 0.8, i + off, str(h), va="center", fontsize=8.5)
ax.set_yticks(list(y), [s for _, s in SHAPES])
ax.invert_yaxis()
ax.set_xlim(0, 60)
ax.set_xlabel("% of 115 localizable tasks where results reach a gold edit site")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
ax.set_title("Code-graph search by query shape: silent empty (0.2.7) → lexical substitution (0.2.11)", fontsize=9.5, loc="left")
fig.savefig(HERE / "cover_fig_v2.png", dpi=160)
print("wrote", HERE / "cover_fig_v2.png", H)
