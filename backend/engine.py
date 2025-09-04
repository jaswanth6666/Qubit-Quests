# Path: Qubic_Quests_Hackathon/backend/engine.py
# --- FINAL CORRECTED VERSION ---

import numpy as np
import time
from qiskit_algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Estimator
from qiskit_nature.second_q.drivers import PySCFDriver
# CORRECTED IMPORT: QubitConverter is no longer needed
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str):
    print(f"--- Starting VQE for {molecule_name} at {bond_length} Å ---")
    start_time = time.time()

    if molecule_name == "H2":
        atom_string = f"H 0 0 0; H 0 0 {bond_length}"
    elif molecule_name == "LiH":
        atom_string = f"Li 0 0 0; H 0 0 {bond_length}"
    else:
        raise ValueError("Unsupported molecule. Please choose H2 or LiH.")

    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()

    # STAGE II: TRANSFORMATION (Corrected)
    # The ParityMapper now directly handles the conversion.
    mapper = ParityMapper(num_particles=problem.num_particles)
    # We call the .map() method on the mapper itself. No QubitConverter needed.
    qubit_op = mapper.map(problem.hamiltonian.second_q_op())

    # The rest of the code is correct and does not need to change
    ansatz = UCCSD(
        problem.num_spatial_orbitals,
        problem.num_particles,
        mapper,
        initial_state=HartreeFock(
            problem.num_spatial_orbitals,
            problem.num_particles,
            mapper,
        ),
    )
    optimizer = COBYLA(maxiter=200)
    estimator = Estimator()

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
        "molecule": molecule_name,
        "bond_length": bond_length,
        "energy": total_vqe_energy,
        "exact_energy": total_exact_energy,
        "error_mHa": error,
        "convergence": convergence_history,
        "diagnostics": {
            "qubits": qubit_op.num_qubits,
            "pauliTerms": len(qubit_op),
            "evaluations": eval_count,
            "circuitDepth": ansatz.decompose().depth(),
            "execution_time_sec": end_time - start_time
        }
    }
    
    print(f"--- VQE Calculation Complete in {results['diagnostics']['execution_time_sec']:.2f}s ---")
    return results