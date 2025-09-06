// Path: frontend/src/components/ResultsTable.tsx

import React from 'react';
import { Badge } from './ui/Badge';

interface ResultsTableProps {
  results: any;
  config: any;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, config }) => {
  if (!results) {
    return (
      <div className="py-8 text-center text-slate-500">
        No results available. Run VQE calculation to see results.
      </div>
    );
  }

  const vqeEnergy = results.energy;
  const exactEnergy = results.exact_energy;
  const vqeError = results.diagnostics.error;

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="font-medium text-slate-900">Energy Comparison</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 border border-blue-200 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl">
            <div>
              <div className="font-semibold text-blue-900">VQE Energy (Quantum)</div>
              <div className="text-sm font-medium text-blue-700">Variational result</div>
            </div>
            <div className="text-right">
              <div className="font-mono text-lg font-bold text-blue-900">{vqeEnergy.toFixed(6)} Ha</div>
              <Badge className="font-semibold text-blue-800 bg-blue-200">{(vqeEnergy * 27.2114).toFixed(2)} eV</Badge>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 border border-green-200 bg-gradient-to-r from-green-50 to-green-100 rounded-xl">
            <div>
              <div className="font-semibold text-green-900">Exact Energy (True)</div>
              <div className="text-sm font-medium text-green-700">Full CI reference</div>
            </div>
            <div className="text-right">
              <div className="font-mono text-lg font-bold text-green-900">{exactEnergy.toFixed(6)} Ha</div>
              <Badge className="font-semibold text-green-800 bg-green-200">{(exactEnergy * 27.2114).toFixed(2)} eV</Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-medium text-slate-900">Error Analysis</h3>
        <div className="p-3 border rounded-lg border-slate-200">
            <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">VQE vs Exact Error</span>
                <span className="font-mono text-lg font-bold text-green-600">{vqeError.toFixed(3)} mHa</span>
            </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-medium text-slate-900">System Configuration</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex justify-between"><span className="text-slate-600">Molecule:</span><span className="font-mono">{config.molecule}</span></div>
            <div className="flex justify-between"><span className="text-slate-600">Bond Length:</span><span className="font-mono">{config.bondLength} Å</span></div>
            <div className="flex justify-between"><span className="text-slate-600">Basis Set:</span><span className="font-mono">{config.basis}</span></div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between"><span className="text-slate-600">Ansatz:</span><span className="font-mono">{config.ansatz}</span></div>
            <div className="flex justify-between"><span className="text-slate-600">Optimizer:</span><span className="font-mono">{config.optimizer}</span></div>
            <div className="flex justify-between"><span className="text-slate-600">Backend:</span><span className="font-mono">{config.backend}</span></div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-medium text-slate-900">Convergence Summary</h3>
        <div className="p-4 rounded-lg bg-slate-50">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-slate-900">{results.convergence.length}</div>
              <div className="text-sm text-slate-600">Total Iterations</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{results.diagnostics.evaluations}</div>
              <div className="text-sm text-slate-600">Function Calls</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{vqeError < 1.6 ? '✓' : '○'}</div>
              <div className="text-sm text-slate-600">Chem. Accuracy</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsTable;