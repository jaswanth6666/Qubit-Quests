from qiskit import IBMQ

# Load your IBMQ account using the API key
IBMQ.save_account('FbRbRQUoNjxUuatxK5r6m06Y6HgpgvQZ6f_X-jID8XY8')  # Save the API key if you haven't already done so
IBMQ.load_account()  # Load your saved account

# Get the provider (accessing IBM Quantum systems)
provider = IBMQ.get_provider(hub='ibm-q')

# List available backends
backends = provider.backends()

# Check the number of qubits for each backend
for backend in backends:
    print(f"Backend: {backend.name()}, Qubits: {backend.configuration().num_qubits}")

