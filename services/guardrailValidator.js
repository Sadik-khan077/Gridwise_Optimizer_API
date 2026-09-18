exports.validateGuardrails = (rawInterpretations, operator_notes) => {
    const validInterpretations = [];
    const supportedTypes = [
        "solar_reduction", "minimum_battery_reserve", 
        "no_charge_window", "no_discharge_window", 
        "max_grid_window", "no_op"
    ];

    for (let i = 0; i < operator_notes.length; i++) {
        // Enforce note_index ordering
        let entry = rawInterpretations.find(e => e.note_index === i);
        
        if (!entry || !supportedTypes.includes(entry.directive_type)) {
            // Controlled fallback if LLM hallucinates an unsupported structure
            validInterpretations.push({
                note_index: i,
                applies: false,
                directive_type: "no_op",
                structured_adjustment: null,
                explanation: "Fallback: The model returned an invalid structure."
            });
            continue;
        }

        if (entry.directive_type === "no_op") {
            entry.applies = false;
            entry.structured_adjustment = null;
        } else {
            entry.applies = true;
            // Purify hours array to strictly 0-23 ascending integers
            if (entry.structured_adjustment && Array.isArray(entry.structured_adjustment.hours)) {
                entry.structured_adjustment.hours = [...new Set(entry.structured_adjustment.hours)]
                    .filter(h => Number.isInteger(h) && h >= 0 && h <= 23)
                    .sort((a, b) => a - b);
            }
        }
        validInterpretations.push(entry);
    }
    
    return validInterpretations;
};

// Add this at the bottom of services/guardrailValidator.js
exports.validateDirectives = exports.validateGuardrails;