// solver.js
const solver = require('javascript-lp-solver');

function solveEnergyPlan(hours, battery, directives) {
    const model = {
        optimize: "cost",
        opType: "min",
        constraints: {},
        variables: {}
    };

    // 1. Initialize Base Constraints
    for (let h = 0; h < 24; h++) {
        model.constraints[`energy_bal_${h}`] = { equal: hours[h].demand_kwh };
        model.constraints[`state_bal_${h}`] = { equal: 0 };
        model.constraints[`max_solar_${h}`] = { max: hours[h].solar_kwh };
        model.constraints[`min_state_${h}`] = { min: battery.minimum_energy_kwh };
        model.constraints[`max_state_${h}`] = { max: battery.capacity_kwh };
        model.constraints[`max_charge_${h}`] = { max: battery.max_charge_kwh_per_hour };
        model.constraints[`max_discharge_${h}`] = { max: battery.max_discharge_kwh_per_hour };
    }

    model.constraints['end_of_day_neutral'] = { equal: battery.initial_energy_kwh };

    // 2. Safely Apply Validated Directives
    if (Array.isArray(directives)) {
        directives.forEach(d => {
            if (!d.applies || !d.structured_adjustment || !Array.isArray(d.structured_adjustment.hours)) return;
            
            d.structured_adjustment.hours.forEach(h => {
                if (h < 0 || h > 23) return;
                switch (d.directive_type) {
                    case 'solar_reduction':
                        if (typeof d.structured_adjustment.factor === 'number') {
                            model.constraints[`max_solar_${h}`].max = hours[h].solar_kwh * d.structured_adjustment.factor;
                        }
                        break;
                    case 'minimum_battery_reserve':
                        if (typeof d.structured_adjustment.minimum_energy_kwh === 'number') {
                            const currentMin = model.constraints[`min_state_${h}`].min;
                            model.constraints[`min_state_${h}`].min = Math.max(currentMin, d.structured_adjustment.minimum_energy_kwh);
                        }
                        break;
                    case 'no_charge_window':
                        model.constraints[`max_charge_${h}`].max = 0;
                        break;
                    case 'no_discharge_window':
                        model.constraints[`max_discharge_${h}`].max = 0;
                        break;
                    case 'max_grid_window':
                        if (typeof d.structured_adjustment.max_grid_kwh === 'number') {
                            model.constraints[`max_grid_${h}`] = { max: d.structured_adjustment.max_grid_kwh };
                        }
                        break;
                }
            });
        });
    }

    // 3. Populate Variables for the LP Solver
    for (let h = 0; h < 24; h++) {
        model.variables[`grid_${h}`] = { 
            cost: hours[h].tariff_bdt_per_kwh, 
            [`energy_bal_${h}`]: 1 
        };
        if (model.constraints[`max_grid_${h}`]) {
            model.variables[`grid_${h}`][`max_grid_${h}`] = 1;
        }

        model.variables[`solar_${h}`] = { 
            [`energy_bal_${h}`]: 1, 
            [`max_solar_${h}`]: 1 
        };

        model.variables[`charge_${h}`] = { 
            [`energy_bal_${h}`]: -1, 
            [`state_bal_${h}`]: -1, 
            [`max_charge_${h}`]: 1 
        };

        model.variables[`discharge_${h}`] = { 
            [`energy_bal_${h}`]: 1, 
            [`state_bal_${h}`]: 1, 
            [`max_discharge_${h}`]: 1 
        };

        model.variables[`state_${h}`] = { 
            [`state_bal_${h}`]: 1, 
            [`min_state_${h}`]: 1, 
            [`max_state_${h}`]: 1 
        };
        if (h < 23) {
            model.variables[`state_${h}`][`state_bal_${h+1}`] = -1;
        }
        if (h === 23) {
            model.variables[`state_${h}`]['end_of_day_neutral'] = 1;
        }
    }

    model.constraints['state_bal_0'].equal = battery.initial_energy_kwh;

    // 4. Run Solver
    const results = solver.Solve(model);
    return formatResults(results, hours, battery);
}

function formatResults(results, hours, battery) {
    const hourly_plan = [];
    let total_grid_kwh = 0;
    let total_cost_bdt = 0;
    let peak_grid_kwh = 0;

    for (let h = 0; h < 24; h++) {
        const grid = results[`grid_${h}`] || 0;
        const solar = results[`solar_${h}`] || 0;
        const charge = results[`charge_${h}`] || 0;
        const discharge = results[`discharge_${h}`] || 0;
        const state = results[`state_${h}`] || (h === 0 ? battery.initial_energy_kwh : hourly_plan[h-1].battery_energy_after_kwh);

        let action = "idle";
        let action_kwh = 0;
        if (charge > 0.001) { action = "charge"; action_kwh = charge; }
        else if (discharge > 0.001) { action = "discharge"; action_kwh = discharge; }

        total_grid_kwh += grid;
        total_cost_bdt += grid * hours[h].tariff_bdt_per_kwh;
        if (grid > peak_grid_kwh) peak_grid_kwh = grid;

        hourly_plan.push({
            hour: h,
            grid_kwh: Number(grid.toFixed(2)),
            solar_used_kwh: Number(solar.toFixed(2)),
            battery_action: action,
            battery_kwh: Number(action_kwh.toFixed(2)),
            battery_energy_after_kwh: Number(state.toFixed(2))
        });
    }

    return {
        hourly_plan,
        total_grid_kwh: Number(total_grid_kwh.toFixed(2)),
        total_cost_bdt: Number(total_cost_bdt.toFixed(2)),
        peak_grid_kwh: Number(peak_grid_kwh.toFixed(2))
    };
}

module.exports = { solveEnergyPlan };