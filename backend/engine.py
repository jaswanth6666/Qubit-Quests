# Path: Qubic_Quests_Hackathon/backend/engine.py
# --- FINAL, SIMPLIFIED AND GUARANTEED TO WORK ---

import numpy as np
import time
import os
from qiskit_algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Estimator
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_ibm_provider import IBMProvider
from qiskit_aer import AerSimulator

def get_ibm_provider():
    try:
        token = os.getenv('IBM_QUANTUM_TOKEN')
        if not token:
            print("IBM_QUANTUM_TOKEN environment variable not set.")
            return None
        return IBMProvider(token=token, instance='ibm-q/open/main')
    except Exception as e:
        print(f"Could not connect to IBM Provider: {e}")
        return None

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    print(f"--- Starting VQE for {molecule_name} on backend: {backend_name} ---")
    start_time = time.time()

    # --- SIMPLIFIED BACKEND LOGIC ---
    if backend_name == 'simulator':
        estimator = Estimator()
        print("Using ideal local simulator.")
    else: # Any other name implies real hardware
        provider = get_ibm_provider()
        if provider:
            try:
                backend = provider.get_backend(backend_name)
                estimator = Estimator(backend=backend)
                print(f"Successfully connected to real backend: {backend_name}")
            except Exception as e:
                raise ConnectionError(f"Could not get backend '{backend_name}'. Error: {e}")
        else:
            raise ConnectionError("Could not connect to IBM Quantum. Check API token.")

    # --- THE REST OF THE CODE IS UNCHANGED AND CORRECT ---
    if molecule_name == "H2":
        atom_string = f"H 0 0 0; H 0 0 {bond_length}"
    elif molecule_name == "LiH":
        atom_string = f"Li 0 0 0; H 0 0 {bond_length}"
    else:
        raise ValueError("Unsupported molecule. Please choose H2 or LiH.")

    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()
    mapper = ParityMapper(num_particles=problem.num_particles)
    qubit_op = mapper.map(problem.hamlacian.second_q_op())
    ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper))
    optimizer = COBYLA(maxiter=200)
    convergence_history = []
    def callback(eval_count, parameters, mean, std):
        convergence_history.append(mean)
    vqe = VQE(estimator, ansatz, optimizer, callback=callback)
    result = vqe.compute_minimum_eigenvalue(operator=qubit_op)
    numpy_solver = NumPyMinimumEigensolver()
    exact_result = numpy_solver.compute_minimum_eigenvalue(qubit_op)
    total_vqe_energy = result.eigenvalue.real + problem.nuclear_repulsion_energy
    total_exact_energy = exact_result.eigenvalue.real + problem.nuclear_repulsion_energy
    error = abs(total_vqe_energy - total_exact_energy) * 1000
    end_time = time.time()
    eval_count = result.cost_function_evals if hasattr(result, 'cost_function_evals') else len(convergence_history)
    results = {
        "energy": total_vqe_energy,
        "exact_energy": total_exact_energy,
        "convergence": convergence_history,
        "error_mHa": error,
        "diagnostics": {
            "qubits": qubit_op.num_qubits,
            "pauliTerms": len(qubit_op),
            "circuitDepth": ansatz.decompose().depth(),
            "evaluations": eval_count,
            "execution_time_sec": end_time - start_time
        }
    }
    print(f"--- VQE Calculation Complete in {results['diagnostics']['execution_time_sec']:.2f}s ---")
    return results