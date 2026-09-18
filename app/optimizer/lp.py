import numpy as np
import scipy.optimize as opt
from typing import List, Dict, Tuple
from app.schemas import ScenarioRequest
import copy

def _build_and_solve_lp(req: ScenarioRequest, directives: List[Dict], tight_e23: bool = True) -> Tuple[bool, np.ndarray]:
    n_vars = 24 * 5
    c = np.zeros(n_vars)
    for h in range(24):
        c[5 * h] = req.hours[h].tariff_bdt_per_kwh
        
    bounds = []
    grid_caps = {}
    solar_factors = {}
    no_charge = set()
    no_discharge = set()
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
                
    for h in range(24):
        max_grid = grid_caps.get(h, 1e6)
        bounds.append((0, max_grid))
        
        eff_solar = req.hours[h].solar_kwh * solar_factors.get(h, 1.0)
        bounds.append((0, eff_solar))
        
        max_c = 0.0 if h in no_charge else req.battery.max_charge_kwh_per_hour
        bounds.append((0, max_c))
        
        max_d = 0.0 if h in no_discharge else req.battery.max_discharge_kwh_per_hour
        bounds.append((0, max_d))
        
        min_e = max(req.battery.minimum_energy_kwh, reserves.get(h, 0.0))
        bounds.append((min_e, req.battery.capacity_kwh))
        
    A_eq = []
    b_eq = []
    
    for h in range(24):
        row = np.zeros(n_vars)
        base = 5 * h
        row[base + 0] = 1
        row[base + 1] = 1
        row[base + 2] = -1
        row[base + 3] = 1
        A_eq.append(row)
        b_eq.append(req.hours[h].demand_kwh)
        
    for h in range(24):
        row = np.zeros(n_vars)
        base = 5 * h
        row[base + 4] = 1
        row[base + 2] = -1
        row[base + 3] = 1
        
        if h == 0:
            A_eq.append(row)
            b_eq.append(req.battery.initial_energy_kwh)
        else:
            row[(h-1)*5 + 4] = -1
            A_eq.append(row)
            b_eq.append(0.0)
            
    if tight_e23:
        row = np.zeros(n_vars)
        row[5 * 23 + 4] = 1
        A_eq.append(row)
        b_eq.append(req.battery.initial_energy_kwh)
    
    res = opt.linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    
    if res.status == 0:
        return True, res.x
    return False, np.array([])

def solve_lp_with_recovery(req: ScenarioRequest, directives: List[Dict]) -> Tuple[bool, np.ndarray]:
    success, x = _build_and_solve_lp(req, directives)
    if success:
        return True, x
        
    # Recovery: drop directives one by one
    drop_order = ["max_grid_window", "no_charge_window", "no_discharge_window", "minimum_battery_reserve", "solar_reduction"]
    
    active_directives = copy.deepcopy(directives)
    
    for dtype in drop_order:
        # find directives of this type
        for d in active_directives:
            if d["directive_type"] == dtype and d["applies"]:
                d["applies"] = False
                
        success, x = _build_and_solve_lp(req, active_directives)
        if success:
            return True, x
            
    # Base case (no directives)
    for d in active_directives:
        d["applies"] = False
        
    success, x = _build_and_solve_lp(req, active_directives)
    return success, x
