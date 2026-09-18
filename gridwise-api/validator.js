// validator.js
const { z } = require('zod');

const HourSchema = z.object({
    hour: z.number().int().min(0).max(23),
    demand_kwh: z.number().nonnegative(),
    solar_kwh: z.number().nonnegative(),
    tariff_bdt_per_kwh: z.number().nonnegative()
});

const BatterySchema = z.object({
    capacity_kwh: z.number().positive(),
    initial_energy_kwh: z.number().nonnegative(),
    minimum_energy_kwh: z.number().nonnegative(),
    max_charge_kwh_per_hour: z.number().nonnegative(),
    max_discharge_kwh_per_hour: z.number().nonnegative()
});

const RequestSchema = z.object({
    scenario_id: z.string(),
    operator_notes: z.array(z.string()).min(1).max(3),
    hours: z.array(HourSchema).length(24),
    battery: BatterySchema
});

function validateRequest(data) {
    return RequestSchema.parse(data);
}

function enforceGuardrails(directives) {
    if (!Array.isArray(directives)) return [];

    return directives.map((d, index) => {
        // Safe default structure
        const entry = {
            note_index: typeof d.note_index === 'number' ? d.note_index : index,
            applies: Boolean(d.applies),
            directive_type: d.directive_type || "no_op",
            structured_adjustment: d.structured_adjustment || null,
            explanation: d.explanation || "Interpreted directive"
        };

        if (!entry.applies || entry.directive_type === "no_op") {
            entry.applies = false;
            entry.directive_type = "no_op";
            entry.structured_adjustment = null;
            return entry;
        }

        // Validate hours array exists for applicable directives
        if (entry.structured_adjustment && Array.isArray(entry.structured_adjustment.hours)) {
            entry.structured_adjustment.hours = [...new Set(entry.structured_adjustment.hours)]
                .filter(h => typeof h === 'number' && h >= 0 && h <= 23)
                .sort((a, b) => a - b);
        } else {
            // If hours is missing, safe-fallback to no_op so it doesn't crash the optimizer
            entry.applies = false;
            entry.directive_type = "no_op";
            entry.structured_adjustment = null;
        }

        return entry;
    });
}

module.exports = { validateRequest, enforceGuardrails };