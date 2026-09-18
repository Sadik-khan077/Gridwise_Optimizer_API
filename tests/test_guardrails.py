import pytest
from app.interpreter.guardrails import validate_and_parse_llm_output

def test_valid_llm_output():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [1, 2], "factor": 0.5},
            "explanation": "test"
        }
    ]
    notes = ["note 1"]
    valid, err, parsed = validate_and_parse_llm_output(raw, notes, 100.0)
    assert valid

def test_invalid_type():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "invalid_type",
            "structured_adjustment": {"hours": [1, 2]},
            "explanation": "test"
        }
    ]
    notes = ["note 1"]
    valid, err, parsed = validate_and_parse_llm_output(raw, notes, 100.0)
    assert not valid
    assert "invalid directive_type" in err

def test_unsorted_hours():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [2, 1]},
            "explanation": "test"
        }
    ]
    notes = ["note 1"]
    valid, err, parsed = validate_and_parse_llm_output(raw, notes, 100.0)
    assert valid
    assert parsed[0]["structured_adjustment"]["hours"] == [1, 2]

def test_invalid_hour():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [25]},
            "explanation": "test"
        }
    ]
    notes = ["note 1"]
    valid, err, parsed = validate_and_parse_llm_output(raw, notes, 100.0)
    assert not valid
    assert "invalid hour" in err

def test_invalid_factor():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [1], "factor": 1.5},
            "explanation": "test"
        }
    ]
    notes = ["note 1"]
    valid, err, parsed = validate_and_parse_llm_output(raw, notes, 100.0)
    assert not valid

def test_duplicate_note_index():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [1]},
            "explanation": "test"
        },
        {
            "note_index": 0, # duplicate
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [2]},
            "explanation": "test"
        }
    ]
    notes = ["note 1", "note 2"]
    valid, err, parsed = validate_and_parse_llm_output(raw, notes, 100.0)
    assert not valid
    assert "duplicate note_index" in err
