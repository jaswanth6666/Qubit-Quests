# Path: Qubic_Quests_Hackathon/backend/app.py
# --- FINAL VERSION WITH BOTH API ENDPOINTS ---

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

# Import our quantum engine function
from engine import run_vqe_calculation

app = Flask(__name__)
CORS(app)

# Endpoint for a single VQE calculation
@app.route('/api/run-vqe', methods=['POST'])
def vqe_endpoint():
    try:
        data = request.get_json()
        print(f"Received VQE request: {data}")

        molecule = data.get('molecule')
        bond_length = float(data.get('bondLength'))
        basis = data.get('basis')

        results = run_vqe_calculation(molecule, bond_length, basis)
        return jsonify(results)

    except Exception as e:
        print(f"Error in /run-vqe: {e}")
        return jsonify({"error": str(e)}), 500

# Endpoint for generating the dissociation curve
@app.route('/api/dissociation-curve', methods=['POST'])
def dissociation_endpoint():
    try:
        data = request.get_json()
        print(f"Received Dissociation Curve request: {data}")

        molecule = data.get('molecule')
        basis = data.get('basis')
        
        # Define the range of bond lengths to simulate
        bond_lengths = np.linspace(0.4, 2.5, 15)
        curve_data = []

        for i, length in enumerate(bond_lengths):
            print(f"Calculating curve point {i+1}/{len(bond_lengths)} at length {length:.2f} Å...")
            # We round the length to avoid floating point issues
            result = run_vqe_calculation(molecule, round(length, 4), basis)
            curve_data.append({
                "bond_length": length,
                "energy": result['energy']
            })

        print("Dissociation curve calculation complete.")
        return jsonify({"curve_data": curve_data})

    except Exception as e:
        print(f"Error in /dissociation-curve: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)