from fastapi import HTTPException
from .schemas import ScenarioRequest

def validate_scenario(req: ScenarioRequest):
    """
    Raises HTTP 400 for structural violations (e.g. 24-hour violations).
    Raises HTTP 422 for semantic issues (e.g. initial_energy > capacity).
    """
    # 24-hour violations (Structural -> 400)
    hours = [h.hour for h in req.hours]
    if len(set(hours)) != 24:
        raise HTTPException(status_code=400, detail="Must have exactly 24 unique hours")
    
    for h in req.hours:
        if h.hour < 0 or h.hour > 23:
            raise HTTPException(status_code=400, detail="Hours must be between 0 and 23")

    # Semantic validations -> 422
    if req.battery.initial_energy_kwh > req.battery.capacity_kwh:
        raise HTTPException(status_code=422, detail="initial_energy_kwh > capacity_kwh")
    
    if req.battery.minimum_energy_kwh > req.battery.capacity_kwh:
        raise HTTPException(status_code=422, detail="minimum_energy_kwh > capacity_kwh")

    for i, note in enumerate(req.operator_notes):
        if not note.strip():
            raise HTTPException(status_code=400, detail=f"Operator note {i} is empty after strip")
