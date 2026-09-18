import re
from typing import List, Dict, Optional

def parse_time_window(text: str) -> Optional[List[int]]:
    # Very basic time window extractor for fallback
    # Convert things like "1 PM", "1pm", "13:00", "noon", "midnight"
    
    # Find all occurrences of times
    time_pattern = r'\b(\d{1,2})(?::00)?\s*(am|pm|a\.m\.|p\.m\.)?\b|\b(noon|midnight)\b'
    matches = list(re.finditer(time_pattern, text))
    
    if len(matches) < 2:
        return None
        
    def to_hour(m) -> int:
        if m.group(3):
            if m.group(3) == 'noon': return 12
            if m.group(3) == 'midnight': return 0
        
        hr = int(m.group(1))
        ampm = (m.group(2) or "").replace(".", "").lower()
        
        if ampm == 'pm' and hr < 12:
            hr += 12
        elif ampm == 'am' and hr == 12:
            hr = 0
            
        return hr
        
    start_hr = to_hour(matches[0])
    end_hr = to_hour(matches[1])
    
    hours = []
    curr = start_hr
    while curr != end_hr:
        hours.append(curr)
        curr = (curr + 1) % 24
        
    return hours

def run_fallback_interpreter(notes: List[str], capacity_kwh: float) -> List[Dict]:
    results = []
    
    for i, note in enumerate(notes):
        lower_note = note.lower()
        hours = parse_time_window(lower_note)
        
        # We need hours for windows
        has_solar = bool(re.search(r'(solar|pv|panel|sun|photovoltaic)', lower_note)) and bool(re.search(r'(reduc|drop|fall|degrad|cloud|wash|clean|inspect|maintenan|inverter)', lower_note))
        has_reserve = bool(re.search(r'(reserve|keep at least|minimum.*batter|batter.*at least|stored)', lower_note))
        has_no_charge = bool(re.search(r'(charge|charging|charger)', lower_note)) and bool(re.search(r'(not|no|disable|unavailable|isolated|prohibit|forbid|maintenance)', lower_note))
        has_no_discharge = bool(re.search(r'(discharge|discharging)', lower_note)) and bool(re.search(r'(not|no|disable|prohibit|forbid|relay|protect)', lower_note))
        has_max_grid = bool(re.search(r'(grid|import|feeder|transformer|substation|intake)', lower_note)) and bool(re.search(r'(not exceed|no more than|at or below|limit|cap|maximum|constrain)', lower_note))

        # Check for numbers for factors/reserves/caps
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(%|kwh)?', lower_note)
        
        if has_reserve and numbers and hours:
            # Check if it's a percentage
            val = float(numbers[0][0])
            is_pct = '%' in lower_note or 'percent' in lower_note or numbers[0][1] == '%'
            if is_pct:
                val = (val / 100.0) * capacity_kwh
            
            results.append({
                "note_index": i,
                "applies": True,
                "directive_type": "minimum_battery_reserve",
                "structured_adjustment": {"hours": hours, "minimum_energy_kwh": val},
                "explanation": "Fallback parsed minimum reserve"
            })
        elif has_solar and hours:
            factor = 1.0
            if bool(re.search(r'(\d+)%\s*reduction', lower_note)):
                m = re.search(r'(\d+)%\s*reduction', lower_note)
                factor = 1.0 - (float(m.group(1)) / 100.0)
            elif bool(re.search(r'drops to (\d+)%', lower_note)):
                m = re.search(r'drops to (\d+)%', lower_note)
                factor = float(m.group(1)) / 100.0
            elif "half" in lower_note:
                factor = 0.5
            elif "one-fifth" in lower_note or "20%" in lower_note:
                factor = 0.2
            
            results.append({
                "note_index": i,
                "applies": True,
                "directive_type": "solar_reduction",
                "structured_adjustment": {"hours": hours, "factor": factor},
                "explanation": "Fallback parsed solar reduction"
            })
        elif has_no_discharge and hours:
            results.append({
                "note_index": i,
                "applies": True,
                "directive_type": "no_discharge_window",
                "structured_adjustment": {"hours": hours},
                "explanation": "Fallback parsed no discharge"
            })
        elif has_no_charge and hours:
            results.append({
                "note_index": i,
                "applies": True,
                "directive_type": "no_charge_window",
                "structured_adjustment": {"hours": hours},
                "explanation": "Fallback parsed no charge"
            })
        elif has_max_grid and numbers and hours:
            val = float(numbers[0][0])
            results.append({
                "note_index": i,
                "applies": True,
                "directive_type": "max_grid_window",
                "structured_adjustment": {"hours": hours, "max_grid_kwh": val},
                "explanation": "Fallback parsed max grid window"
            })
        else:
            results.append({
                "note_index": i,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "Fallback parsed no op"
            })
            
    return results
