#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import json, hashlib, sys
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
schema = json.loads((ROOT / "ground_truth.schema.json").read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
case_files = sorted(ROOT.glob("*_ground_truth.json"))

errors = []

if len(case_files) != manifest["benchmark_fixture_count"]:
    errors.append(f"manifest fixture count {manifest['benchmark_fixture_count']} != files {len(case_files)}")

family_ids = set()
for p in case_files:
    d = json.loads(p.read_text(encoding="utf-8"))
    schema_errors = list(validator.iter_errors(d))
    if schema_errors:
        errors.append(f"{p.name}: JSON Schema errors: {[e.message for e in schema_errors[:3]]}")

    ids = [f["field_id"] for f in d["facts"]]
    duplicates = [x for x,c in Counter(ids).items() if c > 1]
    if duplicates:
        errors.append(f"{p.name}: duplicate field_ids: {duplicates}")

    if not d["fixture_metadata"]["frozen"] or d["fixture_metadata"]["status"] != "frozen":
        errors.append(f"{p.name}: fixture is not frozen")

    for f in d["facts"]:
        if f.get("scorable"):
            if f.get("status") != "known":
                errors.append(f"{p.name}:{f['field_id']}: scorable but status={f.get('status')}")
            if f.get("verification_status") != "verified":
                errors.append(f"{p.name}:{f['field_id']}: scorable but verification={f.get('verification_status')}")
            if not any(s.get("supports_value") for s in f.get("sources", [])):
                errors.append(f"{p.name}:{f['field_id']}: scorable fact has no supporting source")

for r in manifest["fixtures"]:
    family_ids.add(r["vehicle_family_id"])

if len(family_ids) != manifest["vehicle_family_count"]:
    errors.append(f"vehicle family count {len(family_ids)} != manifest {manifest['vehicle_family_count']}")

required_evidence = [
    ROOT / "evidence/02_mini/true_positive_steering_wheel.jpg",
    ROOT / "evidence/02_mini/false_positive_steering_wheel.jpg",
    ROOT / "evidence/02_mini/true_positive_cargurus_snapshot.json",
    ROOT / "evidence/02_mini/false_positive_cargurus_snapshot.json",
    ROOT / "evidence/10_tesla/hw4_listing_snapshot.json",
    ROOT / "SCORING_POLICY.md",
]
for p in required_evidence:
    if not p.exists() or p.stat().st_size == 0:
        errors.append(f"missing required evidence/artifact: {p.relative_to(ROOT)}")

if errors:
    print("AUDIT FAILED")
    for e in errors:
        print("-", e)
    sys.exit(1)

print("AUDIT PASSED")
print(f"fixtures={len(case_files)}")
print(f"vehicle_families={len(family_ids)}")
print("schema_errors=0")
print("scorable_unverified=0")
print("scorable_without_supporting_source=0")
print("required_evidence_missing=0")
