const { z } = require('zod');

const optimizationSchema = z.object({
    scenario_id: z.string(),
    operator_notes: z.array(z.string()).min(1).max(3),
    hours: z.array(z.object({
        hour: z.number().min(0).max(23),
        demand_kwh: z.number(),
        solar_kwh: z.number(),
        tariff_bdt_per_kwh: z.number()
    })).length(24),
    battery: z.object({
        capacity_kwh: z.number(),
        initial_energy_kwh: z.number(),
        minimum_energy_kwh: z.number(),
        max_charge_kwh_per_hour: z.number(),
        max_discharge_kwh_per_hour: z.number()
    })
});

exports.validateOptimizationRequest = (req, res, next) => {
    try {
        req.body = optimizationSchema.parse(req.body);
        next();
    } catch (e) {
        // Log the exact validation failure to the terminal
        console.error("[Zod Error]:", JSON.stringify(e.errors, null, 2));
        
        // Return the exact field errors to Postman
        res.status(400).json({ 
            error: "Malformed JSON or structurally invalid request",
            details: e.errors 
        });
    }
};