const solver = require('javascript-lp-solver');

exports.runOptimization = (hours, battery, validInterpretations) => {
    let model = { optimize: "cost", opType: "min", constraints: {}, variables: {} };

    // 1. Process active constraints from LLM mapped by hour 0-23
    const config = {
        solarFactors: Array(24).fill(1.0),
        minReserves: Array(24).fill(battery.minimum_energy_kwh),
        noCharge: Array(24).fill(false),
        noDischarge: Array(24).fill(false),
        maxGrid: Array(24).fill(Infinity)
    };

    validInterpretations.forEach(dir => {
        if (!dir.applies || !dir.structured_adjustment?.hours) return;
        const hrArr = dir.structured_adjustment.hours;
        
        if (dir.directive_type === "solar_reduction") hrArr.forEach(h => config.solarFactors[h] = dir.structured_adjustment.factor);
        if (dir.directive_type === "minimum_battery_reserve") hrArr.forEach(h => config.minReserves[h] = Math.max(config.minReserves[h], dir.structured_adjustment.minimum_energy_kwh));
        if (dir.directive_type === "no_charge_window") hrArr.forEach(h => config.noCharge[h] = true);
        if (dir.directive_type === "no_discharge_window") hrArr.forEach(h => config.noDischarge[h] = true);
        if (dir.directive_type === "max_grid_window") hrArr.forEach(h => config.maxGrid[h] = Math.min(config.maxGrid[h], dir.structured_adjustment.max_grid_kwh));
    });

    // 2. Build mathematical linear programming model
    for (let h = 0; h < 24; h++) {
        const { demand_kwh, solar_kwh, tariff_bdt_per_kwh } = hours.find(x => x.hour === h);
        
        let eff_solar = solar_kwh * config.solarFactors[h];
        let max_chg = config.noCharge[h] ? 0 : battery.max_charge_kwh_per_hour;
        let max_dischg = config.noDischarge[h] ? 0 : battery.max_discharge_kwh_per_hour;

        // Equations
        model.constraints[`eq_bal_${h}`] = { equal: demand_kwh }; // grid + solar + dischg - chg = demand
        model.constraints[`solar_max_${h}`] = { max: eff_solar };
        model.constraints[`chg_max_${h}`] = { max: max_chg };
        model.constraints[`dischg_max_${h}`] = { max: max_dischg };
        
        if (config.maxGrid[h] !== Infinity) model.constraints[`grid_max_${h}`] = { max: config.maxGrid[h] };

        // Battery boundaries and transition
        if (h === 23) {
            model.constraints[`E_bound_23`] = { equal: battery.initial_energy_kwh }; // End of day rule
        } else {
            model.constraints[`E_bound_${h}`] = { min: config.minReserves[h], max: battery.capacity_kwh };
        }

        model.constraints[`eq_batt_${h}`] = h === 0 ? { equal: battery.initial_energy_kwh } : { equal: 0 };

        // Bind Variables to Constraints
        model.variables[`grid_${h}`] = { [`eq_bal_${h}`]: 1, cost: tariff_bdt_per_kwh };
        if (config.maxGrid[h] !== Infinity) model.variables[`grid_${h}`][`grid_max_${h}`] = 1;

        model.variables[`solar_used_${h}`] = { [`eq_bal_${h}`]: 1, [`solar_max_${h}`]: 1 };
        model.variables[`charge_${h}`] = { [`eq_bal_${h}`]: -1, [`eq_batt_${h}`]: -1, [`chg_max_${h}`]: 1, cost: 0.000001 };
        model.variables[`discharge_${h}`] = { [`eq_bal_${h}`]: 1, [`eq_batt_${h}`]: 1, [`dischg_max_${h}`]: 1, cost: 0.000001 };
        
        model.variables[`E_${h}`] = { [`eq_batt_${h}`]: 1, [`E_bound_${h}`]: 1 };
        if (h < 23) model.variables[`E_${h}`][`eq_batt_${h+1}`] = -1; // Bridge state to next hour
    }

    const results = solver.Solve(model);
    
    // 3. Package JSON Response
    const hourly_plan = [];
    let total_grid = 0, total_cost = 0, peak_grid = 0;

    for (let h = 0; h < 24; h++) {
        let grid = results[`grid_${h}`] || 0;
        let solar = results[`solar_used_${h}`] || 0;
        let charge = results[`charge_${h}`] || 0;
        let discharge = results[`discharge_${h}`] || 0;
        let E_after = results[`E_${h}`] || config.minReserves[h];

        charge = charge < 0.0001 ? 0 : charge;
        discharge = discharge < 0.0001 ? 0 : discharge;

        let action = "idle", bat_kwh = 0;
        if (charge > discharge) { action = "charge"; bat_kwh = charge - discharge; }
        else if (discharge > charge) { action = "discharge"; bat_kwh = discharge - charge; }

        hourly_plan.push({
            hour: h,
            grid_kwh: Number(grid.toFixed(4)),
            solar_used_kwh: Number(solar.toFixed(4)),
            battery_action: action,
            battery_kwh: Number(bat_kwh.toFixed(4)),
            battery_energy_after_kwh: Number(E_after.toFixed(4))
        });

        total_grid += grid;
        total_cost += grid * hours.find(x => x.hour === h).tariff_bdt_per_kwh;
        if (grid > peak_grid) peak_grid = grid;
    }

    return {
        hourly_plan,
        total_grid_kwh: Number(total_grid.toFixed(4)),
        total_cost_bdt: Number(total_cost.toFixed(4)),
        peak_grid_kwh: Number(peak_grid.toFixed(4)),
        plan_summary: "Generated optimal cost schedule observing LLM operator constraints."
    };
};