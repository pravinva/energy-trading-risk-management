import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNEMWEBDataFreshness } from '@/api/hooks/apex';
import { Clock, Database, AlertCircle, CheckCircle2 } from 'lucide-react';

export function DataFreshness() {
  const { data, isLoading, error } = useNEMWEBDataFreshness();

  const freshness = data?.data || [];

  // Determine freshness status based on lag
  const getFreshnessStatus = (minutes: number | null) => {
    if (minutes === null) return { status: 'unknown', color: 'bg-gray-500/20 text-gray-300 border-gray-500/50', icon: AlertCircle };
    if (minutes < 10) return { status: 'fresh', color: 'bg-green-500/20 text-green-300 border-green-500/50', icon: CheckCircle2 };
    if (minutes < 30) return { status: 'recent', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50', icon: Clock };
    return { status: 'stale', color: 'bg-red-500/20 text-red-300 border-red-500/50', icon: AlertCircle };
  };

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-48">
            <div className="text-gray-400">Loading data freshness...</div>
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
            <div className="text-red-400">Error loading data freshness</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <CardTitle className="text-xl text-gray-100">NEMWEB Data Freshness</CardTitle>
        <div className="text-sm text-gray-400">Latest data timestamps and lag</div>
      </CardHeader>
      <CardContent className="p-6">
        {freshness.length === 0 ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center text-gray-400">
              <Database className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No data available</p>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {freshness.map((item) => {
              const freshnessInfo = getFreshnessStatus(item.minutes_since_latest);
              const StatusIcon = freshnessInfo.icon;

              return (
                <Card key={`${item.data_type}-${item.region_id}`} className="bg-gray-800 border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="text-sm font-medium text-gray-100">{item.data_type.replace(/_/g, ' ')}</div>
                        <div className="text-xs text-gray-400">{item.region_id}</div>
                      </div>
                      <Badge className={`text-xs ${freshnessInfo.color}`}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {freshnessInfo.status.toUpperCase()}
                      </Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Latest Data:</span>
                        <span className="text-gray-300">{item.latest_data_timestamp ? new Date(item.latest_data_timestamp).toLocaleString() : 'N/A'}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Lag:</span>
                        <span className={item.minutes_since_latest !== null && item.minutes_since_latest < 30 ? 'text-green-400' : 'text-red-400'}>{item.minutes_since_latest !== null ? `${item.minutes_since_latest} min` : 'N/A'}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Total Records:</span>
                        <span className="text-gray-300">{item.total_records.toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Last Ingestion:</span>
                        <span className="text-gray-300">{item.last_ingestion_timestamp ? new Date(item.last_ingestion_timestamp).toLocaleTimeString() : 'N/A'}</span>
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
