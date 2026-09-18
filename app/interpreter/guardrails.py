from typing import Tuple, List, Dict, Any

def _is_numeric(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)

def validate_and_parse_llm_output(raw_array: Any, notes: List[str], capacity_kwh: float) -> Tuple[bool, str, List[Dict]]:
    if not isinstance(raw_array, list):
        return False, "Output is not a JSON array", []
    
    if len(raw_array) != len(notes):
        return False, f"Expected {len(notes)} entries, got {len(raw_array)}", []
    
    for i, entry in enumerate(raw_array):
        if not isinstance(entry, dict):
            return False, f"Entry {i} is not an object", []
        
        for field in ["note_index", "applies", "directive_type", "structured_adjustment", "explanation"]:
            if field not in entry:
                return False, f"Entry {i} missing field '{field}'", []
                
        if not isinstance(entry["note_index"], int) or isinstance(entry["note_index"], bool):
            return False, f"Entry {i} note_index is not an integer", []
        if not isinstance(entry["applies"], bool):
            return False, f"Entry {i} applies is not a boolean", []
        if not isinstance(entry["directive_type"], str):
            return False, f"Entry {i} directive_type is not a string", []
        if not isinstance(entry["explanation"], str):
            return False, f"Entry {i} explanation is not a string", []
    
    raw_array = sorted(raw_array, key=lambda x: x["note_index"])
    
    for i in range(len(notes)):
        if raw_array[i]["note_index"] != i:
            return False, f"Missing or duplicate note_index {i}", []
    
    allowed_types = {"solar_reduction", "minimum_battery_reserve", "no_charge_window", "no_discharge_window", "max_grid_window", "no_op"}
    
    for i, entry in enumerate(raw_array):
        dtype = entry["directive_type"]
        if dtype not in allowed_types:
            return False, f"Entry {i} has invalid directive_type '{dtype}'", []
            
        applies = entry["applies"]
        adj = entry["structured_adjustment"]
        
        if dtype == "no_op":
            if applies is not False:
                return False, f"Entry {i} (no_op) must have applies=false", []
            if adj is not None:
                return False, f"Entry {i} (no_op) must have structured_adjustment=null", []
        else:
            if applies is not True:
                return False, f"Entry {i} ({dtype}) must have applies=true", []
            if not isinstance(adj, dict):
                return False, f"Entry {i} ({dtype}) must have an object for structured_adjustment", []
                
            if "hours" not in adj or not isinstance(adj["hours"], list):
                return False, f"Entry {i} ({dtype}) structured_adjustment missing 'hours' list", []
                
            hours = adj["hours"]
            for h in hours:
                if not isinstance(h, int) or isinstance(h, bool) or h < 0 or h > 23:
                    return False, f"Entry {i} has invalid hour {h}", []
            
            unique_hours = list(set(hours))
            unique_hours.sort()
            adj["hours"] = unique_hours
            
            if dtype == "solar_reduction":
                if "factor" not in adj or not _is_numeric(adj["factor"]):
                    return False, f"Entry {i} missing valid 'factor'", []
                factor = float(adj["factor"])
                if factor < 0 or factor > 1:
                    return False, f"Entry {i} factor must be between 0 and 1", []
                factor = round(factor, 4)
                if abs(factor - round(factor)) < 1e-9: factor = float(round(factor))
                adj["factor"] = factor
            elif dtype == "minimum_battery_reserve":
                if "minimum_energy_kwh" not in adj or not _is_numeric(adj["minimum_energy_kwh"]):
                    return False, f"Entry {i} missing valid 'minimum_energy_kwh'", []
                kwh = float(adj["minimum_energy_kwh"])
                if kwh < 0 or kwh > capacity_kwh:
                    return False, f"Entry {i} minimum_energy_kwh must be between 0 and capacity", []
                kwh = round(kwh, 2)
                if abs(kwh - round(kwh)) < 1e-9: kwh = float(round(kwh))
                adj["minimum_energy_kwh"] = kwh
            elif dtype == "max_grid_window":
                if "max_grid_kwh" not in adj or not _is_numeric(adj["max_grid_kwh"]):
                    return False, f"Entry {i} missing valid 'max_grid_kwh'", []
                kwh = float(adj["max_grid_kwh"])
                if kwh < 0:
                    return False, f"Entry {i} max_grid_kwh must be >= 0", []
                kwh = round(kwh, 2)
                if abs(kwh - round(kwh)) < 1e-9: kwh = float(round(kwh))
                adj["max_grid_kwh"] = kwh

    return True, "", raw_array
