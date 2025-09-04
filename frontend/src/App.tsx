// Path: Qubic_Quests_Hackathon/frontend/src/App.tsx

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/Tabs';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { Badge } from './components/ui/Badge';
import { Progress } from './components/ui/Progress';
import MolecularSetup from './components/MolecularSetup';
import EnergyPlot from './components/EnergyPlot';
import DiagnosticsDashboard from './components/DiagnosticsDashboard';
import ResultsTable from './components/ResultsTable';
import { Play, Download, Settings, Atom, BarChart3, FileText, Loader2 } from 'lucide-react';

interface VQEResult {
  energy: number;
  convergence: { iteration: number; energy: number }[];
  diagnostics: {
    qubits: number;
    pauliTerms: number;
    circuitDepth: number;
    evaluations: number;
    error: number; 
    totalShots: number;
  };
}
interface MoleculeConfig {
  molecule: 'H2' | 'LiH';
  bondLength: number;
  basis: string;
  ansatz: string;
  optimizer: string;
  backend: string;
  shots: number;
  maxIterations: number;
}
interface DissociationPoint {
  bond_length: number;
  energy: number;
}

// *** THIS MUST BE YOUR DEPLOYED RENDER URL ***
const API_BASE_URL = "https://qubit-quests.onrender.com";

