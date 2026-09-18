from typing import Tuple, List, Dict
from app.schemas import ScenarioRequest, HourlyPlanEntry

def run_replay_validator(req: ScenarioRequest, directives: List[Dict], plan: List[HourlyPlanEntry]) -> Tuple[bool, List[str]]:
    TOL = 0.01
    failures = []
    
    if len(plan) != 24:
        failures.append(f"Expected 24 plan entries, got {len(plan)}")
        return False, failures
        
    hours = [p.hour for p in plan]
    if len(set(hours)) != 24 or min(hours) != 0 or max(hours) != 23:
        failures.append("Plan hours must be exactly 0-23 unique")
        return False, failures
        
    plan_dict = {p.hour: p for p in plan}
    
    solar_factors = {}
    no_charge = set()
    no_discharge = set()
    grid_caps = {}
    reserves = {}
    
    for d in directives:
        if not d["applies"]:
            continue
        dtype = d["directive_type"]
        adj = d["structured_adjustment"]
        if not adj or "hours" not in adj:
            continue
            
        for h in adj["hours"]:
            if dtype == "max_grid_window":
                grid_caps[h] = min(grid_caps.get(h, float('inf')), adj["max_grid_kwh"])
            elif dtype == "solar_reduction":
                solar_factors[h] = min(solar_factors.get(h, 1.0), adj["factor"])
            elif dtype == "no_charge_window":
                no_charge.add(h)
            elif dtype == "no_discharge_window":
                no_discharge.add(h)
            elif dtype == "minimum_battery_reserve":
                reserves[h] = max(reserves.get(h, 0.0), adj["minimum_energy_kwh"])

    e_before = req.battery.initial_energy_kwh
    
    for h in range(24):
        p = plan_dict[h]
        rh = req.hours[h]
        
        # clamp tiny negatives
        if -TOL <= p.grid_kwh < 0: p.grid_kwh = 0.0
        if -TOL <= p.solar_used_kwh < 0: p.solar_used_kwh = 0.0
        if -TOL <= p.battery_kwh < 0: p.battery_kwh = 0.0
        
        if p.grid_kwh < 0: failures.append(f"Hour {h}: grid_kwh < 0")
        if p.solar_used_kwh < 0: failures.append(f"Hour {h}: solar_used_kwh < 0")
        if p.battery_kwh < 0: failures.append(f"Hour {h}: battery_kwh < 0")
        
        eff_solar = rh.solar_kwh * solar_factors.get(h, 1.0)
        if p.solar_used_kwh > eff_solar + TOL:
            failures.append(f"Hour {h}: solar_used_kwh {p.solar_used_kwh} > effective_solar {eff_solar}")
            
        charge = p.battery_kwh if p.battery_action == "charge" else 0.0
        discharge = p.battery_kwh if p.battery_action == "discharge" else 0.0
        
        if p.battery_action == "idle" and p.battery_kwh > TOL:
            failures.append(f"Hour {h}: battery_action is idle but battery_kwh is {p.battery_kwh}")
            
        e_after = e_before + charge - discharge
        if abs(e_after - p.battery_energy_after_kwh) > TOL:
            failures.append(f"Hour {h}: computed e_after {e_after} != reported {p.battery_energy_after_kwh}")
            
        min_e = max(req.battery.minimum_energy_kwh, reserves.get(h, 0.0))
        if e_after < min_e - TOL:
            failures.append(f"Hour {h}: e_after {e_after} < min_e {min_e}")
        if e_after > req.battery.capacity_kwh + TOL:
            failures.append(f"Hour {h}: e_after {e_after} > capacity {req.battery.capacity_kwh}")
            
        if charge > req.battery.max_charge_kwh_per_hour + TOL:
            failures.append(f"Hour {h}: charge {charge} > max_charge {req.battery.max_charge_kwh_per_hour}")
        if discharge > req.battery.max_discharge_kwh_per_hour + TOL:
            failures.append(f"Hour {h}: discharge {discharge} > max_discharge {req.battery.max_discharge_kwh_per_hour}")
            
        if h in no_charge and charge > TOL:
            failures.append(f"Hour {h}: charge in no_charge_window")
        if h in no_discharge and discharge > TOL:
            failures.append(f"Hour {h}: discharge in no_discharge_window")
            
        if h in grid_caps and p.grid_kwh > grid_caps[h] + TOL:
            failures.append(f"Hour {h}: grid {p.grid_kwh} > cap {grid_caps[h]}")
            
        balance = p.grid_kwh + p.solar_used_kwh + discharge - rh.demand_kwh - charge
        if abs(balance) > TOL:
            failures.append(f"Hour {h}: energy balance violated by {balance}")
            
        e_before = e_after
        
    if abs(e_before - req.battery.initial_energy_kwh) > TOL:
        failures.append(f"End of day neutrality violated. e_23={e_before}, initial={req.battery.initial_energy_kwh}")
        
    return len(failures) == 0, failures
