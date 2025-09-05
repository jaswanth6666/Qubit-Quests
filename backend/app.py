# Path: Qubic_Quests_Hackathon/backend/app.py

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import numpy as np
import json
from pydantic import BaseModel

# Import your quantum engine function
from engine import run_vqe_calculation

# Define data models for request validation (a professional FastAPI feature)
class VqeRequest(BaseModel):
    molecule: str
    bondLength: float
    basis: str
    backend: str

class DissociationRequest(BaseModel):
    molecule: str
    basis: str

app = FastAPI()

# Configure CORS "guest list"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://qubit-quests-one.vercel.app",
        "https://qubit-quests.vercel.app",
        "https://qubit-quests-git-main-jaswanthkarri0111-gmailcoms-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is the modern way to run slow, blocking code (like Qiskit) in an async app
def run_in_threadpool(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args, **kwargs)

@app.post("/api/run-vqe")
async def vqe_endpoint(request: VqeRequest):
    try:
        print(f"SERVER: Received VQE request: {request.dict()}")
        results = await run_in_threadpool(
            run_vqe_calculation,
            request.molecule, 
            request.bondLength, 
            request.basis,
            request.backend
        )
        return results
    except Exception as e:
        print(f"SERVER ERROR in /run-vqe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# This is the new, more complex but powerful way to do real-time streaming
progress_queue = asyncio.Queue()

async def progress_streamer():
    """Yields progress updates as they are put into the queue."""
    while True:
        try:
            progress_data = await progress_queue.get()
            if progress_data is None: # A signal to end the stream
                break
            yield json.dumps(progress_data)
        except asyncio.CancelledError:
            break

@app.get("/stream")
async def stream_endpoint(request: Request):
    return EventSourceResponse(progress_streamer())

def dissociation_calculation_thread(molecule: str, basis: str):
    """This function runs in a separate thread to not block the server."""
    from engine import run_vqe_calculation # Lazy load in the thread
    print(f"SERVER: Starting Dissociation Curve calculation...")
    bond_lengths = np.linspace(0.4, 2.5, 15)
    curve_data = []
    total_points = len(bond_lengths)
    for i, length in enumerate(bond_lengths):
        print(f"SERVER: Calculating curve point {i+1}/{total_points}...")
        result = run_vqe_calculation(molecule, round(length, 4), basis, 'simulator')
        curve_data.append({"bond_length": length, "energy": result['energy']})
        
        # Put the progress update into the async queue from this thread
        progress = ((i + 1) / total_points) * 100
        asyncio.run(progress_queue.put({"progress": progress}))
    
    # Signal the end of the stream and store the final result
    asyncio.run(progress_queue.put(None)) 
    app.state.dissociation_result = {"curve_data": curve_data}
    print("SERVER: Dissociation curve calculation complete.")

@app.post("/api/dissociation-curve")
async def dissociation_endpoint(request: DissociationRequest):
    # This endpoint now starts the calculation in the background and returns immediately
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, dissociation_calculation_thread, request.molecule, request.basis)
    return {"message": "Dissociation curve calculation started. See /stream for progress."}

@app.get("/api/dissociation-results")
async def get_dissociation_results():
    # A new endpoint to fetch the final curve data once the stream is complete
    return getattr(app.state, "dissociation_result", {"curve_data": []})