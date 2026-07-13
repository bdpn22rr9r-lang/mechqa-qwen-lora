"""Deterministic Stage C data review with scalable near-duplicate checks."""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import schema as S

EXPECTED = S.V3_TARGETS
SEED = 20260713


def prompt(row: dict) -> str:
    return "\n".join((row["instruction"], row["input"], row["output"]))


def parent_id(row: dict) -> str:
    match = re.search(r"parent:([^;]+)", row.get("source_ref", ""))
    return match.group(1) if match else "missing"


def shingles(row: dict, width: int = 5) -> set[str]:
    text = re.sub(r"\s+", "", prompt(row))
    return {text[i:i + width] for i in range(max(1, len(text) - width + 1))}


def ratio(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a or b else 1.0


def review(train: list[dict], evaluation: list[dict], threshold: float, samples: int) -> dict:
    errors = []
    for pool, rows in (("train", train), ("eval", evaluation)):
        for row in rows:
            for err in S.dict_to_record(row).validate():
                errors.append(f"{pool}:{row.get('id')}: {err}")

    train_counts = Counter(r["category"] for r in train)
    if dict(train_counts) != EXPECTED:
        errors.append(f"category targets mismatch: {dict(train_counts)}")
    if len(train) != 5000 or len(evaluation) != 300:
        errors.append("record counts mismatch")

    all_rows = train + evaluation
    ids = [r["id"] for r in all_rows]
    prompt_keys = [(r["instruction"].strip(), r["input"].strip()) for r in all_rows]
    train_groups = {r["split_group"] for r in train}
    eval_groups = {r["split_group"] for r in evaluation}
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    if len(prompt_keys) != len(set(prompt_keys)):
        errors.append("duplicate prompts")
    if train_groups & eval_groups:
        errors.append("train/eval split_group leakage")
    if any(r.get("review_status") in {"approved", "expert_approved"} for r in all_rows):
        errors.append("unverified record marked expert approved")

    groups = defaultdict(list)
    for row in all_rows:
        groups[parent_id(row)].append(row)
    shingle_cache = {row["id"]: shingles(row) for row in all_rows}
    near = []
    comparisons_same_parent = 0
    for rows in groups.values():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                comparisons_same_parent += 1
                score = ratio(shingle_cache[rows[i]["id"]], shingle_cache[rows[j]["id"]])
                if score >= threshold:
                    near.append((rows[i]["id"], rows[j]["id"], round(score, 4)))

    rng = random.Random(SEED)
    comparisons_cross_parent = 0
    for _ in range(samples):
        a, b = rng.sample(all_rows, 2)
        if parent_id(a) == parent_id(b):
            continue
        comparisons_cross_parent += 1
        score = ratio(shingle_cache[a["id"]], shingle_cache[b["id"]])
        if score >= threshold:
            near.append((a["id"], b["id"], round(score, 4)))
    if near:
        errors.append(f"near duplicate pairs >= {threshold}: {len(near)}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "seed": SEED,
        "train_total": len(train),
        "eval_total": len(evaluation),
        "train_categories": dict(sorted(train_counts.items())),
        "schema_errors": sum("category targets" not in e and "record counts" not in e for e in errors),
        "train_eval_split_group_overlap": len(train_groups & eval_groups),
        "review_statuses": dict(Counter(r["review_status"] for r in all_rows)),
        "near_duplicate_threshold": threshold,
        "near_duplicate_metric": "character_5gram_jaccard",
        "same_parent_pairs_exhaustive": comparisons_same_parent,
        "cross_parent_pairs_sampled": comparisons_cross_parent,
        "near_duplicate_pairs": near[:100],
        "errors": errors[:100],
        "review_scope_note": "Same-parent variants are exhaustive; cross-parent checking is a deterministic sample, not an exhaustive all-pairs proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.9)
    parser.add_argument("--samples", type=int, default=100000)
    args = parser.parse_args()
    train = S.load_jsonl(ROOT / "data/master/mech_sft_v3_master_5000.jsonl")
    evaluation = S.load_jsonl(ROOT / "eval/mech_eval_v3_master_300.jsonl")
    report = review(train, evaluation, args.threshold, args.samples)
    out = ROOT / "reports/review_report_stage_c.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
