import numpy as np
import logging
from qiskit.primitives import Estimator
from qiskit.algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit.algorithms.optimizers import L_BFGS_B
from qiskit_aer import AerSimulator
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.problems import ElectronicStructureProblem
from qiskit_nature.converters.second_quantization import QubitConverter

logging.basicConfig(level=logging.INFO)

def run_vqe_calculation(molecule, bond_length, basis, backend):
    try:
        logging.info(f"Starting VQE calculation for {molecule} at bond length {bond_length} Å")

        # Molecular geometry string
        geometry = [[molecule[0], [0.0, 0.0, 0.0]], [molecule[1:], [0.0, 0.0, bond_length]]]

        # Setup PySCF driver with active space
        driver = PySCFDriver(atom=geometry, basis=basis)
        transformer = ActiveSpaceTransformer(num_electrons=2, num_molecular_orbitals=2)

        # Define the electronic structure problem
        es_problem = ElectronicStructureProblem(driver, transformers=[transformer])

        # Second quantized operators
        second_q_ops = es_problem.second_q_ops()
        main_op = second_q_ops[0]

        # Map to qubit operator
        mapper = JordanWignerMapper()
        qubit_converter = QubitConverter(mapper=mapper)
        qubit_op = qubit_converter.convert(main_op, num_particles=es_problem.num_particles)

        # Setup estimator
        estimator = Estimator()

        # Define ansatz and initial state
        initial_state = HartreeFock(
            qubit_converter.num_qubits,
            qubit_converter.num_particles,
            qubit_converter.mapper,
        )
        ansatz = UCCSD(
            qubit_converter.num_qubits,
            num_particles=es_problem.num_particles,
            qubit_converter=qubit_converter,
            initial_state=initial_state,
        )

        # Optimizer with more max iterations
        optimizer = L_BFGS_B(maxiter=2000)

        # Setup VQE
        vqe_solver = VQE(
            ansatz=ansatz,
            optimizer=optimizer,
            estimator=estimator,
        )

        # Compute ground state energy
        result = vqe_solver.compute_minimum_eigenvalue(operator=qubit_op)

        # Compute exact energy for comparison
        exact_solver = NumPyMinimumEigensolver()
        exact_result = exact_solver.compute_minimum_eigenvalue(operator=qubit_op)

        response = {
            "bond_length": bond_length,
            "energy": result.eigenvalue.real,
            "exact_energy": exact_result.eigenvalue.real,
            "error_mHa": abs(result.eigenvalue.real - exact_result.eigenvalue.real) * 1e3
        }

        logging.info(f"Calculation complete for {molecule}: {response}")
        return response

    except Exception as e:
        logging.error(f"Error during VQE calculation: {str(e)}")
        raise
