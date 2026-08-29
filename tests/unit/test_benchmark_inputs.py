import json
from pathlib import Path

import pytest

from enthusiast_lens.evaluation.benchmark_inputs import (
    BenchmarkInputValidationError,
    load_and_validate_benchmark_inputs,
)
from enthusiast_lens.models.benchmark_input import BenchmarkInputCorpus


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = REPO_ROOT / "evals" / "inputs" / "benchmark_inputs.json"
MANIFEST_PATH = REPO_ROOT / "evals" / "ground_truth" / "manifest.json"


def test_frozen_corpus_maps_all_manifest_fixtures() -> None:
    corpus = load_and_validate_benchmark_inputs(CORPUS_PATH, MANIFEST_PATH)

    assert len(corpus.inputs) == 12
    assert len({item.vehicle_family_id for item in corpus.inputs}) == 11
    assert sum(item.runtime_ready for item in corpus.inputs) == 11


def test_duplicate_fixture_id_is_rejected() -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["inputs"][1]["fixture_id"] = payload["inputs"][0]["fixture_id"]

    with pytest.raises(ValueError, match="fixture IDs must be unique"):
        BenchmarkInputCorpus.model_validate(payload)


def test_duplicate_vin_is_rejected() -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["inputs"][1]["vehicle"]["vin"] = payload["inputs"][0]["vehicle"]["vin"]

    with pytest.raises(ValueError, match="VINs must be unique"):
        BenchmarkInputCorpus.model_validate(payload)


@pytest.mark.parametrize("vin", ["SHORT", "JM1NDAD7IT0702556", "JM1NDAD7OT0702556"])
def test_implausible_vin_is_rejected(vin: str) -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["inputs"][0]["vehicle"]["vin"] = vin

    with pytest.raises(ValueError):
        BenchmarkInputCorpus.model_validate(payload)


@pytest.mark.parametrize("field", ["expected_value", "facts", "tolerance", "answer_key"])
def test_answer_key_fields_are_rejected(tmp_path: Path, field: str) -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["inputs"][0][field] = "leak"
    altered = tmp_path / "benchmark_inputs.json"
    altered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BenchmarkInputValidationError, match="answer-key field"):
        load_and_validate_benchmark_inputs(altered, MANIFEST_PATH)


def test_missing_fixture_mapping_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["inputs"].pop()
    altered = tmp_path / "benchmark_inputs.json"
    altered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BenchmarkInputValidationError, match="fixture mapping mismatch"):
        load_and_validate_benchmark_inputs(altered, MANIFEST_PATH)


def test_required_configuration_identity_is_enforced() -> None:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    payload["inputs"][0]["vehicle"]["transmission"] = None

    with pytest.raises(ValueError, match="vehicle transmission is required"):
        BenchmarkInputCorpus.model_validate(payload)