function App() {
  const [config, setConfig] = useState<MoleculeConfig>({
    molecule: 'H2',
    bondLength: 0.74,
    basis: 'STO-3G',
    ansatz: 'UCCSD',
    optimizer: 'COBYLA',
    backend: 'simulator',
    shots: 4000,
    maxIterations: 200
  });
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<VQEResult | null>(null);
  const [dissociationData, setDissociationData] = useState<DissociationPoint[]>([]);
  const [activeTab, setActiveTab] = useState('setup');

  const runVQE = async () => {
    setIsRunning(true);
    setProgress(10);
    setResults(null);
    setActiveTab('setup');
    console.log("FRONTEND: Sending request with config:", config);
    try {
      const response = await fetch(`${API_BASE_URL}/api/run-vqe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error("Server returned an error:", errorData);
        throw new Error(`Server error: ${errorData.error || response.status}`);
      }
      const backendData = await response.json();
      const formattedResults: VQEResult = {
        energy: backendData.energy,
        convergence: backendData.convergence.map((e: number, i: number) => ({ iteration: i, energy: e })),
        diagnostics: {
          qubits: backendData.diagnostics.qubits,
          pauliTerms: backendData.diagnostics.pauliTerms,
          circuitDepth: backendData.diagnostics.circuitDepth,
          evaluations: backendData.diagnostics.evaluations,
          error: backendData.error_mHa,
          totalShots: 0,
        }
      };
      setResults(formattedResults);
      setProgress(100);
      setActiveTab('results');
    } catch (error) {
      console.error("FRONTEND: Failed to run VQE:", error);
    } finally {
      setIsRunning(false);
      setProgress(0);
    }
  };

  const generateDissociationCurve = async () => {
    setIsRunning(true);
    setDissociationData([]);
    setProgress(0);
    setActiveTab('analysis');
    const eventSource = new EventSource(`${API_BASE_URL}/stream`);
    eventSource.addEventListener('progress_update', (event) => {
      const data = JSON.parse(event.data);
      if (data.progress) setProgress(data.progress);
      if (data.message === 'complete') eventSource.close();
    });
    eventSource.onerror = () => eventSource.close();
    try {
      const response = await fetch(`${API_BASE_URL}/api/dissociation-curve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ molecule: config.molecule, basis: config.basis }),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();
      setDissociationData(data.curve_data);
      setActiveTab('results');
    } catch (error) {
        console.error("Failed to generate dissociation curve:", error);
    } finally {
        setIsRunning(false);
        setProgress(0);
        eventSource.close();
    }
  };

  const exportResults = () => {
    if (!results) return;
    const data = { configuration: config, results, dissociation: dissociationData };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vqe_results_${config.molecule}_${config.bondLength}A.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="sticky top-0 z-50 border-b shadow-sm bg-white/90 backdrop-blur-md border-slate-300">
        <div className="px-6 py-4 mx-auto max-w-7xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-3 shadow-lg bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-xl"><Atom className="w-6 h-6 text-white" /></div>
              <div>
                <h1 className="text-3xl font-bold text-transparent bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text">Quantum Chemistry VQE</h1>
                <p className="text-sm font-medium text-slate-700">Variational Quantum Eigensolver for Molecular Systems</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Badge variant={isRunning ? "destructive" : "secondary"} className={`px-3 py-1 text-sm font-semibold ${isRunning ? 'bg-red-100 text-red-800 border-red-200' : 'bg-green-100 text-green-800 border-green-200'}`}>{isRunning ? "Running" : "Ready"}</Badge>
              <Button onClick={runVQE} disabled={isRunning} className="font-semibold transition-all duration-200 shadow-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:shadow-xl">
                { isRunning ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" /> }
                { isRunning ? "Calculating..." : "Run VQE" }
              </Button>
            </div>
          </div>
          {isRunning && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2 text-sm font-medium text-slate-700"><span>Calculation Progress</span><span>{Math.round(progress)}%</span></div>
              <Progress value={progress} className="h-3 bg-slate-200" />
            </div>
          )}
        </div>
      </div>
      <div className="px-6 py-8 mx-auto max-w-7xl">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 border shadow-lg bg-white/80 backdrop-blur-md border-slate-200">
            <TabsTrigger value="setup" className="flex items-center space-x-2"><Settings className="w-4 h-4" /><span>Setup</span></TabsTrigger>
            <TabsTrigger value="results" className="flex items-center space-x-2" disabled={!results}><BarChart3 className="w-4 h-4" /><span>Results</span></TabsTrigger>
            <TabsTrigger value="diagnostics" className="flex items-center space-x-2" disabled={!results}><FileText className="w-4 h-4" /><span>Diagnostics</span></TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center space-x-2" disabled={!results}><Atom className="w-4 h-4" /><span>Analysis</span></TabsTrigger>
          </TabsList>
          <TabsContent value="setup" className="space-y-6"><MolecularSetup config={config} setConfig={setConfig} /></TabsContent>
          <TabsContent value="results" className="space-y-6">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card><CardHeader><CardTitle className="flex items-center space-x-2"><BarChart3 className="w-5 h-5 text-blue-600" /><span>Energy Convergence</span></CardTitle></CardHeader><CardContent><EnergyPlot data={results?.convergence || []} /></CardContent></Card>
              <Card>
                <CardHeader><div className="flex items-center justify-between"><CardTitle>Results Summary</CardTitle><Button variant="outline" size="sm" onClick={exportResults} disabled={!results}><Download className="w-4 h-4 mr-2" />Export</Button></div></CardHeader>
                <CardContent><ResultsTable results={results} config={config} /></CardContent>
              </Card>
            </div>
            {dissociationData.length > 0 && (
              <Card className='mt-6'>
                <CardHeader><CardTitle>Dissociation Curve</CardTitle></CardHeader>
                <CardContent><EnergyPlot data={dissociationData.map(d => ({ iteration: d.bond_length * 100, energy: d.energy }))} xLabel="Bond Length (Å)" isDissociation={true} /></CardContent>
              </Card>
            )}
          </TabsContent>
          <TabsContent value="diagnostics" className="space-y-6"><DiagnosticsDashboard results={results} config={config} /></TabsContent>
          <TabsContent value="analysis" className="space-y-6">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>Advanced Analysis</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <Button onClick={generateDissociationCurve} disabled={isRunning} className="w-full">
                    { isRunning && progress > 0 ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null }
                    Generate Dissociation Curve
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;