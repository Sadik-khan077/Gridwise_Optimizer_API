# GridWise API - Smart Campus Energy Optimization
**Team:** JU_Retake_11

## Architecture Overview
This solution implements a robust, four-stage pipeline to optimize 24-hour campus energy scheduling while strictly adhering to operator directives:
1. **LLM Interpretation:** Parses natural-language operator notes using `openai/gpt-oss-20b` (via Groq for sub-second, JSON-enforced inference).
2. **Deterministic Guardrails:** Validates the LLM output to ensure safe, feasible constraint mapping. Time windows, numeric adjustments, and directive types are strictly sanitized. Unsafe or malformed directives safely fall back to `no_op`.
3. **Mathematical Optimization:** Uses `javascript-lp-solver` to formulate the 24-hour schedule as a Mixed-Integer Linear Programming (MILP) problem. It strictly enforces battery physics (charge/discharge rates, capacity, state-of-charge), solar curtailment, and end-of-day battery neutrality.
4. **Formatting:** Structures the solved MILP variables into the exact required JSON schema.

## Tech Stack & Dependencies
* **Backend:** Node.js, Express.js
* **LLM Provider:** Groq (`openai/gpt-oss-20b` model)
* **Optimization:** `javascript-lp-solver`
* **Validation/Routing:** Built-in JS guardrails

## Local Quickstart
**1. Clone and Install**
\`\`\`bash
git clone <repository-url>
cd gridwise-api
npm install
\`\`\`

**2. Environment Configuration**
Create a `.env` file in the root directory with the following keys:
\`\`\`env
PORT=3000
GROQ_API_KEY=your_groq_api_key_here
\`\`\`

**3. Run the Server**
\`\`\`bash
npm start
\`\`\`

## API Usage Examples
**Health Check**
\`\`\`bash
curl http://localhost:3000/health
\`\`\`

**Optimize Energy (Public Sample Test)**
\`\`\`bash
curl -X POST http://localhost:3000/optimize-energy \
-H "Content-Type: application/json" \
-d '{
  "scenario_id": "SAMPLE-01",
  "operator_notes": ["Do not charge the battery between 2 PM and 4 PM."],
  "battery": { "capacity_kwh": 500, "initial_energy_kwh": 200, "minimum_energy_kwh": 50, "max_charge_kwh_per_hour": 100, "max_discharge_kwh_per_hour": 100 },
  "hours": [
    {"hour": 0, "demand_kwh": 180, "solar_kwh": 0, "tariff_bdt_per_kwh": 7},
    {"hour": 1, "demand_kwh": 150, "solar_kwh": 0, "tariff_bdt_per_kwh": 7},
    {"hour": 23, "demand_kwh": 200, "solar_kwh": 0, "tariff_bdt_per_kwh": 7}
  ]
}'
\`\`\`

## Docker Fallback Execution
If local Node.js execution is unavailable, pull and run the containerized fallback image:
\`\`\`bash
docker pull yourdockerhubusername/gridwise-api:v1
docker run -p 3000:3000 --env-file .env yourdockerhubusername/gridwise-api:v1
\`\`\`

## Known Limitations
* The solver assumes discrete 1-hour time blocks; sub-hour constraints are not modeled.