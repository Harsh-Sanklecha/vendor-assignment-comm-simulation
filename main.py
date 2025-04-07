from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
from typing import List, Dict, Any, Optional
from vendor_agent import VendorAgent
from pydantic import BaseModel

app = FastAPI(title="Vendor Assignment & Communication AI Agent")

class Task(BaseModel):
    task_description: str
    category: str = None
    urgency: str
    special_requirements: str = None

# Endpoints
@app.post("/process-task/")
async def process_task_endpoint(task: Task):
    """Process a task and get vendor assignment with communication."""
    try:
        vendor_agent = VendorAgent()
        result = vendor_agent.run_workflow(task.model_dump())
        return result
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)