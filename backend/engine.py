# Path: Qubic_Quests_Hackathon/backend/engine.py
# --- MASTER BLUEPRINT - THESIS GRADE ---

import numpy as np
import time
import os
import logging

# Set up professional logging to see the process, just like in a real experiment
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Core Qiskit and scientific libraries
from qiskit_algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Estimator
from qiskit_ibm_provider import IBMProvider, IBMBackend
from qiskit_aer import AerSimulator

# Qiskit Nature imports, as described in the thesis
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer

def get_backend(backend_name: str):
    """
    Connects to and returns the requested backend (simulator or real hardware).
    This function handles the crucial connection to the quantum computation resource.
    """
    logging.info(f"Attempting to get backend: '{backend_name}'")
    
    if backend_name == 'simulator':
        logging.info("SUCCESS: Selected Ideal Local Simulator (AerSimulator).")
        # An ideal, noise-free simulator for fast, accurate results.
        return AerSimulator()

    # For all other backends, we connect to the cloud.
    token = os.getenv('IBM_QUANTUM_TOKEN')
    if not token:
        raise ConnectionError("CRITICAL: IBM_QUANTUM_TOKEN environment variable not set. Cannot access any IBM backends.")
    
    try:
        logging.info("SUCCESS: Found IBM_QUANTUM_TOKEN. Connecting to IBM Provider...")
        provider = IBMProvider(token=token, instance='ibm-q/open/main')
        logging.info("SUCCESS: Connected to IBM Provider.")
        backend = provider.get_backend(backend_name)
        logging.info(f"SUCCESS: Successfully retrieved backend '{backend_name}' from IBM provider.")
        return backend
    except Exception as e:
        logging.error(f"CRITICAL: Failed to get backend '{backend_name}'. Error: {e}", exc_info=True)
        raise ConnectionError(f"Failed to get backend '{backend_name}'. It may be offline, you may not have access, or your token may be invalid.")

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    """
    Executes the full VQE protocol, mirroring the steps outlined in the provided thesis.
    """
    logging.info(f"--- VQE PROTOCOL STARTED ---")
    logging.info(f"Parameters: Molecule={molecule_name}, Bond Length={bond_length}, Backend='{backend_name}'")
    start_time = time.time()

    try:
        # THESIS STEP 1: DEFINE THE MOLECULAR HAMILTONIAN (Chapter 2 & 3.2.1)
        # We start by defining the physical system.
        backend = get_backend(backend_name)
        
        if molecule_name == "H2":
            atom_string = f"H 0 0 0; H 0 0 {bond_length}"
            # For H2, the active space includes all 2 electrons and 2 orbitals.
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
        elif molecule_name == "LiH":
            atom_string = f"Li 0 0 0; H 0 0 {bond_length}"
            # For LiH, we use a professional technique: we freeze the core electrons
            # and only simulate the 2 chemically active electrons in 5 active orbitals.
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=5)
        else:
            raise ValueError("Unsupported molecule.")
        
        logging.info(f"Defined Active Space for {molecule_name}: {transformer._num_electrons} electrons in {transformer._num_spatial_orbitals} orbitals.")

        driver = PySCFDriver(atom=atom_string, basis=basis.lower())
        problem = driver.run()
        
        # This crucial step reduces the problem size for LiH, making it solvable.
        problem = transformer.transform(problem)
        logging.info(f"Problem transformed. Qubits required will be based on {problem.num_spatial_orbitals} orbitals.")

        # THESIS STEP 2: MAPPING TO THE QUANTUM COMPUTER (Section 2.3)
        # Convert the chemical problem into the language of qubits.
        mapper = JordanWignerMapper()
        qubit_op = mapper.map(problem.hamiltonian.second_q_op())
        
        # THESIS STEP 3: CONSTRUCTING A VARIATIONAL ANSATZ (Section 3.2.2)
        # UCCSD is the Qiskit equivalent of the chemically-accurate ansatz in the thesis.
        ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper))
        
        # THESIS STEP 4: OPTIMIZING THE PARAMETERS (Section 3.2.3)
        # We define the classical optimizer and the quantum estimator.
        optimizer = COBYLA(maxiter=1000)
        
        # The modern, professional way to run jobs in Qiskit.
        # This correctly handles both local simulators and real cloud backends.
        estimator = Estimator(backend=backend)
        logging.info(f"Estimator configured for backend: {backend.name}")
        
        logging.info("Starting VQE optimization...")
        convergence_history = []
        def callback(eval_count, parameters, mean, std): convergence_history.append(mean)
        
        vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
        
        # For comparison, we solve the problem exactly with a classical algorithm.
        classical_solver = NumPyMinimumEigensolver()
        classical_result = classical_solver.compute_minimum_eigenvalue(qubit_op)
        
        # This is the line where the actual quantum (or simulated) calculation is executed.
        vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)
        logging.info("VQE optimization finished.")
        
        # THESIS STEP 5: FINAL RESULTS (Section 3.3.2)
        # Combine the quantum electronic energy with the classical nuclear repulsion energy.
        total_vqe_energy = vqe_result.eigenvalue.real + problem.nuclear_repulsion_energy
        total_exact_energy = classical_result.eigenvalue.real + problem.nuclear_repulsion_energy
        error = abs(total_vqe_energy - total_exact_energy) * 1000
        
        end_time = time.time()
        
        results = {
            "energy": total_vqe_energy, "exact_energy": total_exact_energy, "convergence": convergence_history, "error_mHa": error,
            "diagnostics": {
                "qubits": qubit_op.num_qubits, "pauliTerms": len(qubit_op), "circuitDepth": ansatz.decompose().depth(), "evaluations": len(convergence_history), "execution_time_sec": end_time - start_time
            }
        }
        logging.info(f"--- VQE PROTOCOL COMPLETE. Final Error: {error:.4f} mHa ---")
        return results

    except Exception as e:
        logging.error(f"CRITICAL ERROR in VQE Calculation: {e}", exc_info=True)
        raise e