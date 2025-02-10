import subprocess

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from .dto.command_dto import KubernetesCommand

app = FastAPI(
    title="K8s Agent",
    description="K8s Agent",
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}


"""
Routes that receives a kubernetes command and executes it and send the output for the command
"""
@app.post('/command')
def command(data: KubernetesCommand):
    command = data.command
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return PlainTextResponse(result.stdout)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing command: {e.stderr}"
        ) from e

def start():
    """Start the Uvicorn server to run the FastAPI application."""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="critical",
    )
