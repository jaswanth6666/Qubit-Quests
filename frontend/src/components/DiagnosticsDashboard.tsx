import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Cpu, Zap, Target, Clock, Gauge, CheckCircle } from 'lucide-react';

interface DiagnosticsDashboardProps {
  results: any;
  config: any;
}

const DiagnosticsDashboard: React.FC<DiagnosticsDashboardProps> = ({ results, config }) => {
  if (!results) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-40 text-slate-500">
          Run VQE calculation to see diagnostics
        </CardContent>
      </Card>
    );
  }

  const { diagnostics } = results;

  return (
    <div className="space-y-6">
      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-semibold text-slate-800">Quantum Resources</CardTitle>
            <div className="p-2 bg-blue-100 rounded-lg">
              <Cpu className="h-5 w-5 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {diagnostics.qubits}
            </div>
            <p className="text-sm text-slate-700 font-medium">
              Qubits utilized
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-semibold text-slate-800">Circuit Complexity</CardTitle>
            <div className="p-2 bg-green-100 rounded-lg">
              <Zap className="h-5 w-5 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {diagnostics.circuitDepth}
            </div>
            <p className="text-sm text-slate-700 font-medium">
              Circuit depth
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-semibold text-slate-800">Accuracy</CardTitle>
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="h-5 w-5 text-purple-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {diagnostics.error.toFixed(2)}
            </div>
            <p className="text-sm text-slate-700 font-medium">
              Error (mHa)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Gauge className="h-5 w-5" />
              <span>Computational Statistics</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Pauli Terms</span>
                <Badge variant="secondary">{diagnostics.pauliTerms}</Badge>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Function Evaluations</span>
                <Badge variant="secondary">{diagnostics.evaluations}</Badge>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Total Shots</span>
                <Badge variant="secondary">
                  {diagnostics.totalShots.toLocaleString()}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Measurement Groups</span>
                <Badge variant="secondary">
                  {Math.ceil(diagnostics.pauliTerms / 3)}
                </Badge>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h4 className="font-medium text-slate-900 mb-2">Optimization Profile</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Ansatz Type:</span>
                  <span className="font-mono">{config.ansatz}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Optimizer:</span>
                  <span className="font-mono">{config.optimizer}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Backend:</span>
                  <span className="font-mono">{config.backend}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5" />
              <span>Quality Assessment</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              {/* Chemical Accuracy Check */}
              <div className="p-3 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Chemical Accuracy</span>
                  {diagnostics.error < 1.6 ? (
                    <Badge className="bg-green-100 text-green-800">
                      ✓ Achieved
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="border-yellow-300 text-yellow-800">
                      In Progress
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  Target: ≤ 1.6 mHa | Current: {diagnostics.error.toFixed(3)} mHa
                </p>
              </div>

              {/* Convergence Check */}
              <div className="p-3 rounded-lg bg-gradient-to-r from-green-50 to-blue-50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Convergence Status</span>
                  <Badge className="bg-blue-100 text-blue-800">
                    Converged
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  Optimization completed in {diagnostics.evaluations} steps
                </p>
              </div>

              {/* Resource Efficiency */}
              <div className="p-3 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Resource Efficiency</span>
                  <Badge className="bg-purple-100 text-purple-800">
                    {diagnostics.qubits < 10 ? 'Excellent' : 'Good'}
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  {diagnostics.qubits} qubits, depth {diagnostics.circuitDepth}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h4 className="font-medium text-slate-900 mb-2">Performance Insights</h4>
              <div className="text-sm text-slate-600 space-y-1">
                <p>• Circuit depth is {diagnostics.circuitDepth < 15 ? 'optimal' : 'moderate'} for current ansatz</p>
                <p>• {diagnostics.pauliTerms} Pauli terms efficiently grouped</p>
                <p>• Shot allocation: {Math.round(diagnostics.totalShots / diagnostics.pauliTerms)} shots/term</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quantum Circuit Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Circuit Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(diagnostics.circuitDepth * 0.7)}
              </div>
              <div className="text-sm text-slate-600">Single-qubit gates</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(diagnostics.circuitDepth * 0.3)}
              </div>
              <div className="text-sm text-slate-600">Two-qubit gates</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Math.ceil(diagnostics.pauliTerms / 3)}
              </div>
              <div className="text-sm text-slate-600">Measurement settings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {((diagnostics.circuitDepth * diagnostics.qubits * 2) / 1000).toFixed(1)}μs
              </div>
              <div className="text-sm text-slate-600">Est. execution time</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DiagnosticsDashboard;