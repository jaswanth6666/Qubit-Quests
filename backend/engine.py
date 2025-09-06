# Path: Qubic_Quests_Hackathon/backend/engine.py

import numpy as np
import time
import os
from qiskit_algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Estimator
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_ibm_provider import IBMProvider
from qiskit_aer import AerSimulator

# --- THIS IS THE NEW, PROFESSIONAL TOOL ---
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer

def get_ibm_provider():
    try:
        token = os.getenv('IBM_QUANTUM_TOKEN')
        if not token:
            print("CRITICAL: IBM_QUANTUM_TOKEN environment variable not set. Real hardware will not be available.")
            return None
        print("SUCCESS: Found IBM_QUANTUM_TOKEN. Attempting to connect to IBM Provider...")
        provider = IBMProvider(token=token, instance='ibm-q/open/main')
        print("SUCCESS: Connected to IBM Provider.")
        return provider
    except Exception as e:
        print(f"CRITICAL: Could not connect to IBM Provider: {e}")
        return None

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    print(f"--- VQE ENGINE STARTED (JordanWignerMapper) ---")
    print(f"Received: Molecule={molecule_name}, Bond Length={bond_length}, Backend='{backend_name}'")
    start_time = time.time()

    if backend_name == 'simulator':
        estimator = Estimator()
        print("ENGINE ACTION: Using IDEAL LOCAL SIMULATOR.")
    else:
        print(f"ENGINE ACTION: Attempting to use REAL HARDWARE backend: '{backend_name}'")
        provider = get_ibm_provider()
        if provider:
            try:
                backend = provider.get_backend(backend_name)
                estimator = Estimator(backend=backend)
                print(f"SUCCESS: Successfully connected to real backend: {backend_name}")
            except Exception as e:
                raise ConnectionError(f"ENGINE ERROR: Could not get backend '{backend_name}'. Error: {e}")
        else:
            raise ConnectionError("ENGINE ERROR: Could not connect to IBM Quantum.")

    if molecule_name == "H2":
        atom_string = f"H 0 0 0; H 0 0 {bond_length}"
        # For H2, we simulate all electrons and orbitals
        transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
    elif molecule_name == "LiH":
        atom_string = f"Li 0 0 0; H 0 0 {bond_length}"
        # For LiH, we FREEZE the core and simulate only the 2 valence electrons in 4 active orbitals
        transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=4)
    else:
        raise ValueError("Unsupported molecule.")

    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()

    # --- THIS IS THE CRUCIAL NEW STEP ---
    # We apply the transformer to reduce the problem size
    problem = transformer.transform(problem)

    mapper = JordanWignerMapper()
    qubit_op = mapper.map(problem.hamiltonian.second_q_op())
    
    # The ansatz is now built for the SMALLER, transformed problem
    ansatz = UCCSD(
        problem.num_spatial_orbitals,
        problem.num_particles,
        mapper,
        initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
    )
    
    optimizer = COBYLA(maxiter=200)
    convergence_history = []
    def callback(eval_count, parameters, mean, std):
        convergence_history.append(mean)
        
    vqe = VQE(estimator, ansatz, optimizer, callback=callback)
    result = vqe.compute_minimum_eigenvalue(operator=qubit_op)
    
    numpy_solver = NumPyMinimumEigensolver()
    exact_result = numpy_solver.compute_minimum_eigenvalue(qubit_op)
    
    # We must use the transformed problem's properties to get the right energy
    total_vqe_energy = result.eigenvalue.real + problem.nuclear_repulsion_energy
    total_exact_energy = exact_result.eigenvalue.real + problem.nuclear_repulsion_energy
    error = abs(total_vqe_energy - total_exact_energy) * 1000
    
    end_time = time.time()
    eval_count = len(convergence_history)
    
    results = {
        "energy": total_vqe_energy, "exact_energy": total_exact_energy, "convergence": convergence_history, "error_mHa": error,
        "diagnostics": {
            "qubits": qubit_op.num_qubits, "pauliTerms": len(qubit_op), "circuitDepth": ansatz.decompose().depth(), "evaluations": eval_count, "execution_time_sec": end_time - start_time
        }
    }
    print(f"--- VQE Calculation Complete in {results['diagnostics']['execution_time_sec']:.2f}s ---")
    return results