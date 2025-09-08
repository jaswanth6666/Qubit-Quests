import numpy as np
import os
import time
import logging
from typing import List, Tuple
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------------------------------------
# Define Molecule Templates
# ------------------------------------------------
MOLECULES = {
    "H2": {
        "atoms": ["H 0 0 0", "H 0 0 {bond_length}"],
        "num_electrons": 2,
        "num_orbitals": 2,
    },
    "LiH": {
        "atoms": ["Li 0 0 0", "H 0 0 {bond_length}"],
        "num_electrons": 2,
        "num_orbitals": 5,
    },
    "H2O": {
        "atoms": ["O 0 0 0", "H {bond_length} 0 0", "H {-bond_length} 0 0"],
        "num_electrons": 8,
        "num_orbitals": 7,
    },
    "HF": {
        "atoms": ["H 0 0 0", "F 0 0 {bond_length}"],
        "num_electrons": 10,
        "num_orbitals": 7,
    },
    "LiF": {
        "atoms": ["Li 0 0 0", "F 0 0 {bond_length}"],
        "num_electrons": 10,
        "num_orbitals": 7,
    },
    "BeH2": {
        "atoms": ["Be 0 0 0", "H {bond_length} 0 0", "H {-bond_length} 0 0"],
        "num_electrons": 4,
        "num_orbitals": 5,
    },
    "NH3": {
        "atoms": [
            "N 0 0 0",
            "H {bond_length} 0 0",
            "H {-bond_length/2} {bond_length*np.sqrt(3)/2} 0",
            "H {-bond_length/2} {-bond_length*np.sqrt(3)/-2} 0",
        ],
        "num_electrons": 5,
        "num_orbitals": 6,
    },
}


# ------------------------------------------------
# Helpers
# ------------------------------------------------
def get_backend(backend_name: str):
    """Return AerSimulator or IBM backend."""
    if backend_name == "simulator":
        return AerSimulator()
    token = os.getenv("IBM_QUANTUM_TOKEN")
    if not token:
        raise ConnectionError("IBM_QUANTUM_TOKEN not set")
    provider = IBMProvider(token=token, instance="ibm-q/open/main")
    return provider.get_backend(backend_name)


def build_atom_string(atoms_template: List[str], bond_length: float) -> str:
    atoms = []
    for line in atoms_template:
        formatted = line.format(bond_length=bond_length, np=np)
        atoms.append(formatted)
    return "; ".join(atoms)


def compute_energy(molecule_name: str, bond_length: float, basis: str, backend_name: str) -> float:
    """Compute total energy for a given bond length."""
    molecule = MOLECULES[molecule_name]
    atom_string = build_atom_string(molecule["atoms"], bond_length)

    driver = PySCFDriver(atom=atom_string, basis=basis.lower())
    problem = driver.run()

    transformer = ActiveSpaceTransformer(
        num_electrons=molecule["num_electrons"], num_spatial_orbitals=molecule["num_orbitals"]
    )
    problem = transformer.transform(problem)

    mapper = JordanWignerMapper()
    qubit_op = mapper.map(problem.hamiltonian.second_q_op())

    ansatz = UCCSD(
        problem.num_spatial_orbitals,
        problem.num_particles,
        mapper,
        initial_state=HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper),
    )

    optimizer = COBYLA(maxiter=50)
    backend = get_backend(backend_name)

    convergence = []

    def callback(eval_count, params, mean, std):
        convergence.append(mean)

    if isinstance(backend, AerSimulator):
        estimator = Estimator()
        vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
        vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)
    else:
        with backend.open_session() as session:
            estimator = Estimator(session=session)
            vqe_solver = VQE(estimator, ansatz, optimizer, callback=callback)
            vqe_result = vqe_solver.compute_minimum_eigenvalue(qubit_op)

    total_energy = vqe_result.eigenvalue.real + problem.nuclear_repulsion_energy
    return total_energy


# ------------------------------------------------
# Bond Length Search + Optimization
# ------------------------------------------------
def scan_bond_lengths(molecule_name: str, basis: str, backend: str) -> Tuple[float, float]:
    bond_lengths = np.linspace(0.5, 2.5, 5)
    results = []
    for bl in bond_lengths:
        try:
            e = compute_energy(molecule_name, bl, basis, backend)
            results.append((bl, e))
        except Exception as ex:
            logging.error(f"Failed at {bl:.2f}: {ex}")

    best_bl, best_e = min(results, key=lambda x: x[1])
    return best_bl, best_e


def optimize_bond_length(molecule_name: str, basis: str, backend: str, initial_guess: float) -> Tuple[float, float]:
    def objective(bl):
        return compute_energy(molecule_name, float(bl[0]), basis, backend)

    result = minimize(objective, [initial_guess], bounds=[(0.3, 3.0)], method="L-BFGS-B")
    return float(result.x[0]), float(result.fun)


# ------------------------------------------------
# Public API Function
# ------------------------------------------------
def run_vqe_calculation(molecule_name: str, bond_length: float, basis: str, backend_name: str):
    """
    Entry point for app.py.
    - Ignores input bond_length (we compute best automatically).
    - Returns optimal bond length and energy.
    """
    start = time.time()

    # Step 1: scan coarse bond lengths
    approx_bl, approx_energy = scan_bond_lengths(molecule_name, basis, backend_name)

    # Step 2: refine using optimizer
    opt_bl, opt_energy = optimize_bond_length(molecule_name, basis, backend_name, approx_bl)

    end = time.time()

    return {
        "molecule": molecule_name,
        "basis": basis,
        "approx_bond_length": approx_bl,
        "approx_energy": approx_energy,
        "optimal_bond_length": opt_bl,
        "optimal_energy": opt_energy,
        "execution_time_sec": end - start,
    }
