// server.js
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const { validateRequest, enforceGuardrails } = require('./validator');
const { interpretNotes } = require('./llmService');
const { solveEnergyPlan } = require('./solver');

const app = express();
app.use(cors());
app.use(express.json());

// Serve React frontend (place your Vite 'dist' output in the 'public' folder)
app.use(express.static(path.join(__dirname, 'public')));

// Required Health Endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: "ok" });
});

// Main Optimization Endpoint
app.post('/optimize-energy', async (req, res) => {
    try {
        // 1. Validate incoming JSON structure
        const { scenario_id, operator_notes, hours, battery } = validateRequest(req.body);

        // 2. LLM Interpretation
        const rawDirectives = await interpretNotes(operator_notes);

        // 3. Deterministic Guardrails (Validate LLM Output)
        const validDirectives = enforceGuardrails(rawDirectives); 

        // 4. Math Optimization
        const plan = solveEnergyPlan(hours, battery, validDirectives);

        // 5. Final Response Formatting
        res.status(200).json({
            scenario_id,
            directive_interpretation: validDirectives,
            hourly_plan: plan.hourly_plan,
            total_grid_kwh: plan.total_grid_kwh,
            total_cost_bdt: plan.total_cost_bdt,
            peak_grid_kwh: plan.peak_grid_kwh,
            plan_summary: "Optimized 24-hour schedule applying LLM directives."
        });

    } catch (error) {
        console.error("Optimization Error:", error.message);
        res.status(400).json({ error: error.message }); 
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`GridWise API running on port ${PORT}`);
});