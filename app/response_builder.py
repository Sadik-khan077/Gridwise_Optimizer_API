from typing import List, Dict
from app.schemas import OptimizeResponse, DirectiveInterpretationEntry, HourlyPlanEntry, ScenarioRequest

def build_response(req: ScenarioRequest, directives: List[Dict], plan: List[HourlyPlanEntry]) -> OptimizeResponse:
    interps = []
    applied_count = 0
    noop_count = 0
    for d in directives:
        interps.append(DirectiveInterpretationEntry(
            note_index=d["note_index"],
            applies=d["applies"],
            directive_type=d["directive_type"],
            structured_adjustment=d["structured_adjustment"],
            explanation=d["explanation"]
        ))
        if d["applies"]:
            applied_count += 1
        else:
            noop_count += 1
            
    total_grid = sum(p.grid_kwh for p in plan)
    peak_grid = max(p.grid_kwh for p in plan)
    
    total_cost = 0.0
    for i, p in enumerate(plan):
        total_cost += p.grid_kwh * req.hours[i].tariff_bdt_per_kwh
        
    summary = f"Applied {applied_count} operator directive(s) and {noop_count} no-op note(s); shifted battery use toward high-tariff hours while keeping battery at/above required reserves."
    
    return OptimizeResponse(
        scenario_id=req.scenario_id,
        directive_interpretation=interps,
        hourly_plan=plan,
        total_grid_kwh=round(total_grid, 2),
        total_cost_bdt=round(total_cost, 2),
        peak_grid_kwh=round(peak_grid, 2),
        plan_summary=summary
    )
