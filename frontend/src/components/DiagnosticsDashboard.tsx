// Path: frontend/src/components/DiagnosticsDashboard.tsx

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

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3 space-y-0">
            <CardTitle className="text-sm font-semibold text-slate-800">Quantum Resources</CardTitle>
            <div className="p-2 bg-blue-100 rounded-lg">
              <Cpu className="w-5 h-5 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">–</div>
            <p className="text-sm font-medium text-slate-700">Qubits utilized (Not provided)</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3 space-y-0">
            <CardTitle className="text-sm font-semibold text-slate-800">Circuit Complexity</CardTitle>
            <div className="p-2 bg-green-100 rounded-lg">
              <Zap className="w-5 h-5 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">–</div>
            <p className="text-sm font-medium text-slate-700">Circuit depth (Not provided)</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3 space-y-0">
            <CardTitle className="text-sm font-semibold text-slate-800">Accuracy</CardTitle>
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="w-5 h-5 text-purple-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {results.error_mHa.toFixed(3)}
            </div>
            <p className="text-sm font-medium text-slate-700">Error (mHa)</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Gauge className="w-5 h-5" />
              <span>Computational Statistics</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Pauli Terms</span>
                <Badge variant="secondary">–</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Function Evaluations</span>
                <Badge variant="secondary">–</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Total Shots</span>
                <Badge variant="secondary">–</Badge>
              </div>
            </div>
            <div className="pt-4 border-t">
              <h4 className="mb-2 font-medium text-slate-900">Optimization Profile</h4>
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
              <CheckCircle className="w-5 h-5" />
              <span>Quality Assessment</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Chemical Accuracy</span>
                  {results.error_mHa < 1.6 ? (
                    <Badge className="text-green-800 bg-green-100">✓ Achieved</Badge>
                  ) : (
                    <Badge variant="outline">In Progress</Badge>
                  )}
                </div>
                <p className="mt-1 text-xs text-slate-600">
                  Target: ≤ 1.6 mHa | Current: {results.error_mHa.toFixed(3)} mHa
                </p>
              </div>

              <div className="p-3 rounded-lg bg-gradient-to-r from-green-50 to-blue-50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Convergence Status</span>
                  <Badge className="text-blue-800 bg-blue-100">–</Badge>
                </div>
                <p className="mt-1 text-xs text-slate-600">Optimization status not provided</p>
              </div>

              <div className="p-3 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Resource Efficiency</span>
                  <Badge className="text-purple-800 bg-purple-100">–</Badge>
                </div>
                <p className="mt-1 text-xs text-slate-600">Resource usage not available</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DiagnosticsDashboard;
