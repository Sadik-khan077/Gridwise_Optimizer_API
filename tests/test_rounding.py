import pytest
import numpy as np
from app.optimizer.postprocess import postprocess_plan
from app.schemas import ScenarioRequest, Battery, HourEntry

def test_drift_absorption():
    req = ScenarioRequest(
        scenario_id="test",
        operator_notes=["no_op"],
        hours=[HourEntry(hour=i, demand_kwh=10.0, solar_kwh=5.0, tariff_bdt_per_kwh=10.0) for i in range(24)],
        battery=Battery(
            capacity_kwh=100.0,
            initial_energy_kwh=50.0,
            minimum_energy_kwh=20.0,
            max_charge_kwh_per_hour=50.0,
            max_discharge_kwh_per_hour=50.0
        )
    )
    
    # Fake LP result with a small drift due to floats
    # let's say charge=0, discharge=0 everywhere, but due to something e_23 = 50.02
    x = np.zeros(24 * 5)
    for h in range(24):
        x[5*h + 1] = 5.0 # solar
        x[5*h + 2] = 0.0 # c
        x[5*h + 3] = 0.0 # d
        x[5*h + 4] = 50.0
        
    # introduce drift at the end
    x[5*23 + 2] = 0.03 # charge 0.03 at hour 23
    
    plan = postprocess_plan(req, x, [])
    
    # It should absorb the drift and result in e_23 = 50.0 exactly
    assert abs(plan[23].battery_energy_after_kwh - 50.0) <= 0.01
