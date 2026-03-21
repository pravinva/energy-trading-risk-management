import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNEMWEBQualitySummary } from '@/api/hooks/apex';
import { CheckCircle2, XCircle, Activity } from 'lucide-react';

export function DataQuality() {
  const { data, isLoading, error } = useNEMWEBQualitySummary(7);

  const quality = data?.data || [];

  const metricColors: Record<string, string> = {
    COMPLETENESS: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
    TIMELINESS: 'bg-green-500/20 text-green-300 border-green-500/50',
    ACCURACY: 'bg-purple-500/20 text-purple-300 border-purple-500/50',
    CONSISTENCY: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
  };

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-48">
            <div className="text-gray-400">Loading data quality metrics...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-48">
            <div className="text-red-400">Error loading data quality</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <CardTitle className="text-xl text-gray-100">Data Quality Summary</CardTitle>
        <div className="text-sm text-gray-400">Last 7 days quality checks</div>
      </CardHeader>
      <CardContent className="p-6">
        {quality.length === 0 ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center text-gray-400">
              <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No quality checks run yet</p>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {quality.map((item, idx) => {
              const passRate = item.total_checks > 0 ? (item.passed_checks / item.total_checks) * 100 : 0;

              return (
                <Card key={idx} className="bg-gray-800 border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="text-sm font-medium text-gray-100">{item.data_type.replace(/_/g, ' ')}</div>
                        <Badge className={`mt-1 text-xs ${metricColors[item.metric_name] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'}`}>{item.metric_name}</Badge>
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${passRate >= 95 ? 'text-green-400' : passRate >= 80 ? 'text-yellow-400' : 'text-red-400'}`}>{passRate.toFixed(0)}%</div>
                        <div className="text-xs text-gray-500">Pass Rate</div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Total Checks:</span>
                        <span className="text-gray-300">{item.total_checks}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3 text-green-400" />
                          Passed:
                        </span>
                        <span className="text-green-400">{item.passed_checks}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500 flex items-center gap-1">
                          <XCircle className="h-3 w-3 text-red-400" />
                          Failed:
                        </span>
                        <span className="text-red-400">{item.failed_checks}</span>
                      </div>

                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Avg Value:</span>
                          <span className="text-gray-300">{item.avg_metric_value.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Range:</span>
                          <span className="text-gray-300">
                            {item.min_metric_value.toFixed(2)} - {item.max_metric_value.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
