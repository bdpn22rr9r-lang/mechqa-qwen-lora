"""Validate completed blind ratings and calculate the task-book weighted score."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "reports/model_comparison_manifest_900.jsonl"
WEIGHTS = {"engineering_fact": 0.30, "risk_coverage": 0.20, "actionability": 0.15, "evidence_boundary": 0.15, "no_fabrication": 0.15, "clarity": 0.05}
rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
missing = []
totals = defaultdict(list)
high_risk_errors = defaultdict(int)
unsupported = defaultdict(int)
for row in rows:
    if not row.get("response") or any(row["scores"].get(k) is None for k in WEIGHTS) or not row.get("reviewer"):
        missing.append(f"{row['question_id']}:{row['model_key']}")
        continue
    score = sum(float(row["scores"][k]) * weight for k, weight in WEIGHTS.items())
    totals[row["model_key"]].append(score)
    high_risk_errors[row["model_key"]] += int(bool(row.get("high_risk_fact_error")))
    unsupported[row["model_key"]] += int(bool(row.get("unsupported_fixed_number")))
if missing:
    print(f"FAIL incomplete_records={len(missing)} examples={missing[:10]}")
    raise SystemExit(1)
summary = {model: {"mean_weighted_score": round(sum(values) / len(values), 4), "rated": len(values), "high_risk_fact_errors": high_risk_errors[model], "unsupported_fixed_numbers": unsupported[model]} for model, values in totals.items()}
(ROOT / "reports/model_comparison_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
