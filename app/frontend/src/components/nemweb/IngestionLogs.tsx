import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNEMWEBIngestionLogs } from '@/api/hooks/apex';
import { CheckCircle2, XCircle, Clock, FileText } from 'lucide-react';

export function IngestionLogs() {
  const [dataTypeFilter, setDataTypeFilter] = useState<string>('all');
  const [regionFilter, setRegionFilter] = useState<string>('all');
  const [limit, setLimit] = useState<number>(50);

  const { data, isLoading, error } = useNEMWEBIngestionLogs(dataTypeFilter === 'all' ? null : dataTypeFilter, regionFilter === 'all' ? null : regionFilter, limit);

  const logs = data?.data || [];

  const statusColors: Record<string, string> = {
    SUCCESS: 'bg-green-500/20 text-green-300 border-green-500/50',
    PARTIAL: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
    FAILED: 'bg-red-500/20 text-red-300 border-red-500/50',
  };

  const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    SUCCESS: CheckCircle2,
    PARTIAL: Clock,
    FAILED: XCircle,
  };

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-48">
            <div className="text-gray-400">Loading ingestion logs...</div>
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
            <div className="text-red-400">Error loading ingestion logs</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl text-gray-100">Ingestion Logs</CardTitle>
            <div className="text-sm text-gray-400">Recent NEMWEB ingestion jobs</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Data Type:</span>
              <Select value={dataTypeFilter} onValueChange={setDataTypeFilter}>
                <SelectTrigger className="w-[180px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="DISPATCH_PRICES">Dispatch Prices</SelectItem>
                  <SelectItem value="PREDISPATCH_FORECASTS">Pre-Dispatch</SelectItem>
                  <SelectItem value="DEMAND_ACTUAL">Demand Actual</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Region:</span>
              <Select value={regionFilter} onValueChange={setRegionFilter}>
                <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="NSW1">NSW1</SelectItem>
                  <SelectItem value="VIC1">VIC1</SelectItem>
                  <SelectItem value="QLD1">QLD1</SelectItem>
                  <SelectItem value="SA1">SA1</SelectItem>
                  <SelectItem value="TAS1">TAS1</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Limit:</span>
              <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
                <SelectTrigger className="w-[100px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center text-gray-400">
              <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No ingestion logs found</p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Date Loaded</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Data Type</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Region</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Records</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Duration</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const StatusIcon = statusIcons[log.status] || Clock;

                  return (
                    <tr key={log.log_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                      <td className="py-3 px-4">
                        <div>
                          <div className="text-sm text-gray-200">{new Date(log.date_loaded).toLocaleDateString()}</div>
                          <div className="text-xs text-gray-500">{new Date(log.start_timestamp).toLocaleTimeString()}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm text-gray-300">{log.data_type.replace(/_/g, ' ')}</div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/50 text-xs">{log.region_id}</Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="text-sm text-gray-300">{log.records_loaded.toLocaleString()}</div>
                        {log.records_failed > 0 && <div className="text-xs text-red-400">{log.records_failed} failed</div>}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="text-sm text-gray-300">{log.duration_seconds ? `${log.duration_seconds.toFixed(1)}s` : 'N/A'}</div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge className={`${statusColors[log.status] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'} text-xs`}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {log.status}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
