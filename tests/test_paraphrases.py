import pytest
from app.interpreter.llm_client import interpret_notes

@pytest.mark.asyncio
async def test_paraphrase_solar():
    notes = [
        "PV production will drop to about 20% between 13:00 and 15:00",
        "Panel washing from one until three will leave roughly one-fifth of normal solar output",
        "Expect a 50% cut in rooftop solar during the 10 AM-noon window",
        "80% reduction in solar output from 9am to 10am"
    ]
    res = await interpret_notes(notes, 100)
    assert len(res) == 4
    
    # "PV production will drop to about 20% between 13:00 and 15:00" -> [13, 14], 0.2
    assert res[0]["directive_type"] == "solar_reduction"
    assert res[0]["structured_adjustment"]["hours"] == [13, 14]
    assert abs(res[0]["structured_adjustment"]["factor"] - 0.2) < 0.01

    # "Panel washing from one until three will leave roughly one-fifth of normal solar output" -> [13, 14], 0.2
    assert res[1]["directive_type"] == "solar_reduction"
    assert res[1]["structured_adjustment"]["hours"] == [13, 14]
    assert abs(res[1]["structured_adjustment"]["factor"] - 0.2) < 0.01

    # "Expect a 50% cut in rooftop solar during the 10 AM-noon window" -> [10, 11], 0.5
    assert res[2]["directive_type"] == "solar_reduction"
    assert res[2]["structured_adjustment"]["hours"] == [10, 11]
    assert abs(res[2]["structured_adjustment"]["factor"] - 0.5) < 0.01

@pytest.mark.asyncio
async def test_paraphrase_reserve():
    notes = [
        "Keep at least 30% of battery capacity in reserve from 7 PM until 10 PM",
        "Maintain a minimum of 40kwh in the battery between 18:00 and 20:00",
        "Battery must stay above 25 percent capacity from midnight to 2 AM"
    ]
    res = await interpret_notes(notes, 100)
    
    assert res[0]["directive_type"] == "minimum_battery_reserve"
    assert res[0]["structured_adjustment"]["hours"] == [19, 20, 21]
    assert res[0]["structured_adjustment"]["minimum_energy_kwh"] == 30.0

    assert res[1]["directive_type"] == "minimum_battery_reserve"
    assert res[1]["structured_adjustment"]["hours"] == [18, 19]
    assert res[1]["structured_adjustment"]["minimum_energy_kwh"] == 40.0

@pytest.mark.asyncio
async def test_paraphrase_no_charge():
    notes = [
        "The charger will be isolated from 2 AM until 5 AM",
        "No charging allowed between 3 PM and 4 PM",
        "Charger maintenance from 14:00 to 16:00, charging disabled"
    ]
    res = await interpret_notes(notes, 100)
    assert res[0]["directive_type"] == "no_charge_window"
    assert res[0]["structured_adjustment"]["hours"] == [2, 3, 4]
    
@pytest.mark.asyncio
async def test_paraphrase_no_discharge():
    notes = [
        "Discharge is prohibited during relay testing from 5 PM until 7 PM",
        "Do not discharge battery from 8 AM to 10 AM",
        "Battery discharging disabled between 21:00 and 22:00"
    ]
    res = await interpret_notes(notes, 100)
    assert res[0]["directive_type"] == "no_discharge_window"
    assert res[0]["structured_adjustment"]["hours"] == [17, 18]
    
@pytest.mark.asyncio
async def test_paraphrase_max_grid():
    notes = [
        "Grid intake must stay at or below 190 kWh from 7 PM until 10 PM",
        "Cap grid import at 50 kwh between 12 PM and 2 PM",
        "Maximum grid usage is 200 from 08:00 to 09:00"
    ]
    res = await interpret_notes(notes, 100)
    assert res[0]["directive_type"] == "max_grid_window"
    assert res[0]["structured_adjustment"]["hours"] == [19, 20, 21]
    assert res[0]["structured_adjustment"]["max_grid_kwh"] == 190.0
    
@pytest.mark.asyncio
async def test_paraphrase_no_op():
    notes = [
        "The campus will host a job fair next month",
        "Library hours are extended to 10 PM",
        "Cafeteria menu changes tomorrow",
        "Sports registration opens at noon",
        "Seminar booking is cancelled",
        "Club notices will be posted on the bulletin board"
    ]
    res = await interpret_notes(notes, 100)
    for r in res:
        assert r["directive_type"] == "no_op"
        assert r["applies"] is False
