def build_system_prompt(capacity_kwh: float) -> str:
    return f"""You interpret campus operator notes for a 24-hour energy scheduler (hours 0-23).

OUTPUT: a JSON array with exactly one entry per note, in order. Each entry:
{{"note_index": <int>, "applies": <bool>, "directive_type": <str>,
 "structured_adjustment": <obj or null>, "explanation": <short str>}}

TIME WINDOWS: start hour inclusive, end hour EXCLUSIVE. "1 PM to 3 PM" -> [13,14].
"11 AM until 2 PM" -> [11,12,13]. "13:00 and 15:00" -> [13,14].
"from noon until 2 PM" -> [12,13]. If ambiguous (e.g. "one until three" for solar), assume PM -> [13,14].
Hours: unique integers 0-23, ascending.

DIRECTIVE TYPES (the only allowed ones):
1. solar_reduction: {{"hours":[...],"factor":F}}. F = usable fraction REMAINING,
   0 <= F <= 1. "80% reduction" -> 0.2. "drops to about 20%" -> 0.2.
   "one-fifth of normal output" -> 0.2. "about half" -> 0.5.
2. minimum_battery_reserve: {{"hours":[...],"minimum_energy_kwh":K}}.
   If the note states a percentage of battery capacity, K = pct * CAPACITY.
   Battery capacity for this scenario: {capacity_kwh} kWh.
3. no_charge_window: {{"hours":[...]}}. Battery charging forbidden those hours.
4. no_discharge_window: {{"hours":[...]}}. Battery discharging forbidden those hours.
5. max_grid_window: {{"hours":[...],"max_grid_kwh":M}}. Grid import capped per hour.
6. no_op: note is irrelevant to today's energy schedule -> applies=false,
   structured_adjustment=null.

If a note does not affect the 24-hour electricity schedule (e.g., cafeteria menu,
library hours, sports registration, seminar booking, club notices), use no_op.
For every non-no_op directive, applies=true.

Never invent directive types. Never alter demand, solar, tariff, or battery limits.
Respond with ONLY the JSON array — no prose, no markdown fences.
"""

def build_user_prompt(notes: list[str]) -> str:
    lines = ["Notes:"]
    for i, note in enumerate(notes):
        lines.append(f"[{i}] {note}")
    return "\n".join(lines)
