const { interpretNotes } = require('../services/llmInterpreter');
// Change this line:
// const { validateDirectives } = require('../services/guardrailValidator');

// To this:
const { validateGuardrails: validateDirectives } = require('../services/guardrailValidator');
const { runOptimization } = require('../services/mathOptimizer');
const logger = require('../utils/logger');

exports.optimizeEnergy = async (req, res, next) => {
  try {
    const { scenario_id, operator_notes, hours, battery } = req.body;
    
    // 1. LLM Interpretation: Convert raw natural language strings into structured directives
    const rawInterpretations = await interpretNotes(operator_notes);
    
    // 2. Deterministic Guardrails: Validate types, array ranges, index order, and bounds
    const validInterpretations = validateDirectives(rawInterpretations, operator_notes.length);
    
    // 3. Math Optimization: Execute linear programming solver against adjusted constraints
    const optimizationResult = runOptimization(hours, battery, validInterpretations);
    
    // 4. Return the complete, canonical schema required by the hackathon spec
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
    logger.error(`Optimization pipeline error: ${error.message}`);
    next(error);
  }
};