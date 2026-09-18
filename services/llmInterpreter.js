const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

exports.interpretNotes = async (operator_notes) => {
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

    const maxRetries = 3;
    let attempt = 0;

    while (attempt < maxRetries) {
        try {
            attempt++;
            const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
                    'HTTP-Referer': 'http://localhost:3000',
                    'X-Title': 'GridWise Optimizer',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: 'openai/gpt-4o',
                    response_format: { type: 'json_object' },
                    messages: [
                        {
                            role: 'system',
                            content: 'You are a precise data extraction engine. Always respond with valid JSON containing the requested array structure.'
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                }),
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`OpenRouter API error (status ${response.status}): ${errText}`);
            }

            const data = await response.json();
            const content = data.choices[0].message.content;
            
            // Clean markdown block wrappers if the model accidentally includes them
            const cleanedContent = content.replace(/```json/g, '').replace(/```/g, '').trim();
            const parsed = JSON.parse(cleanedContent);

            // Handle cases where the model wraps the array inside an object key
            if (Array.isArray(parsed)) {
                return parsed;
            } else if (typeof parsed === 'object' && parsed !== null) {
                const key = Object.keys(parsed).find(k => Array.isArray(parsed[k]));
                if (key) return parsed[key];
            }
            
            return parsed;

        } catch (error) {
            console.warn(`[Attempt ${attempt}] OpenRouter interpretation failed: ${error.message}`);
            
            if (attempt < maxRetries) {
                console.log(`Retrying in ${attempt * 2} seconds...`);
                await sleep(attempt * 2000);
            } else {
                // Hackathon fallback safety: return safe no_op array if LLM completely fails
                console.warn("[WARNING] OpenRouter unavailable after retries. Falling back to default no_op directives.");
                return operator_notes.map((_, i) => ({
                    note_index: i,
                    applies: false,
                    directive_type: "no_op",
                    structured_adjustment: null,
                    explanation: "Fallback due to LLM provider unavailability."
                }));
            }
        }
    }
};