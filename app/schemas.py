from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union

class HourEntry(BaseModel):
    hour: int = Field(ge=0, le=23)
    demand_kwh: float = Field(ge=0.0)
    solar_kwh: float = Field(ge=0.0)
    tariff_bdt_per_kwh: float = Field(ge=0.0)

class Battery(BaseModel):
    capacity_kwh: float = Field(ge=0.0)
    initial_energy_kwh: float = Field(ge=0.0)
    minimum_energy_kwh: float = Field(ge=0.0)
    max_charge_kwh_per_hour: float = Field(ge=0.0)
    max_discharge_kwh_per_hour: float = Field(ge=0.0)

class ScenarioRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    operator_notes: List[str] = Field(min_length=1, max_length=3)
    hours: List[HourEntry] = Field(min_length=24, max_length=24)
    battery: Battery

class DirectiveInterpretationEntry(BaseModel):
    note_index: int
    applies: bool
    directive_type: str
    structured_adjustment: Optional[Dict[str, Any]] = None
    explanation: str

class HourlyPlanEntry(BaseModel):
    hour: int
    grid_kwh: float
    solar_used_kwh: float
    battery_action: str  # "charge" | "discharge" | "idle"
    battery_kwh: float
    battery_energy_after_kwh: float

class OptimizeResponse(BaseModel):
    scenario_id: str
    directive_interpretation: List[DirectiveInterpretationEntry]
    hourly_plan: List[HourlyPlanEntry]
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float
    plan_summary: str
