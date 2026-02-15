"""
Aider Service
FastAPI wrapper for Aider to allow direct control via HTTP.
"""
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import StreamingResponse

from aider_runner import AiderRunner

app = FastAPI(title="LUMA Aider Service")
aider_runner = AiderRunner()

class FixRequest(BaseModel):
    instruction: str
    target_file: Optional[str] = None

@app.post("/fix")
async def fix_code(request: FixRequest):
    """
    Auto-fix code using Aider.
    Returns a streaming response of the Aider output.
    """
    print(f"🔧 Fix request received: {request.instruction} (Target: {request.target_file})")
    
    async def output_generator():
        try:
            yield f"🚀 Aider started for: {request.instruction}\n"
            
            async for line in aider_runner.run_stream(
                target_file=request.target_file,
                instruction=request.instruction
            ):
                yield f"{line}\n"
                
            yield "✅ Aider finished.\n"
            
        except Exception as e:
            yield f"❌ Error: {str(e)}\n"

    return StreamingResponse(output_generator(), media_type="text/plain")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "luma-aider-service"}

