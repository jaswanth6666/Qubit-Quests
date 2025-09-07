# Path: Qubic_Quests_Hackathon/backend/engine.py
# --- FINAL, CORRECTED MASTER VERSION ---

import numpy as np
import time
import os
import logging

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
    logging.info(f"Attempting to get backend: '{backend_name}'")
    if backend_name == 'simulator':
        logging.info("SUCCESS: Selected Ideal Local Simulator.")
        return AerSimulator()
    token = os.getenv('IBM_QUANTUM_TOKEN')
    if not token:
        raise ConnectionError("CRITICAL: IBM_QUANTUM_TOKEN environment variable not set.")
    try:
        logging.info("SUCCESS: Found IBM_QUANTUM_TOKEN. Connecting...")
        provider = IBMProvider(token=token, instance='ibm-q/open/main')
        logging.info("SUCCESS: Connected to IBM Provider.")
        backend = provider.get_backend(backend_name)
        logging.info(f"SUCCESS: Retrieved backend '{backend_name}'.")
        return backend
    except Exception as e:
        logging.error(f"CRITICAL: Failed to get backend '{backend_name}'. Error: {e}", exc_info=True)
        raise ConnectionError(f"Failed to get backend '{backend_name}'.")

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    logging.info(f"--- VQE ENGINE STARTED ---")
    logging.info(f"Received: Molecule={molecule_name}, Bond Length={bond_length}, Backend='{backend_name}'")
    start_time = time.time()
    try:
        backend = get_backend(backend_name)
        if molecule_name == "H2":
            atom_string = f"H 0 0 0; H 0 0 {bond_length}"
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
        elif molecule_name == "LiH":
            atom_string = f"Li 0 0 0; H 0 0 {bond_length}"
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=5)
        else:
            raise ValueError("Unsupported molecule.")
        
        # --- THIS IS THE CORRECTED LINE ---
        logging.info(f"Defined Active Space for {molecule_name}: {transformer._num_electrons} electrons in {transformer._num_spatial_orbitals} orbitals.")

        driver = PySCFDriver(atom=atom_string, basis=basis.lower())
        problem = driver.run()
        problem = transformer.transform(problem)
        
        logging.info(f"Problem transformed. Qubits required will be based on {problem.num_spatial_orbitals} orbitals.")

        mapper = JordanWignerMapper()
        qubit_op = mapper.map(problem.hamiltonian.second_q_op())
        
        ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper))
        optimizer = COBYLA(maxiter=1000)
        
        if isinstance(backend, (IBMBackend, AerSimulator)):
            estimator = Estimator(backend=backend)
        else:
            estimator = Estimator()
        
        logging.info(f"Estimator configured for backend: {backend.name}")

        logging.info("Starting VQE optimization...")
        convergence_history = []
        def callback(eval_count, parameters, mean, std): convergence_history.append(mean)
        vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
        classical_solver = NumPyMinimumEigensolver()
        classical_result = classical_solver.compute_minimum_eigenvalue(qubit_op)
        vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)
        logging.info("VQE optimization finished.")
        
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
        raise e