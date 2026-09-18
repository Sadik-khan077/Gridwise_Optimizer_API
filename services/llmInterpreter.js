const { GoogleGenAI } = require('@google/genai');

exports.interpretNotes = async (operator_notes) => {
    // Moved inside the function so it reads the key AFTER the server is fully running
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

    const prompt = `
    You are an energy system expert. Analyze the following operator notes and extract deterministic directives for an energy optimizer.
    For each note, return exactly ONE JSON object mapping.
    
    Supported directive types: "solar_reduction", "minimum_battery_reserve", "no_charge_window", "no_discharge_window", "max_grid_window", "no_op"
    - "no_op" must use applies = false and structured_adjustment = null.
    - All other directives must use applies = true.
    - "hours" must be an array of unique integers from 0 to 23 in ascending order.
    - "solar_reduction" needs {"hours": [...], "factor": number} where factor is the usable fraction remaining.
    - "minimum_battery_reserve" needs {"hours": [...], "minimum_energy_kwh": number}
    - "no_charge_window" needs {"hours": [...]}
    - "no_discharge_window" needs {"hours": [...]}
    - "max_grid_window" needs {"hours": [...], "max_grid_kwh": number}
    
    Notes to interpret:
    ${operator_notes.map((n, i) => `Note ${i}: "${n}"`).join('\n')}
    
    Return a valid JSON array of objects strictly following this shape:
    [
      {
        "note_index": 0,
        "applies": boolean,
        "directive_type": string,
        "structured_adjustment": object or null,
        "explanation": string
      }
    ]
    `;

    try {
        const response = await ai.models.generateContent({
            model: 'gemini-3.6-flash',
            contents: prompt,
            config: { responseMimeType: 'application/json' }
        });
        
        return JSON.parse(response.text);
    } catch (error) {
        throw new Error(`LLM generation error: ${error.message}`);
    }
};