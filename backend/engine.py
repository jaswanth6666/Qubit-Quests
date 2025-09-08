import numpy as np
import time
import logging
from qiskit.primitives import Estimator
from qiskit_aer import AerSimulator
from qiskit_ibm_provider import IBMProvider
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.problems import ElectronicStructureProblem
from qiskit_nature.second_q.algorithms import GroundStateEigensolver, NumPyMinimumEigensolver
from qiskit_nature.second_q.converters import QubitConverter
from scipy.optimize import minimize

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MOLECULE_GEOMETRIES = {
    "H2": {"num_electrons": 2, "num_orbitals": 2, "geometry": lambda l: f"H 0 0 0; H 0 0 {l}"},
    "LiH": {"num_electrons": 2, "num_orbitals": 4, "geometry": lambda l: f"Li 0 0 0; H 0 0 {l}"},
    "H2O": {"num_electrons": 8, "num_orbitals": 4, "geometry": lambda l: f"O 0 0 0; H {l} 0 0; H {-l} 0 0"},
    "HF": {"num_electrons": 10, "num_orbitals": 5, "geometry": lambda l: f"H 0 0 0; F 0 0 {l}"},
    "LiF": {"num_electrons": 10, "num_orbitals": 5, "geometry": lambda l: f"Li 0 0 0; F 0 0 {l}"},
    "BeH2": {"num_electrons": 4, "num_orbitals": 4, "geometry": lambda l: f"H -{l} 0 0; Be 0 0 0; H {l} 0 0"},
    "NH3": {"num_electrons": 8, "num_orbitals": 4, "geometry": lambda l: f"N 0 0 0; H {l} 0 0; H 0 {l} 0; H 0 0 {l}"}
}

def get_backend(backend_name: str):
    if backend_name == 'simulator':
        return AerSimulator()
    token = os.getenv('IBM_QUANTUM_TOKEN')
    if not token:
        raise ConnectionError("IBM_QUANTUM_TOKEN env var missing.")
    provider = IBMProvider(token=token, instance='ibm-q/open/main')
    return provider.get_backend(backend_name)

def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    start_time = time.time()
    geometry_info = MOLECULE_GEOMETRIES.get(molecule_name)
    if not geometry_info:
        raise ValueError(f"Unsupported molecule: {molecule_name}")

    atom_string = geometry_info["geometry"](bond_length)
    transformer = ActiveSpaceTransformer(num_electrons=geometry_info["num_electrons"],
                                         num_spatial_orbitals=geometry_info["num_orbitals"])
    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()
    problem = transformer.transform(problem)

    qubit_converter = QubitConverter(mapper=JordanWignerMapper())

    electronic_structure_problem = ElectronicStructureProblem(driver, transformers=[transformer], qubit_converter=qubit_converter)
    solver = NumPyMinimumEigensolver()
    ground_state_solver = GroundStateEigensolver(qubit_converter, solver)
    classical_result = ground_state_solver.solve(problem)

    backend = get_backend(backend_name)

    estimator = Estimator()
    def vqe_objective(params):
        ansatz = UCCSD(num_spatial_orbitals=problem.num_spatial_orbitals,
                       num_particles=problem.num_particles,
                       qubit_converter=qubit_converter,
                       initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, qubit_converter.mapper))
        circuit = ansatz.assign_parameters(params)
        observable = problem.hamiltonian.second_q_op()
        result = estimator.run(circuits=[circuit], observables=[observable]).result()
        return result.values[0].real

    initial_params = np.zeros(problem.num_spatial_orbitals)
    optimizer_result = minimize(vqe_objective, initial_params, method='L-BFGS-B', options={'maxiter': 2000})

    qubit_op = qubit_converter.convert(problem.hamiltonian.second_q_op(), num_particles=problem.num_particles)

    final_energy = vqe_objective(optimizer_result.x) + problem.nuclear_repulsion_energy

    error_mHa = abs(final_energy - classical_result.total_energies[0]) * 1000
    execution_time_sec = time.time() - start_time

    return {
        "bond_length": bond_length,
        "energy": final_energy,
        "exact_energy": classical_result.total_energies[0],
        "error_mHa": error_mHa,
        "execution_time_sec": execution_time_sec
    }

def compute_dissociation_curve(molecule_name: str, basis: str):
    bond_lengths = np.linspace(0.4, 2.5, 7)  # Reduced points for speed
    curve_data = []
    for l in bond_lengths:
        result = run_vqe_calculation(molecule_name, round(l, 4), basis, 'simulator')
        curve_data.append({"bond_length": l, "energy": result["energy"]})
    return curve_data
