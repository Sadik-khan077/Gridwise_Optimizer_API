import json
import asyncio
import logging
from typing import List, Dict
from app.config import settings
from app.interpreter.prompt import build_system_prompt, build_user_prompt
from app.interpreter.guardrails import validate_and_parse_llm_output
from app.interpreter.fallback import run_fallback_interpreter

logger = logging.getLogger("gridwise")

_cache: Dict[str, List[Dict]] = {}
_MAX_CACHE = 512

async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    if settings.LLM_PROVIDER == "openai":
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
        )
        return response.choices[0].message.content
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.LLM_API_KEY)
        response = await client.aio.models.generate_content(
            model=settings.LLM_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        return response.text

async def _call_llm_with_timeout(system_prompt: str, user_prompt: str) -> str:
    return await asyncio.wait_for(
        _call_llm(system_prompt, user_prompt), 
        timeout=settings.LLM_TIMEOUT_SECONDS
    )

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def interpret_notes(notes: List[str], capacity_kwh: float) -> List[Dict]:
    if not notes:
        return []
    
    cache_key = json.dumps({"notes": notes, "cap": capacity_kwh})
    if settings.LLM_CACHE_ENABLED and cache_key in _cache:
        return _cache[cache_key]
        
    system_prompt = build_system_prompt(capacity_kwh)
    user_prompt = build_user_prompt(notes)
    
    parsed = None
    try:
        raw_text = await _call_llm_with_timeout(system_prompt, user_prompt)
        raw_text = _clean_json(raw_text)
        raw_json = json.loads(raw_text)
        
        valid, err, parsed = validate_and_parse_llm_output(raw_json, notes, capacity_kwh)
        
        if not valid:
            logger.warning(f"LLM validation failed: {err}. Retrying...")
            retry_prompt = f"{user_prompt}\n\nYour previous output failed validation: {err}. Return a corrected JSON array."
            raw_text = await _call_llm_with_timeout(system_prompt, retry_prompt)
            raw_text = _clean_json(raw_text)
            raw_json = json.loads(raw_text)
            
            valid, err, parsed = validate_and_parse_llm_output(raw_json, notes, capacity_kwh)
            
            if not valid:
                logger.warning(f"LLM validation failed twice: {err}. Using fallback.")
                parsed = run_fallback_interpreter(notes, capacity_kwh)
    except asyncio.TimeoutError:
        logger.error("LLM timeout. Using fallback.")
        parsed = run_fallback_interpreter(notes, capacity_kwh)
    except Exception as e:
        logger.error(f"LLM exception: {e}. Using fallback.")
        parsed = run_fallback_interpreter(notes, capacity_kwh)
        
    valid, err, final_parsed = validate_and_parse_llm_output(parsed, notes, capacity_kwh)
    if not valid:
        logger.error(f"Fallback validation failed: {err}. Using all no_op.")
        final_parsed = [{
            "note_index": i,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "Ultimate fallback"
        } for i in range(len(notes))]
        
    if settings.LLM_CACHE_ENABLED:
        if len(_cache) >= _MAX_CACHE:
            _cache.pop(next(iter(_cache)))
        _cache[cache_key] = final_parsed
        
    return final_parsed
