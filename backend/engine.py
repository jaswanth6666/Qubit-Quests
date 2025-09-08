import numpy as np
import time
import os
import logging
from typing import Tuple, List
from scipy.optimize import minimize
from qiskit_algorithms.minimum_eigensolvers import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Estimator
from qiskit_ibm_provider import IBMProvider
from qiskit_aer import AerSimulator
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Supported molecules with atomic templates
MOLECULES = {
    "H2": {
        "atoms": ["H 0 0 0", "H 0 0 {bond_length}"],
        "num_electrons": 2,
        "num_orbitals": 2
    },
    "LiH": {
        "atoms": ["Li 0 0 0", "H 0 0 {bond_length}"],
        "num_electrons": 2,
        "num_orbitals": 5
    },
    "H2O": {
        "atoms": ["O 0 0 0", "H {bond_length} 0 0", "H {-bond_length} 0 0"],
        "num_electrons": 8,
        "num_orbitals": 7
    },
    "HF": {
        "atoms": ["H 0 0 0", "F 0 0 {bond_length}"],
        "num_electrons": 10,
        "num_orbitals": 7
    },
    "LiF": {
        "atoms": ["Li 0 0 0", "F 0 0 {bond_length}"],
        "num_electrons": 10,
        "num_orbitals": 7
    },
    "BeH2": {
        "atoms": ["Be 0 0 0", "H {bond_length} 0 0", "H {-bond_length} 0 0"],
        "num_electrons": 4,
        "num_orbitals": 5
    },
    "NH3": {
        "atoms": ["N 0 0 0", "H {bond_length} 0 0", "H {-bond_length/2} {bond_length*np.sqrt(3)/2} 0", "H {-bond_length/2} {-bond_length*np.sqrt(3)/2} 0"],
        "num_electrons": 5,
        "num_orbitals": 6
    }
}

def get_backend(backend_name: str):
    logging.info(f"Attempting to get backend: '{backend_name}'")
    if backend_name == 'simulator':
        logging.info("SUCCESS: Selected Ideal Local Simulator (AerSimulator).")
        return AerSimulator()
    token = os.getenv('IBM_QUANTUM_TOKEN')
    if not token:
        raise ConnectionError("IBM_QUANTUM_TOKEN environment variable not set.")
    try:
        logging.info("Found IBM_QUANTUM_TOKEN, connecting...")
        provider = IBMProvider(token=token, instance="ibm-q/open/main")
        backend = provider.get_backend(backend_name)
        logging.info(f"Connected to IBM backend '{backend_name}'.")
        return backend
    except Exception as e:
        logging.error(f"Failed to connect to IBM backend: {e}")
        raise

def build_atom_string(atoms_template: List[str], bond_length: float) -> str:
    atoms = []
    for line in atoms_template:
        formatted = line.format(bond_length=bond_length, np=np)
        atoms.append(formatted)
    return "; ".join(atoms)

def compute_energy(molecule_name: str, bond_length: float, basis: str, backend_name: str) -> float:
    backend = get_backend(backend_name)
    molecule = MOLECULES[molecule_name]
    atom_string = build_atom_string(molecule["atoms"], bond_length)
    transformer = ActiveSpaceTransformer(num_electrons=molecule["num_electrons"], num_spatial_orbitals=molecule["num_orbitals"])
    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()
    problem = transformer.transform(problem)
    mapper = JordanWignerMapper()
    qubit_op = mapper.map(problem.hamiltonian.second_q_op())
    ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper))
    optimizer = COBYLA(maxiter=500)
    convergence_history = []
    def callback(eval_count, parameters, mean, std): convergence_history.append(mean)
    if isinstance(backend, AerSimulator):
        estimator = Estimator()
        vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
        result = vqe_solver.compute_minimum_eigenvalue(qubit_op)
    else:
        with backend.open_session() as session:
            estimator = Estimator(session=session)
            vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
            result = vqe_solver.compute_minimum_eigenvalue(qubit_op)
    total_energy = result.eigenvalue.real + problem.nuclear_repulsion_energy
    return total_energy

def scan_bond_lengths(molecule_name: str, basis: str, backend_name: str) -> Tuple[float, float]:
    logging.info(f"Scanning bond lengths for {molecule_name}...")
    bond_lengths = np.linspace(0.5, 2.5, 20)
    energies = []
    for bl in bond_lengths:
        try:
            energy = compute_energy(molecule_name, bl, basis, backend_name)
            logging.info(f"Bond Length = {bl:.3f} → Energy = {energy:.6f}")
            energies.append((bl, energy))
        except Exception as e:
            logging.error(f"Failed at bond length {bl}: {e}")
    optimal_bond, min_energy = min(energies, key=lambda x: x[1])
    logging.info(f"Optimal bond length after scan: {optimal_bond:.3f}, Energy: {min_energy:.6f}")
    return optimal_bond, min_energy

def optimize_bond_length(molecule_name: str, basis: str, backend_name: str, initial_guess: float) -> Tuple[float, float]:
    logging.info(f"Starting optimization around {initial_guess}...")
    def objective(bl):
        try:
            return compute_energy(molecule_name, bl[0], basis, backend_name)
        except Exception as e:
            logging.error(f"Error in optimization: {e}")
            return 1e6
    result = minimize(objective, [initial_guess], bounds=[(0.1, 3.0)], method='L-BFGS-B', options={'maxiter': 100})
    if result.success:
        logging.info(f"Optimization success: {result.x[0]:.4f}, Energy: {result.fun:.6f}")
    else:
        logging.error(f"Optimization failed: {result.message}")
    return result.x[0], result.fun

def run_vqe_calculation(molecule_name: str, basis: str = "STO-3G", backend_name: str = "simulator"):
    logging.info(f"Running full VQE workflow for {molecule_name}")
    optimal_bond_scan, energy_scan = scan_bond_lengths(molecule_name, basis, backend_name)
    optimal_bond_opt, energy_opt = optimize_bond_length(molecule_name, basis, backend_name, optimal_bond_scan)
    logging.info(f"Final optimized bond length: {optimal_bond_opt:.4f}, Energy: {energy_opt:.6f}")
    return optimal_bond_opt, energy_opt

# Example Usage:
if __name__ == "__main__":
    molecule = "H2"  # Change to desired molecule
    run_vqe_workflow(molecule)
