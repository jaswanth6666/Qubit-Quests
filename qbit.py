from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.primitives import Estimator
from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

def compute_min_ground_state_energy(molecule: str, distance_range: list):
    min_energy = float('inf')
    optimal_distance = None
    optimal_result = None

    for bond_distance in distance_range:
        print(f"Calculating for {molecule} at bond distance {bond_distance} Å...")

        # Define molecular geometry
        if molecule == "H2":
            atom_str = f"H 0 0 0; H 0 0 {bond_distance}"
        elif molecule == "LiH":
            atom_str = f"Li 0 0 0; H 0 0 {bond_distance}"
        elif molecule == "HF":
            atom_str = f"H 0 0 0; F 0 0 {bond_distance}"
        elif molecule == "H2O":
            atom_str = f"O 0 0 0; H 0 0 {bond_distance}; H 0.76 0.58 0"
        else:
            raise ValueError(f"Molecule {molecule} not supported yet.")

        # Initialize PySCFDriver
        driver = PySCFDriver(
            atom=atom_str,
            basis="sto3g",
            charge=0,
            spin=0,
            unit=DistanceUnit.ANGSTROM
        )
        es_problem = driver.run()

        # Use Jordan-Wigner Mapper
        mapper = JordanWignerMapper()

        # Define Ansatz and VQE solver
        ansatz = UCCSD(
            es_problem.num_spatial_orbitals,
            es_problem.num_particles,
            mapper,
            initial_state=HartreeFock(
                es_problem.num_spatial_orbitals,
                es_problem.num_particles,
                mapper
            )
        )
        vqe_solver = VQE(Estimator(), ansatz, SLSQP())
        vqe_solver.initial_point = [0.0] * ansatz.num_parameters

        # Ground state eigensolver
        calc = GroundStateEigensolver(mapper, vqe_solver)

        # Solve the problem
        result = calc.solve(es_problem)
        energy = result.total_energy

        print(f"  --> Energy: {energy:.6f} Hartree")

        if energy < min_energy:
            min_energy = energy
            optimal_distance = bond_distance
            optimal_result = result

    print(f"\n✅ Lowest energy for {molecule}: {min_energy:.6f} Hartree at bond distance {optimal_distance} Å\n")
    return optimal_distance, min_energy, optimal_result


# Molecules to compute
molecule_list = ["H2", "LiH", "HF", "H2O"]

# Define bond distance range (in Angstrom)
distance_range = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]

# Run calculations
for molecule in molecule_list:
    optimal_distance, min_energy, result = compute_min_ground_state_energy(molecule, distance_range)
    print(f"*** Molecule: {molecule}")
    print(f"Optimal Bond Distance: {optimal_distance} Å")
    print(f"Minimum Ground State Energy: {min_energy:.6f} Hartree")
    print("-" * 60)
