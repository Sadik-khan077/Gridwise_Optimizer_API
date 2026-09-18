from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.schemas import ScenarioRequest, OptimizeResponse
from app.request_validator import validate_scenario

app = FastAPI(title="GridWise LLM")
logger = logging.getLogger("gridwise")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log safely
    logger.warning("Request validation error")
    return JSONResponse(
        status_code=400,
        content={"error": "invalid_request"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from app.interpreter.llm_client import interpret_notes
from app.optimizer.lp import solve_lp_with_recovery
from app.optimizer.postprocess import postprocess_plan
from app.validator.replay import run_replay_validator
from app.response_builder import build_response

@app.post("/optimize-energy", response_model=OptimizeResponse)
async def optimize_energy(req: ScenarioRequest):
    validate_scenario(req)
    
    directives = await interpret_notes(req.operator_notes, req.battery.capacity_kwh)
    
    success, x = solve_lp_with_recovery(req, directives)
    if not success:
        logger.error("LP solve failed completely")
        raise Exception("LP solve failed completely")
        
    plan = postprocess_plan(req, x, directives)
    
    valid, failures = run_replay_validator(req, directives, plan)
    if not valid:
        logger.warning(f"Replay validation failures: {failures}")
        
    return build_response(req, directives, plan)
