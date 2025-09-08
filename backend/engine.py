import numpy as np
import logging
from qiskit.primitives import Estimator
from qiskit_algorithms.optimizers import L_BFGS_B
from qiskit_aer import AerSimulator
from qiskit_ibm_provider import IBMProvider
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.problems import ElectronicStructureProblem
from qiskit_nature.algorithms import GroundStateEigensolver, NumPyMinimumEigensolver
from qiskit_nature.converters.second_quantization import QubitConverter

logging.basicConfig(level=logging.INFO)

def run_vqe_calculation(molecule, bond_length, basis, backend):
    logging.info(f"Running VQE for {molecule} at bond length {bond_length} Å")

    # Molecular geometry setup
    geometry = {
        'H2': [['H', [0.0, 0.0, 0.0]], ['H', [0.0, 0.0, bond_length]]],
        'LiH': [['Li', [0.0, 0.0, 0.0]], ['H', [0.0, 0.0, bond_length]]]
    }

    if molecule not in geometry:
        raise ValueError(f"Unsupported molecule '{molecule}'.")

    driver = PySCFDriver(atom=geometry[molecule], basis=basis)

    transformer = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2)
    es_problem = ElectronicStructureProblem(driver, transformers=[transformer])

    # Set up backend
    estimator = Estimator()  # Uses AerSimulator by default

    # Setup mapper & qubit converter
    mapper = JordanWignerMapper()
    qubit_converter = QubitConverter(mapper=mapper)

    # Define initial state and ansatz
    initial_state = HartreeFock(
        num_spin_orbitals=es_problem.num_spin_orbitals,
        num_particles=es_problem.num_particles,
        qubit_mapper=mapper
    )
    ansatz = UCCSD(
        num_spin_orbitals=es_problem.num_spin_orbitals,
        num_particles=es_problem.num_particles,
        qubit_mapper=mapper,
        initial_state=initial_state
    )

    # Optimizer
    optimizer = L_BFGS_B(maxiter=2000)

    # Ground state solver
    solver = GroundStateEigensolver(
        qubit_converter=qubit_converter,
        solver=VQE(estimator=estimator, ansatz=ansatz, optimizer=optimizer)
    )

    result = solver.solve(es_problem)

    # Exact result for comparison
    exact_solver = NumPyMinimumEigensolver()
    exact_result = exact_solver.compute_minimum_eigenvalue(es_problem.second_q_ops()[0])

    energy = result.total_energy
    exact_energy = exact_result.eigenvalue.real
    error_mHa = abs(energy - exact_energy) * 1e3

    logging.info(f"VQE Energy: {energy} Hartree | Exact Energy: {exact_energy} Hartree | Error: {error_mHa:.4f} mHa")

    return {
        "bond_length": bond_length,
        "energy": energy,
        "exact_energy": exact_energy,
        "error_mHa": error_mHa
    }
