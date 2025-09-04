
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Input } from './ui/Input';
import { Select } from './ui/Select';
import { Atom, Sliders, Cpu } from 'lucide-react';

interface MolecularSetupProps {
  config: any;
  setConfig: (config: any) => void;
}

const MolecularSetup: React.FC<MolecularSetupProps> = ({ config, setConfig }) => {
  const updateConfig = (key: string, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2"><Atom className="w-5 h-5 text-blue-600" /><span>Molecular System</span></CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block mb-3 text-sm font-semibold text-slate-800">Molecule</label>
            <Select value={config.molecule} onChange={(e) => updateConfig('molecule', e.target.value)}>
              <option value="H2">H₂ (Hydrogen)</option>
              <option value="LiH">LiH (Lithium Hydride)</option>
            </Select>
          </div>
          <div>
            <label className="block mb-3 text-sm font-semibold text-slate-800">Bond Length (Å)</label>
            <Input type="number" step="0.01" min="0.1" max="5.0" value={config.bondLength} onChange={(e) => updateConfig('bondLength', parseFloat(e.target.value))} className="font-mono"/>
          </div>
          <div>
            <label className="block mb-3 text-sm font-semibold text-slate-800">Basis Set</label>
            <Select value={config.basis} onChange={(e) => updateConfig('basis', e.target.value)}>
              <option value="STO-3G">STO-3G (Minimal)</option>
              <option value="6-31G">6-31G (Split-valence)</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2"><Sliders className="w-5 h-5 text-green-600" /><span>Variational Ansatz</span></CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
           <div>
            <label className="block mb-2 text-sm font-medium text-slate-700">Ansatz Type</label>
            <Select value={config.ansatz} disabled><option value="UCCSD">UCCSD</option></Select>
          </div>
          <div>
            <label className="block mb-2 text-sm font-medium text-slate-700">Optimizer</label>
            <Select value={config.optimizer} disabled><option value="COBYLA">COBYLA</option></Select>
          </div>
        </CardContent>
      </Card>
      
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2"><Cpu className="w-5 h-5 text-purple-600" /><span>Quantum Backend</span></CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium text-slate-700">Backend Type</label>
            <Select value={config.backend} onChange={(e) => updateConfig('backend', e.target.value)}>
              <option value="simulator">Ideal Simulator (Fastest)</option>
              <option value="ibmq_qasm_simulator">IBM Cloud Simulator</option>
              <option value="ibm_brisbane">IBM Brisbane (Real Hardware)</option>
              <option value="ibm_kyoto">IBM Kyoto (Real Hardware)</option>
            </Select>
            <p className="mt-2 text-xs text-slate-500">Calculations on real hardware may have long queue times.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MolecularSetup;