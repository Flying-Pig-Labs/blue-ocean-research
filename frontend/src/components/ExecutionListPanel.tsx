import React from 'react';
import { 
  ArrowPathIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { ExecutionUpdate, ExecutionStatus } from '../types/graphql';

interface ExecutionListPanelProps {
  executions: ExecutionUpdate[];
  selectedJobId: string | null;
  loading: boolean;
  onExecutionSelect: (jobId: string) => void;
  onRefresh: () => Promise<void>;
}

const getStatusIcon = (status: ExecutionStatus) => {
  switch (status) {
    case 'RUNNING':
      return <ArrowPathIcon className="h-4 w-4 text-blue-600 animate-spin" />;
    case 'COMPLETED':
      return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
    case 'FAILED':
      return <XCircleIcon className="h-4 w-4 text-red-600" />;
    case 'CANCELLED':
      return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />;
    default:
      return <ClockIcon className="h-4 w-4 text-gray-400" />;
  }
};

const getStatusColor = (status: ExecutionStatus) => {
  switch (status) {
    case 'RUNNING':
      return 'bg-blue-50 border-blue-200';
    case 'COMPLETED':
      return 'bg-green-50 border-green-200';
    case 'FAILED':
      return 'bg-red-50 border-red-200';
    case 'CANCELLED':
      return 'bg-yellow-50 border-yellow-200';
    default:
      return 'bg-gray-50 border-gray-200';
  }
};

const formatTimeAgo = (timestamp: string) => {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now.getTime() - time.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
};

const formatDuration = (minutes: number) => {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainingMins = minutes % 60;
  return `${hours}h ${remainingMins}m`;
};

export const ExecutionListPanel: React.FC<ExecutionListPanelProps> = ({
  executions,
  selectedJobId,
  loading,
  onExecutionSelect,
  onRefresh,
}) => {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Refresh Button */}
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={onRefresh}
          disabled={loading}
          className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Execution List */}
      <div className="flex-1 overflow-y-auto">
        {loading && executions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <ArrowPathIcon className="h-6 w-6 mx-auto mb-2 animate-spin" />
            Loading executions...
          </div>
        ) : executions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <ClockIcon className="h-6 w-6 mx-auto mb-2" />
            No executions found
          </div>
        ) : (
          <div className="space-y-2 p-2">
            {executions.map((execution) => (
              <div
                key={execution.jobId}
                onClick={() => onExecutionSelect(execution.jobId)}
                className={`
                  p-3 rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-md
                  ${selectedJobId === execution.jobId ? 'ring-2 ring-indigo-500 ring-offset-1' : ''}
                  ${getStatusColor(execution.status)}
                `}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    {getStatusIcon(execution.status)}
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {execution.metadata?.researchDocId || execution.jobId}
                      </div>
                      <div className="text-xs text-gray-500">
                        {execution.metadata?.username}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 ml-2">
                    {formatTimeAgo(execution.timestamp)}
                  </div>
                </div>

                {/* Progress */}
                <div className="mb-2">
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>
                      Stage {execution.currentStage}/7: {execution.stageName}
                    </span>
                    <span>{Math.round(execution.overallProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        execution.status === 'FAILED' ? 'bg-red-500' :
                        execution.status === 'COMPLETED' ? 'bg-green-500' :
                        'bg-blue-500'
                      }`}
                      style={{ width: `${execution.overallProgress}%` }}
                    />
                  </div>
                </div>

                {/* Status Info */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 text-gray-500">
                    {execution.status === 'RUNNING' && execution.estimatedRemainingMinutes && (
                      <>
                        <ClockIcon className="h-3 w-3" />
                        <span>~{execution.estimatedRemainingMinutes}min left</span>
                      </>
                    )}
                    {execution.status === 'COMPLETED' && execution.metadata?.actualDurationMinutes && (
                      <>
                        <CheckCircleIcon className="h-3 w-3" />
                        <span>Completed in {formatDuration(execution.metadata.actualDurationMinutes)}</span>
                      </>
                    )}
                    {execution.status === 'QUEUED' && (
                      <span className="text-gray-400">Queued</span>
                    )}
                  </div>
                  
                  {execution.results?.githubRepoUrl && (
                    <a
                      href={execution.results.githubRepoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-indigo-600 hover:text-indigo-800 font-medium"
                    >
                      View Repo →
                    </a>
                  )}
                </div>

                {/* Error Message */}
                {execution.error && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                    <strong>Error:</strong> {execution.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};