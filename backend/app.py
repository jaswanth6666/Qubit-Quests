# Path: Qubic_Quests_Hackathon/backend/app.py
# --- FINAL, MASTER, FASTAPI-NATIVE VERSION ---

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import numpy as np
import json
from pydantic import BaseModel

app = FastAPI()

# Configure CORS "guest list"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Qubic Quests Quantum Backend is running."}

# --- Pydantic models for request validation ---
class VqeRequest(BaseModel):
    molecule: str
    bondLength: float
    basis: str
    backend: str

class DissociationRequest(BaseModel):
    molecule: str
    basis: str

# Function to run blocking code in a thread pool
def run_in_threadpool(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args, **kwargs)

@app.post("/api/run-vqe")
async def vqe_endpoint(request: VqeRequest):
    try:
        from engine import run_vqe_calculation
        print(f"SERVER: Received VQE request: {request.dict()}")
        results = await run_in_threadpool(
            run_vqe_calculation, request.molecule, request.bondLength, request.basis, request.backend
        )
        return results
    except Exception as e:
        print(f"SERVER ERROR in /run-vqe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Real-time progress streaming setup ---
progress_queue = asyncio.Queue()

async def progress_streamer():
    while True:
        try:
            progress_data = await progress_queue.get()
            if progress_data is None: break
            yield json.dumps(progress_data)
        except asyncio.CancelledError:
            break

@app.get("/stream")
async def stream_endpoint(request: Request):
    return EventSourceResponse(progress_streamer())

def dissociation_calculation_thread(molecule: str, basis: str):
    from engine import run_vqe_calculation
    print(f"SERVER: Starting Dissociation Curve calculation...")
    bond_lengths = np.linspace(0.4, 2.5, 15)
    curve_data = []
    total_points = len(bond_lengths)
    for i, length in enumerate(bond_lengths):
        print(f"SERVER: Calculating curve point {i+1}/{total_points}...")
        result = run_vqe_calculation(molecule, round(length, 4), basis, 'simulator')
        curve_data.append({"bond_length": length, "energy": result['energy']})
        asyncio.run(progress_queue.put({"progress": ((i + 1) / total_points) * 100}))
    
    asyncio.run(progress_queue.put(None))
    app.state.dissociation_result = {"curve_data": curve_data}
    print("SERVER: Dissociation curve calculation complete.")

@app.post("/api/dissociation-curve")
async def dissociation_endpoint(request: DissociationRequest):
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, dissociation_calculation_thread, request.molecule, request.basis)
    return {"message": "Dissociation curve calculation started."}

@app.get("/api/dissociation-results")
async def get_dissociation_results():
    return getattr(app.state, "dissociation_result", {"curve_data": []})