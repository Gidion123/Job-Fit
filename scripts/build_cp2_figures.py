"""Create CP2 development figures from saved measurements only."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/jobfit_mplconfig")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/figures/cp2"
OUT.mkdir(parents=True, exist_ok=True)


def read(path):
    return json.loads((ROOT / path).read_text())


def save(fig, name, caption):
    fig.text(.04, .018, caption, fontsize=8, color="#425466", va="bottom")
    fig.savefig(OUT / name, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


retrieval = read("evals/results/cp23_stage3_retrieval_evaluation_20261003_v2.json")["aggregate"]
labels = [r["method"].replace("_", " ") for r in retrieval]
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(labels))
for offset, key, title, color in [(-.27, "p_at_5_macro", "P@5", "#2166ac"),
                                  (0, "ndcg_at_10_macro", "NDCG@10", "#238b45")]:
    ax.bar(x + offset, [r[key] for r in retrieval], width=.25, label=title, color=color)
ax.bar(x + .27, [r["recall_labeled_pool"]["20"] for r in retrieval], width=.25,
       label="Recall@20", color="#d95f0e")
ax.set_xticks(x, labels, rotation=20, ha="right")
ax.set_ylim(0, .8); ax.set_ylabel("Metric value"); ax.set_title("Development retrieval comparison")
ax.legend(ncol=3, loc="upper center")
fig.tight_layout(rect=(0, .05, 1, 1))
save(fig, "fig01_retrieval_methods.png",
     "Development: CV1/CV2, 214 eligible JDs; original ranks, reviewed relevance pool; no optional filter.")

pair = {r["method"]: r for r in retrieval}
fig, ax = plt.subplots(figsize=(8, 4.6))
labs = ["Dense OpenAI", "Dense Qwen", "Hybrid OpenAI", "Hybrid Qwen"]
keys = ["dense_openai", "dense_qwen", "hybrid_openai", "hybrid_qwen"]
bars = ax.bar(labs, [pair[k]["recall_labeled_pool"]["20"] for k in keys],
              color=["#9ecae1", "#2171b5", "#a1d99b", "#238b45"])
ax.bar_label(bars, fmt="%.3f", padding=3)
ax.set_ylim(0, .7); ax.set_ylabel("Labeled-pool Recall@20")
ax.set_title("Embedding comparison under the same retrieval method")
fig.tight_layout(rect=(0, .06, 1, 1))
save(fig, "fig02_embedding_recall20.png",
     "Development: CV1/CV2, 214 JDs; OpenAI 1536 dimensions, Qwen 4096; D-044 selects Qwen.")

sql = read("evals/results/cp23_sql_reference_comparison_20261004_v2.json")["results"]
gem = read("evals/results/cp23_gemini_f00815_alignment_20261004_v1.json")
names = ["DeepSeek Flash", "GPT-6 Luna", "Gemini Lite", "Claude Haiku", "GPT-6 Sol"]
keys = ["deepseek-flash", "gpt-6-luna", "gemini-3.5-flash-lite", "claude-haiku-4.5", "gpt-6-sol"]
scopes = ["round_one_B"] * 4 + ["reference_round_two"]
extraction = [.861789, .793651, gem["seven_jd_new"]["f1"], .541667, np.nan]
matching = [sql[s][k]["new"]["all_cases_guarded"]["macro_f1"] for s, k in zip(scopes, keys)]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
y = np.arange(len(names))
ax1.barh(y, extraction, color="#2171b5")
ax2.barh(y, matching, color="#238b45")
for ax, title in [(ax1, "JD extraction F1"), (ax2, "Evidence Macro-F1")]:
    ax.set_yticks(y, names); ax.invert_yaxis(); ax.set_xlim(0, 1)
    ax.set_title(title); ax.grid(axis="x", alpha=.2)
ax1.text(.03, 4, "not accepted on common\nextraction scope", fontsize=7, va="center")
fig.tight_layout(rect=(0, .07, 1, 1))
save(fig, "fig03_llm_quality.png",
     "Development: extraction 7 JDs/120 units; GPT Sol extraction N/A. Matching 4 pairs/73 units, B, v1.1, D-067, G1/G2.")

conf = sql["round_one_B"]["deepseek-flash"]["new"]["all_cases_guarded"]["confusion"]
classes = ["MATCH", "PARTIAL", "NO_MATCH", "not_assessed"]
gold_classes = classes[:3]
matrix = np.array([[conf[g][p] for p in classes] for g in gold_classes])
fig, ax = plt.subplots(figsize=(7, 4.7))
im = ax.imshow(matrix, cmap="Blues", vmin=0)
for i in range(3):
    for j in range(4): ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black")
ax.set_xticks(range(4), classes, rotation=20); ax.set_yticks(range(3), gold_classes)
ax.set_xlabel("Predicted"); ax.set_ylabel("Reviewed reference")
ax.set_title("DeepSeek Flash evidence confusion matrix")
fig.colorbar(im, ax=ax, shrink=.8)
fig.tight_layout(rect=(0, .06, 1, 1))
save(fig, "fig04_matching_confusion.png",
     "Development: 4 CV/JD pairs, 73 units; validator v1.1, D-067 SQL reference, G1/G2; failures are not_assessed.")

fig, ax = plt.subplots(figsize=(8.5, 4.7))
subkeys = keys[:4]
before = [sql["round_one_B"][k]["new"]["all_cases"]["macro_f1"] for k in subkeys]
after = [sql["round_one_B"][k]["new"]["all_cases_guarded"]["macro_f1"] for k in subkeys]
x = np.arange(4)
ax.bar(x - .18, before, width=.36, label="Before G1/G2", color="#9ecae1")
ax.bar(x + .18, after, width=.36, label="After G1/G2", color="#2171b5")
ax.set_xticks(x, names[:4], rotation=15, ha="right"); ax.set_ylim(0, .85)
ax.set_ylabel("Evidence Macro-F1"); ax.set_title("Guardrail effect on saved model outputs")
ax.legend(); fig.tight_layout(rect=(0, .06, 1, 1))
save(fig, "fig05_guardrail_effect.png",
     "Development: same 73 reference units/model, B, v1.1, D-067; Gemini/Claude have incomplete valid-pair coverage.")

cost = read("evals/results/cp23_k20_cost_projection_20261004_v1.json")["models"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.8))
cost_names = ["DeepSeek Flash", "GPT-6 Luna", "GPT-6 Sol"]
model_keys = ["deepseek-flash", "gpt-6-luna", "gpt-6-sol"]
positions = np.arange(3)
for offset, depth, color in [(-.23, 10, "#a1d99b"), (0, 20, "#238b45"), (.23, 30, "#005a32")]:
    ax1.bar(positions + offset,
            [cost[k]["k20_cached_jd_matching_only_usd"] * depth / 20 for k in model_keys],
            width=.22, label=f"K={depth}", color=color)
ax1.set_xticks(positions, cost_names)
ax1.set_ylabel("Projected USD / CV"); ax1.set_title("Matching cost with JD cache")
ax1.legend(fontsize=8)
ax2.bar(cost_names, [90.747, 21.880, 16.134], color=["#238b45", "#6baed6", "#d95f0e"])
ax2.set_ylabel("Observed request p95, seconds"); ax2.set_title("Matching request latency")
for ax in (ax1, ax2): ax.tick_params(axis="x", rotation=15)
fig.tight_layout(rect=(0, .07, 1, 1))
save(fig, "fig06_cost_latency.png",
     "Development: K10/20/30 linear matching-cost projection from 4 pairs/model; p95 requests only, not end-to-end timing.")

print("Created", len(list(OUT.glob("fig0*.png"))), "CP2 figures in", OUT)
