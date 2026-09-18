import numpy as np
from typing import List, Dict, Any
from app.schemas import ScenarioRequest, HourlyPlanEntry

def postprocess_plan(req: ScenarioRequest, x: np.ndarray, directives: List[Dict]) -> List[HourlyPlanEntry]:
    eps = 1e-6
    e_before = req.battery.initial_energy_kwh
    
    raw_charges = []
    raw_discharges = []
    raw_s_used = []
    
    for h in range(24):
        base = 5 * h
        s_raw = x[base + 1]
        c_raw = x[base + 2]
        d_raw = x[base + 3]
        
        net_h = c_raw - d_raw
        if net_h > eps:
            raw_charges.append(net_h)
            raw_discharges.append(0.0)
        elif net_h < -eps:
            raw_charges.append(0.0)
            raw_discharges.append(-net_h)
        else:
            raw_charges.append(0.0)
            raw_discharges.append(0.0)
            
        raw_s_used.append(s_raw)
        
    def _build_plan(charges, discharges, s_used) -> List[HourlyPlanEntry]:
        plan = []
        e_curr = req.battery.initial_energy_kwh
        for h in range(24):
            c = round(charges[h], 2)
            d = round(discharges[h], 2)
            su = round(s_used[h], 2)
            
            if c > 0:
                action = "charge"
                bkwh = c
            elif d > 0:
                action = "discharge"
                bkwh = d
            else:
                action = "idle"
                bkwh = 0.0
                
            grid = round(req.hours[h].demand_kwh + c - d - su, 2)
            if grid < 0: grid = 0.0
            
            e_next = e_curr + c - d
            
            plan.append(HourlyPlanEntry(
                hour=h,
                grid_kwh=grid,
                solar_used_kwh=su,
                battery_action=action,
                battery_kwh=bkwh,
                battery_energy_after_kwh=e_next
            ))
            e_curr = e_next
        return plan
        
    plan = _build_plan(raw_charges, raw_discharges, raw_s_used)
    drift = plan[23].battery_energy_after_kwh - req.battery.initial_energy_kwh
    
    if abs(drift) < 1e-9:
        plan[23].battery_energy_after_kwh = req.battery.initial_energy_kwh
    elif abs(drift) > 0.01:
        # Try to fix drift by walking backwards
        for h in range(23, -1, -1):
            if abs(drift) <= 0.01:
                break
                
            c = round(raw_charges[h], 2)
            d = round(raw_discharges[h], 2)
            
            if drift > 0:
                # Ending with too much energy. Need less charge or more discharge.
                if c > 0:
                    adj = min(c, drift)
                    raw_charges[h] -= adj
                    drift -= adj
                elif d > 0 and d < req.battery.max_discharge_kwh_per_hour:
                    adj = min(req.battery.max_discharge_kwh_per_hour - d, drift)
                    raw_discharges[h] += adj
                    drift -= adj
            else:
                # Ending with too little energy. Need more charge or less discharge.
                if d > 0:
                    adj = min(d, -drift)
                    raw_discharges[h] -= adj
                    drift += adj
                elif c > 0 and c < req.battery.max_charge_kwh_per_hour:
                    adj = min(req.battery.max_charge_kwh_per_hour - c, -drift)
                    raw_charges[h] += adj
                    drift += adj
                    
        plan = _build_plan(raw_charges, raw_discharges, raw_s_used)
        
    return plan
