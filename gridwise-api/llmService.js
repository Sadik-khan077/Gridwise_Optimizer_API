// llmService.js
const { OpenAI } = require('openai');

const groq = new OpenAI({
    apiKey: process.env.GROQ_API_KEY,
    baseURL: "https://api.groq.com/openai/v1"
});

async function interpretNotes(operator_notes) {
    const promptContext = `
    You are an energy optimization assistant. Map the following operator notes to their exact structured directives.
    
    Supported directive types:
    - "solar_reduction": requires factor (0 to 1) and hours array.
    - "minimum_battery_reserve": requires minimum_energy_kwh and hours array.
    - "no_charge_window": requires hours array.
    - "no_discharge_window": requires hours array.
    - "max_grid_window": requires max_grid_kwh and hours array.
    - "no_op": use for irrelevant notes. applies must be false, structured_adjustment must be null.

    IMPORTANT: "hours" must ALWAYS be an array of unique integers from 0 to 23.
    Time windows are start-inclusive and end-exclusive (e.g. 2 PM to 4 PM is [14, 15]).

    Operator Notes:
    ${operator_notes.map((note, index) => `[Index ${index}]:${note}`).join('\n')}
    
    Return a JSON object containing a "directives" array with one entry per note in note_index order:
    {
      "directives": [
        {
          "note_index": 0,
          "applies": true,
          "directive_type": "no_charge_window",
          "structured_adjustment": { "hours": [14, 15] },
          "explanation": "Battery charging disabled from 2 PM to 4 PM."
        }
      ]
    }
    `;

    const response = await groq.chat.completions.create({
        model: "openai/gpt-oss-20b",
        messages: [
            { role: "system", content: "You output strict JSON following the exact schema provided." },
            { role: "user", content: promptContext }
        ],
        response_format: { type: "json_object" }
    });

    const parsed = JSON.parse(response.choices[0].message.content);
    
    // Normalize return value whether model wrapped it in directives, directive_interpretation, or returned an array
    if (Array.isArray(parsed)) return parsed;
    if (Array.isArray(parsed.directives)) return parsed.directives;
    if (Array.isArray(parsed.directive_interpretation)) return parsed.directive_interpretation;
    return [];
}

module.exports = { interpretNotes };