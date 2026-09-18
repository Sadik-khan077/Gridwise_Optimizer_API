# GridWise LLM - Smart Campus Energy Optimization

This is the backend service for the "GridWise — Smart Campus Energy Optimization Challenge" (BUP CSE Fest 2026). It receives a 24-hour campus energy scenario with natural-language operator notes, interprets those notes using an LLM, and schedules optimal battery usage using a linear programming model.

## Setup & Quickstart

1. Clone the repository and navigate to this directory.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set your environment variables (copy `.env.example` to `.env`):
   ```bash
   export LLM_API_KEY="your_api_key_here"
   export LLM_PROVIDER="gemini" # or "openai"
   export LLM_MODEL="gemini-2.0-flash" # or "gpt-4o-mini"
   export PORT="8000"
   ```
4. Run the API:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. Test the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
6. Run the public samples:
   ```bash
   pytest tests/test_public_cases.py -v
   ```

## Architecture

- **LLM Interpreter Path (Mandatory):** Natural language notes are parsed using Google Gemini (or OpenAI) with a rigid schema to extract one of 6 directive types.
- **Guardrails:** All LLM outputs pass through a deterministic guardrail validator to ensure schema consistency, proper hours formatting, and numeric bounds checking. If validation fails twice, a robust regex-based fallback extractor is used.
- **LP Solver:** Uses `scipy.optimize.linprog` with the `"highs"` method to minimize grid costs while respecting battery and directive limits.
- **Replay Validation:** Mirrors the judge's validation rules before returning the response.

## Docker

Build and run using Docker:
```bash
docker build -t gridwise-llm .
docker run -p 8000:8000 -e LLM_API_KEY="your_key" gridwise-llm
```

## Security Notice

- Never bake secrets (`LLM_API_KEY`) into Docker images.
- Use environment variables for sensitive configuration.
