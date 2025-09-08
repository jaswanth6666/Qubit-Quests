import numpy as np
import time
import logging
from qiskit.primitives import Estimator
from qiskit.algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit.algorithms.optimizers import COBYLA
from qiskit_aer import AerSimulator
from qiskit_ibm_provider import IBMProvider
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from scipy.optimize import minimize

logging.basicConfig(level=logging.INFO)

SUPPORTED_MOLECULES = ["H2", "LiH", "H2O", "HF", "LiF", "BeH2", "NH3"]

MOLECULE_GEOMETRIES = {
    "H2": lambda bl: f"H 0 0 0; H 0 0 {bl}",
    "LiH": lambda bl: f"Li 0 0 0; H 0 0 {bl}",
    "H2O": lambda bl: f"O 0 0 0; H 0 {bl} 0; H {bl} 0 0",
    "HF": lambda bl: f"H 0 0 0; F 0 0 {bl}",
    "LiF": lambda bl: f"Li 0 0 0; F 0 0 {bl}",
    "BeH2": lambda bl: f"Be 0 0 0; H {bl} 0 0; H {-bl} 0 0",
    "NH3": lambda bl: f"N 0 0 0; H {bl} 0 0; H 0 {bl} 0; H -{bl} 0 0",
}

def get_active_space_transformer(molecule: str):
    if molecule in ["H2", "HF", "LiF"]:
        return ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
    elif molecule == "LiH":
        return ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=5)
    elif molecule == "H2O":
        return ActiveSpaceTransformer(num_electrons=4, num_spatial_orbitals=4)
    elif molecule == "BeH2":
        return ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=3)
    elif molecule == "NH3":
        return ActiveSpaceTransformer(num_electrons=4, num_spatial_orbitals=4)
    else:
        raise ValueError("Unsupported molecule")

def run_single_vqe(molecule: str, basis: str, bond_length: float):
    logging.info(f"Running VQE for {molecule} at bond length {bond_length}")

    atom_string = MOLECULE_GEOMETRIES[molecule](bond_length)
    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()
    transformer = get_active_space_transformer(molecule)
    problem = transformer.transform(problem)

    mapper = JordanWignerMapper()
    qubit_op = mapper.map(problem.hamiltonian.second_q_op())

    ansatz = UCCSD(
        problem.num_spatial_orbitals,
        problem.num_particles,
        mapper,
        initial_state=HartreeFock(
            problem.num_spatial_orbitals,
            problem.num_particles,
            mapper
        )
    )
    optimizer = COBYLA(maxiter=50)

    estimator = Estimator()

    vqe_solver = VQE(estimator, ansatz, optimizer)
    vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)

    classical_solver = NumPyMinimumEigensolver()
    classical_result = classical_solver.compute_minimum_eigenvalue(qubit_op)

    total_vqe_energy = vqe_result.eigenvalue.real + problem.nuclear_repulsion_energy
    total_exact_energy = classical_result.eigenvalue.real + problem.nuclear_repulsion_energy
    error_mHa = abs(total_vqe_energy - total_exact_energy) * 1000

    return {
        "bond_length": bond_length,
        "energy": total_vqe_energy,
        "exact_energy": total_exact_energy,
        "error_mHa": error_mHa
    }

def run_vqe_calculation(molecule: str, basis: str, bond_length: float):
    if molecule not in SUPPORTED_MOLECULES:
        raise ValueError(f"Unsupported molecule: {molecule}")

    # Simple single-point calculation for quick response
    result = run_single_vqe(molecule, basis, bond_length)
    return result
