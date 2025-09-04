# Path: Qubic_Quests_Hackathon/backend/app.py
# --- FINAL PRODUCTION VERSION WITH CORRECT CORS ---

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sse import sse
import numpy as np
import json

# Import your quantum engine function
from engine import run_vqe_calculation

app = Flask(__name__)

# --- THIS IS THE CORRECTED LINE ---
# This tells your Render server to ONLY accept requests from your local
# test server and your live Vercel application.
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "https://qubit-quests.vercel.app"]}})

app.register_blueprint(sse, url_prefix='/stream')

# --- THE REST OF THE FILE IS UNCHANGED ---
@app.route('/api/run-vqe', methods=['POST'])
def vqe_endpoint():
    try:
        data = request.get_json()
        print(f"Received VQE request: {data}")
        backend_choice = data.get('backend', 'simulator')
        results = run_vqe_calculation(
            data['molecule'], 
            float(data['bondLength']), 
            data['basis'],
            backend_choice
        )
        return jsonify(results)
    except Exception as e:
        print(f"Error in /run-vqe: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dissociation-curve', methods=['POST'])
def dissociation_endpoint():
    try:
        data = request.get_json()
        print(f"Received Dissociation Curve request: {data}")
        molecule = data.get('molecule')
        basis = data.get('basis')
        
        bond_lengths = np.linspace(0.4, 2.5, 15)
        curve_data = []
        total_points = len(bond_lengths)

        for i, length in enumerate(bond_lengths):
            print(f"Calculating curve point {i+1}/{total_points}...")
            result = run_vqe_calculation(molecule, round(length, 4), basis, 'simulator')
            curve_data.append({"bond_length": length, "energy": result['energy']})
            
            progress = ((i + 1) / total_points) * 100
            sse.publish({"progress": progress}, type='progress_update')

        print("Dissociation curve calculation complete.")
        sse.publish({"message": "complete"}, type='progress_update')
        return jsonify({"curve_data": curve_data})
    except Exception as e:
        print(f"Error in /dissociation-curve: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)