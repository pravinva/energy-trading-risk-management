import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAgents, useAgentMessages } from '@/api/hooks/apex';
import { Bot, MessageCircle, CheckCircle2, Clock, XCircle } from 'lucide-react';

const agentTypeColors: Record<string, string> = {
  QUANT: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
  RISK: 'bg-red-500/20 text-red-300 border-red-500/50',
  EXECUTION: 'bg-green-500/20 text-green-300 border-green-500/50',
  FORECAST: 'bg-purple-500/20 text-purple-300 border-purple-500/50',
};

const messageTypeColors: Record<string, string> = {
  SIGNAL_VALIDATION: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
  VALIDATION_RESULT: 'bg-green-500/20 text-green-300 border-green-500/50',
  RISK_CHECK: 'bg-red-500/20 text-red-300 border-red-500/50',
  EXECUTION_REQUEST: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
  FORECAST_ANALYSIS: 'bg-purple-500/20 text-purple-300 border-purple-500/50',
};

const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  DELIVERED: CheckCircle2,
  PENDING: Clock,
  RESPONDED: CheckCircle2,
  FAILED: XCircle,
};

export function AgentCollaboration() {
  const [sessionFilter, setSessionFilter] = useState<string>('all');
  const [messageLimit, setMessageLimit] = useState<number>(50);

  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: messagesData, isLoading: messagesLoading } = useAgentMessages(sessionFilter === 'all' ? null : sessionFilter, messageLimit);

  const agents = agentsData?.data || [];
  const messages = messagesData?.data || [];

  return (
    <div className="space-y-6">
      {/* Active Agents */}
      <Card className="bg-gray-900 border-gray-700">
        <CardHeader className="border-b border-gray-700">
          <CardTitle className="text-xl text-gray-100">Active Agents</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          {agentsLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-gray-400">Loading agents...</div>
            </div>
          ) : agents.length === 0 ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center text-gray-400">
                <Bot className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No active agents</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-4">
              {agents.map((agent) => (
                <Card key={agent.agent_id} className="bg-gray-800 border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="p-2 bg-blue-500/20 rounded-lg">
                        <Bot className="h-5 w-5 text-blue-400" />
                      </div>
                      <Badge className={agentTypeColors[agent.agent_type] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'}>{agent.agent_type}</Badge>
                    </div>
                    <div className="text-sm font-medium text-gray-100 mb-1">{agent.agent_name}</div>
                    <div className="text-xs text-gray-400 line-clamp-2">{agent.description}</div>
                    <div className="mt-2 text-xs text-gray-500">
                      ID: <span className="text-gray-400">{agent.agent_id}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Agent Messages */}
      <Card className="bg-gray-900 border-gray-700">
        <CardHeader className="border-b border-gray-700">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl text-gray-100">Agent Communication</CardTitle>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Limit:</span>
                <Select value={messageLimit.toString()} onValueChange={(v) => setMessageLimit(parseInt(v))}>
                  <SelectTrigger className="w-[100px] bg-gray-800 border-gray-700 text-gray-200">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="20">20</SelectItem>
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
          {messagesLoading ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-gray-400">Loading messages...</div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-center text-gray-400">
                <MessageCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No agent messages</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((message) => {
                const StatusIcon = statusIcons[message.status] || Clock;
                const fromAgent = agents.find((a) => a.agent_id === message.from_agent_id);
                const toAgent = agents.find((a) => a.agent_id === message.to_agent_id);

                return (
                  <Card key={message.message_id} className="bg-gray-800 border-gray-700">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            <Badge className={agentTypeColors[fromAgent?.agent_type || ''] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'} variant="outline">
                              {fromAgent?.agent_type || message.from_agent_id.substring(0, 8)}
                            </Badge>
                            <span className="text-gray-500 text-sm">→</span>
                            <Badge className={agentTypeColors[toAgent?.agent_type || ''] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'} variant="outline">
                              {toAgent?.agent_type || message.to_agent_id.substring(0, 8)}
                            </Badge>
                          </div>
                          <Badge className={messageTypeColors[message.message_type] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'}>{message.message_type.replace(/_/g, ' ')}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="text-xs text-gray-400">{new Date(message.timestamp).toLocaleString()}</div>
                          <StatusIcon className={`h-4 w-4 ${message.status === 'DELIVERED' || message.status === 'RESPONDED' ? 'text-green-400' : message.status === 'FAILED' ? 'text-red-400' : 'text-yellow-400'}`} />
                        </div>
                      </div>
                      <div className="text-sm text-gray-300 bg-gray-900/50 p-3 rounded border border-gray-700">{message.content}</div>
                      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                        <div>Message ID: {message.message_id.substring(0, 12)}</div>
                        <div className="flex items-center gap-1">
                          Status: <span className={message.status === 'DELIVERED' || message.status === 'RESPONDED' ? 'text-green-400' : message.status === 'FAILED' ? 'text-red-400' : 'text-yellow-400'}>{message.status}</span>
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
    </div>
  );
}
