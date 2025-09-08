import numpy as np
import time
import os
import logging

from qiskit_ibm_provider import IBMProvider
from qiskit_aer import AerSimulator
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.algorithms import GroundStateEigensolver
from qiskit_nature.algorithms.ground_state_solvers import NumPyMinimumEigensolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_backend(backend_name: str):
    if backend_name == 'simulator':
        return AerSimulator()
    token = os.getenv('IBM_QUANTUM_TOKEN')
    if not token:
        raise ConnectionError("IBM_QUANTUM_TOKEN environment variable not set.")
    provider = IBMProvider(token=token, instance='ibm-q/open/main')
    return provider.get_backend(backend_name)

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    start_time = time.time()

    backend = get_backend(backend_name)

    geometries = {
        "H2": f"H 0 0 0; H 0 0 {bond_length}",
        "LiH": f"Li 0 0 0; H 0 0 {bond_length}",
        "H2O": f"O 0 0 0; H 0.758602 0.504284 {bond_length}; H -0.758602 0.504284 {bond_length}",
        "HF": f"H 0 0 0; F 0 0 {bond_length}",
        "LiF": f"Li 0 0 0; F 0 0 {bond_length}",
        "BeH2": f"Be 0 0 0; H 0 0 {bond_length}; H 0 0 {-bond_length}",
        "NH3": f"N 0 0 0; H 0.9377 0.3816 {bond_length}; H -0.9377 0.3816 {bond_length}; H 0 -0.7633 {bond_length}"
    }

    if molecule_name not in geometries:
        raise ValueError(f"Unsupported molecule: {molecule_name}")

    atom_string = geometries[molecule_name]

    transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2) if molecule_name in ["H2", "LiH"] else ActiveSpaceTransformer(num_electrons=8, num_spatial_orbitals=4)

    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()
    problem = transformer.transform(problem)

    mapper = JordanWignerMapper()

    num_particles = problem.num_particles
    num_spin_orbitals = problem.num_spatial_orbitals * 2

    initial_state = HartreeFock(num_spin_orbitals, num_particles, mapper)
    ansatz = UCCSD(num_spin_orbitals, num_particles, mapper, initial_state=initial_state)

    solver = GroundStateEigensolver(mapper, ansatz)
    result = solver.solve(problem)

    classical_solver = NumPyMinimumEigensolver()
    classical_result = classical_solver.solve(problem)

    energy = result.total_energies[0]
    exact_energy = classical_result.total_energies[0]
    error_mHa = abs(energy - exact_energy) * 1000
    end_time = time.time()

    return {
        "bond_length": bond_length,
        "energy": energy,
        "exact_energy": exact_energy,
        "error_mHa": error_mHa,
        "execution_time_sec": round(end_time - start_time, 2)
    }
