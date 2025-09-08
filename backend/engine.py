import numpy as np
import time
import os
import logging
from scipy.optimize import minimize

from qiskit_ibm_provider import IBMProvider
from qiskit_aer import AerSimulator
from qiskit.primitives import Estimator
from qiskit_nature.algorithms import VQE
from qiskit_nature.algorithms.ground_state_solvers import NumPyMinimumEigensolver
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_backend(backend_name: str):
    logging.info(f"Attempting to get backend: '{backend_name}'")
    if backend_name == 'simulator':
        logging.info("Using local AerSimulator for fast computation.")
        return AerSimulator()
    token = os.getenv('IBM_QUANTUM_TOKEN')
    if not token:
        raise ConnectionError("IBM_QUANTUM_TOKEN environment variable not set.")
    provider = IBMProvider(token=token, instance='ibm-q/open/main')
    backend = provider.get_backend(backend_name)
    logging.info(f"Connected to IBM backend '{backend_name}'.")
    return backend

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    logging.info(f"VQE calculation for {molecule_name} at bond length {bond_length} Å")
    start_time = time.time()

    try:
        backend = get_backend(backend_name)

        molecule_geometries = {
            "H2": f"H 0 0 0; H 0 0 {bond_length}",
            "LiH": f"Li 0 0 0; H 0 0 {bond_length}",
            "H2O": f"O 0 0 0; H 0.758602 0.504284 {bond_length}; H -0.758602 0.504284 {bond_length}",
            "HF": f"H 0 0 0; F 0 0 {bond_length}",
            "LiF": f"Li 0 0 0; F 0 0 {bond_length}",
            "BeH2": f"Be 0 0 0; H 0 0 {bond_length}; H 0 0 {-bond_length}",
            "NH3": f"N 0 0 0; H 0.9377 0.3816 {bond_length}; H -0.9377 0.3816 {bond_length}; H 0 -0.7633 {bond_length}"
        }

        if molecule_name not in molecule_geometries:
            raise ValueError(f"Unsupported molecule: {molecule_name}")

        atom_string = molecule_geometries[molecule_name]

        # Set appropriate active space per molecule
        if molecule_name in ["H2", "LiH"]:
            transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
        else:
            transformer = ActiveSpaceTransformer(num_electrons=8, num_spatial_orbitals=4)

        driver = PySCFDriver(atom=atom_string, basis=basis.lower())
        problem = driver.run()
        problem = transformer.transform(problem)

        mapper = JordanWignerMapper()
        qubit_op = mapper.map(problem.hamiltonian.second_q_op())

        initial_state = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
        ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=initial_state)

        convergence_history = []
        def callback(eval_count, parameters, mean, std):
            convergence_history.append(mean)

        estimator = Estimator()

        vqe_solver = VQE(estimator=estimator, ansatz=ansatz, optimizer='L_BFGS_B', callback=callback)

        vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)

        classical_solver = NumPyMinimumEigensolver()
        classical_result = classical_solver.compute_minimum_eigenvalue(qubit_op)

        total_vqe_energy = vqe_result.eigenvalue.real + problem.nuclear_repulsion_energy
        total_exact_energy = classical_result.eigenvalue.real + problem.nuclear_repulsion_energy
        error_mHa = abs(total_vqe_energy - total_exact_energy) * 1000
        end_time = time.time()

        results = {
            "bond_length": bond_length,
            "energy": total_vqe_energy,
            "exact_energy": total_exact_energy,
            "error_mHa": error_mHa,
            "convergence": convergence_history,
            "diagnostics": {
                "qubits": qubit_op.num_qubits,
                "pauli_terms": len(qubit_op),
                "circuit_depth": ansatz.decompose().depth(),
                "evaluations": len(convergence_history),
                "execution_time_sec": end_time - start_time
            }
        }

        logging.info(f"Calculation complete. Energy: {total_vqe_energy:.6f}, Error: {error_mHa:.4f} mHa")

        return results

    except Exception as e:
        logging.error(f"Error during VQE calculation: {e}", exc_info=True)
        raise e
