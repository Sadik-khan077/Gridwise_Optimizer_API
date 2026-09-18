import json
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import OptimizeResponse
from app.validator.replay import run_replay_validator
from app.schemas import ScenarioRequest, HourlyPlanEntry

client = TestClient(app)

@pytest.fixture(scope="module")
def public_cases():
    data_path = os.path.join(os.path.dirname(__file__), "../data/public_cases.json")
    if not os.path.exists(data_path):
        pytest.skip(f"Could not find {data_path}")
    with open(data_path, 'r') as f:
        return json.load(f)

def test_public_cases(public_cases):
    # Only run if we have an API key or if fallback is good enough
    # If no API key, it will fall back anyway, but might not match exactly.
    for case in public_cases.get("cases", public_cases):
        req_data = case["input"]
        expected = case["expected_output"]
        
        response = client.post("/optimize-energy", json=req_data)
        assert response.status_code == 200, f"Failed on case {req_data['scenario_id']}"
        
        resp_data = response.json()
        
        # deep match directive interpretations
        exp_interp = expected["directive_interpretation"]
        act_interp = resp_data["directive_interpretation"]
        
        assert len(exp_interp) == len(act_interp)
        for i in range(len(exp_interp)):
            e = exp_interp[i]
            a = act_interp[i]
            assert a["note_index"] == e["note_index"]
            assert a["applies"] == e["applies"]
            assert a["directive_type"] == e["directive_type"]
            
            e_adj = e["structured_adjustment"]
            a_adj = a["structured_adjustment"]
            
            if e_adj is None:
                assert a_adj is None
            else:
                assert a_adj is not None
                assert sorted(a_adj["hours"]) == sorted(e_adj["hours"])
                if "factor" in e_adj:
                    assert abs(a_adj["factor"] - e_adj["factor"]) < 0.01
                if "minimum_energy_kwh" in e_adj:
                    assert abs(a_adj["minimum_energy_kwh"] - e_adj["minimum_energy_kwh"]) < 0.01
                if "max_grid_kwh" in e_adj:
                    assert abs(a_adj["max_grid_kwh"] - e_adj["max_grid_kwh"]) < 0.01
        
        # run replay validator
        req_obj = ScenarioRequest(**req_data)
        plan_objs = [HourlyPlanEntry(**p) for p in resp_data["hourly_plan"]]
        valid, failures = run_replay_validator(req_obj, act_interp, plan_objs)
        assert valid, f"Replay validation failed for {req_data['scenario_id']}: {failures}"
        
        # assert cost
        assert resp_data["total_cost_bdt"] <= expected["total_cost_bdt"] + 0.01
