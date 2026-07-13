"""Create a locked 300-question manifest for three-model blind comparison."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["qwen25_7b_base", "v2_80_lora", "v3_5000_lora"]
rows = [json.loads(line) for line in (ROOT / "eval/mech_eval_v3_master_300.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
manifest = []
for row in rows:
    for model in MODELS:
        manifest.append({
            "question_id": row["id"], "model_key": model,
            "instruction": row["instruction"], "input": row["input"],
            "response": None,
            "scores": {"engineering_fact": None, "risk_coverage": None, "actionability": None, "evidence_boundary": None, "no_fabrication": None, "clarity": None},
            "high_risk_fact_error": None, "unsupported_fixed_number": None,
            "reviewer": None, "reviewed_at": None,
        })
out = ROOT / "reports/model_comparison_manifest_900.jsonl"
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in manifest), encoding="utf-8")
print(f"questions={len(rows)} models={len(MODELS)} records={len(manifest)} path={out}")
