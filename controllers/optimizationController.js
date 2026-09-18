const { interpretNotes } = require('../services/llmInterpreter');
const { validateGuardrails } = require('../services/guardrailValidator');
const { runOptimization } = require('../services/mathOptimizer');
const logger = require('../utils/logger');

exports.optimizeEnergy = async (req, res, next) => {
    try {
        const { scenario_id, operator_notes, hours, battery } = req.body;
        
        // 1. LLM Interpretation (Untrusted string -> JSON mapping)
        const rawInterpretations = await interpretNotes(operator_notes);
        
        // 2. Deterministic Guardrails (Validate mapping against math rules)
        const validInterpretations = validateGuardrails(rawInterpretations, operator_notes);
        
        // 3. Math Optimization (javascript-lp-solver executes linear constraints)
        const optimizationResult = runOptimization(hours, battery, validInterpretations);
        
        // 4. Return canonical JSON schema
        res.status(200).json({
            scenario_id,
            directive_interpretation: validInterpretations,
            hourly_plan: optimizationResult.hourly_plan,
            total_grid_kwh: optimizationResult.total_grid_kwh,
            total_cost_bdt: optimizationResult.total_cost_bdt,
            peak_grid_kwh: optimizationResult.peak_grid_kwh,
            plan_summary: optimizationResult.plan_summary
        });
    } catch (error) {
        logger.error(`Optimization failed: ${error.message}`);
        next(error);
    }
};