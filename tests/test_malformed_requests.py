import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_malformed_json():
    response = client.post("/optimize-energy", data="{malformed json")
    assert response.status_code == 400

def test_23_hours():
    req = {
        "scenario_id": "test",
        "operator_notes": ["note 1"],
        "hours": [{"hour": i, "demand_kwh": 10, "solar_kwh": 5, "tariff_bdt_per_kwh": 10} for i in range(23)],
        "battery": {
            "capacity_kwh": 100,
            "initial_energy_kwh": 50,
            "minimum_energy_kwh": 20,
            "max_charge_kwh_per_hour": 50,
            "max_discharge_kwh_per_hour": 50
        }
    }
    response = client.post("/optimize-energy", json=req)
    assert response.status_code == 400

def test_initial_energy_greater_than_capacity():
    req = {
        "scenario_id": "test",
        "operator_notes": ["note 1"],
        "hours": [{"hour": i, "demand_kwh": 10, "solar_kwh": 5, "tariff_bdt_per_kwh": 10} for i in range(24)],
        "battery": {
            "capacity_kwh": 100,
            "initial_energy_kwh": 150, # invalid
            "minimum_energy_kwh": 20,
            "max_charge_kwh_per_hour": 50,
            "max_discharge_kwh_per_hour": 50
        }
    }
    response = client.post("/optimize-energy", json=req)
    assert response.status_code == 422
