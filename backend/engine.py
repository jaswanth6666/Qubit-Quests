# Path: Qubic_Quests_Hackathon/backend/engine.py

import numpy as np
import time
import os
import logging

# Set up professional logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from qiskit_algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Estimator
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_ibm_provider import IBMProvider, IBMBackend
from qiskit_aer import AerSimulator
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer

def get_backend(backend_name: str):
    """
    Connects to and returns the requested backend (simulator or real hardware).
    This function is now robust and provides clear error messages.
    """
    logging.info(f"Attempting to get backend: '{backend_name}'")
    
    if backend_name == 'simulator':
        logging.info("SUCCESS: Selected Ideal Local Simulator.")
        return AerSimulator() # Use AerSimulator for ideal local simulation

    # All other options require connecting to IBM Quantum
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
        logging.error(f"CRITICAL: Failed to get backend '{backend_name}' from IBM. Error: {e}", exc_info=True)
        raise ConnectionError(f"Failed to get backend '{backend_name}'. It may be offline, you may not have access, or your token may be invalid.")

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    logging.info(f"--- VQE ENGINE STARTED ---")
    logging.info(f"Received: Molecule={molecule_name}, Bond Length={bond_length}, Backend='{backend_name}'")
    start_time = time.time()

    try:
        # Step 1: Get the backend. This will raise an error if it fails.
        backend = get_backend(backend_name)
        
        # Step 2: Define the molecule and the active space
        if molecule_name == "H2":
            atom_string = f"H 0 0 0; H 0 0 {bond_length}"
            # For H2, we simulate all 2 electrons in the 2 relevant orbitals
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
        elif molecule_name == "LiH":
            atom_string = f"Li 0 0 0; H 0 0 {bond_length}"
            # For LiH, we ONLY simulate the 2 valence electrons in 5 active orbitals
            # This is the key to making it work reliably.
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=5)
        else:
            raise ValueError("Unsupported molecule.")
        
        logging.info(f"Defined Active Space for {molecule_name}: {transformer.num_electrons} electrons in {transformer.num_spatial_orbitals} orbitals.")

        # Step 3: Set up and run the classical chemistry driver
        driver = PySCFDriver(atom=atom_string, basis=basis.lower())
        problem = driver.run()
        
        # Step 4: Apply the active space transformation to reduce the problem size
        problem = transformer.transform(problem)
        logging.info(f"Problem transformed. Qubits required will be based on {problem.num_spatial_orbitals} orbitals.")

        # Step 5: Map the problem to qubits
        mapper = JordanWignerMapper()
        qubit_op = mapper.map(problem.hamiltonian.second_q_op())
        
        # Step 6: Define the quantum components
        ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper))
        optimizer = COBYLA(maxiter=1000) # Increased max iterations for robustness
        
        # Step 7: Configure the Estimator for the chosen backend
        # This is a critical step that was missing before.
        # If it's a real backend, we pass it to the estimator.
        if isinstance(backend, (IBMBackend, AerSimulator)):
            estimator = Estimator(backend=backend)
        else: # Should not happen, but as a fallback
            estimator = Estimator()
        
        logging.info(f"Estimator configured for backend: {backend.name}")

        # Step 8: Run VQE
        logging.info("Starting VQE optimization...")
        convergence_history = []
        def callback(eval_count, parameters, mean, std): convergence_history.append(mean)
        
        vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
        
        # Step 9: Calculate the exact classical answer for comparison
        classical_solver = NumPyMinimumEigensolver()
        classical_result = classical_solver.compute_minimum_eigenvalue(qubit_op)
        
        # This is where the actual quantum (or simulated) calculation happens
        vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)
        
        logging.info("VQE optimization finished.")
        
        # Step 10: Combine quantum and classical results for the final energy
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
        logging.info(f"--- VQE Calculation Complete. Final Error: {error:.4f} mHa ---")
        return results

    except Exception as e:
        logging.error(f"CRITICAL ERROR in VQE Calculation: {e}", exc_info=True)
        # Re-raise the exception so FastAPI can catch it and report a 500 error
        raise e