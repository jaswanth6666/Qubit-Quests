import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Input } from './ui/Input';
import { Select } from './ui/Select';
import { Atom, Sliders, Cpu, Target } from 'lucide-react';

interface MolecularSetupProps {
  config: any;
  setConfig: (config: any) => void;
}

const MolecularSetup: React.FC<MolecularSetupProps> = ({ config, setConfig }) => {
  const updateConfig = (key: string, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Atom className="h-5 w-5 text-blue-600" />
            <span>Molecular System</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-800 mb-3">
              Molecule
            </label>
            <Select 
              value={config.molecule} 
              onChange={(e) => updateConfig('molecule', e.target.value)}
            >
              <option value="H2">H₂ (Hydrogen)</option>
              <option value="LiH">LiH (Lithium Hydride)</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-800 mb-3">
              Bond Length (Å)
            </label>
            <Input
              type="number"
              step="0.01"
              min="0.1"
              max="5.0"
              value={config.bondLength}
              onChange={(e) => updateConfig('bondLength', parseFloat(e.target.value))}
              className="font-mono"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-800 mb-3">
              Basis Set
            </label>
            <Select 
              value={config.basis} 
              onChange={(e) => updateConfig('basis', e.target.value)}
            >
              <option value="STO-3G">STO-3G (Minimal)</option>
              <option value="6-31G">6-31G (Split-valence)</option>
              <option value="cc-pVDZ">cc-pVDZ (Correlation-consistent)</option>
            </Select>
          </div>

          <div className="pt-4 border-t border-slate-200">
            <h4 className="font-semibold text-slate-900 mb-3">Expected Properties</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-700 font-medium">Qubits Required:</span>
                <span className="font-mono font-semibold text-blue-600">{config.molecule === 'H2' ? '2' : '8-10'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-700 font-medium">Pauli Terms:</span>
                <span className="font-mono font-semibold text-green-600">{config.molecule === 'H2' ? '5' : '20-30'}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sliders className="h-5 w-5 text-green-600" />
            <span>Variational Ansatz</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Ansatz Type
            </label>
            <Select 
              value={config.ansatz} 
              onChange={(e) => updateConfig('ansatz', e.target.value)}
            >
              <option value="UCCSD">UCCSD (Unitary Coupled Cluster)</option>
              <option value="HardwareEfficient">Hardware Efficient</option>
              <option value="ADAPT">ADAPT-VQE</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Optimizer
            </label>
            <Select 
              value={config.optimizer} 
              onChange={(e) => updateConfig('optimizer', e.target.value)}
            >
              <option value="COBYLA">COBYLA</option>
              <option value="SLSQP">SLSQP</option>
              <option value="SPSA">SPSA</option>
              <option value="L-BFGS-B">L-BFGS-B</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Max Iterations
            </label>
            <Input
              type="number"
              min="10"
              max="1000"
              value={config.maxIterations}
              onChange={(e) => updateConfig('maxIterations', parseInt(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Cpu className="h-5 w-5 text-purple-600" />
            <span>Quantum Backend</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Backend Type
            </label>
            <Select 
              value={config.backend} 
              onChange={(e) => updateConfig('backend', e.target.value)}
            >
              <option value="statevector">Ideal Statevector</option>
              <option value="qasm">QASM Simulator</option>
              <option value="noisy">Noisy Simulator</option>
              <option value="hardware">Real Hardware (Limited)</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Shots per Measurement
            </label>
            <Input
              type="number"
              min="100"
              max="100000"
              step="100"
              value={config.shots}
              onChange={(e) => updateConfig('shots', parseInt(e.target.value))}
              disabled={config.backend === 'statevector'}
            />
          </div>

          <div className="pt-4 border-t">
            <h4 className="font-medium text-slate-900 mb-3">Performance Estimate</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Circuit Depth:</span>
                <span className="font-mono">{config.ansatz === 'UCCSD' ? '12-20' : '4-8'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Runtime (est.):</span>
                <span className="font-mono">
                  {config.backend === 'statevector' ? '< 1 min' : '2-5 min'}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5 text-red-600" />
            <span>Reference Methods</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="p-3 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900">Hartree-Fock</h4>
              <p className="text-sm text-blue-700">Mean-field approximation</p>
            </div>
            
            <div className="p-3 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-900">Exact Diagonalization</h4>
              <p className="text-sm text-green-700">Full Configuration Interaction</p>
            </div>
            
            <div className="p-3 bg-purple-50 rounded-lg">
              <h4 className="font-medium text-purple-900">Chemical Accuracy</h4>
              <p className="text-sm text-purple-700">Target: ≤ 1.6 mHa error</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MolecularSetup;