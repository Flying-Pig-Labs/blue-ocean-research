import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { 
  PlayIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { StageStatus } from '../types/graphql';

interface PipelineStageNodeData {
  stageId: number;
  name: string;
  status: StageStatus;
  progress: number;
  estimatedMinutes: number;
  actualMinutes?: number;
  description: string;
  inputs: string[];
  outputs: string[];
  startedAt?: string;
  completedAt?: string;
  error?: string;
  outputs?: Array<{
    fileName: string;
    fileSize: number;
    contentPreview: string;
    s3Location?: string;
    generatedAt: string;
  }>;
}

const getStatusColor = (status: StageStatus): string => {
  switch (status) {
    case 'RUNNING':
      return 'border-blue-500 bg-blue-50';
    case 'COMPLETED':
      return 'border-green-500 bg-green-50';
    case 'FAILED':
      return 'border-red-500 bg-red-50';
    case 'SKIPPED':
      return 'border-gray-400 bg-gray-50';
    default:
      return 'border-gray-300 bg-white';
  }
};

const getStatusIcon = (status: StageStatus): React.ReactElement => {
  switch (status) {
    case 'RUNNING':
      return <ArrowPathIcon className="h-4 w-4 text-blue-600 animate-spin" />;
    case 'COMPLETED':
      return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
    case 'FAILED':
      return <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />;
    case 'SKIPPED':
      return <ArrowPathIcon className="h-4 w-4 text-gray-400" />;
    default:
      return <ClockIcon className="h-4 w-4 text-gray-400" />;
  }
};

const formatDuration = (minutes: number): string => {
  if (minutes < 1) return '<1min';
  if (minutes === 1) return '1min';
  return `${minutes}min`;
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1048576) return `${Math.round(bytes / 1024)}KB`;
  return `${Math.round(bytes / 1048576 * 10) / 10}MB`;
};

export const PipelineStageNode = memo<NodeProps<PipelineStageNodeData>>(({ data, selected }) => {
  const {
    stageId,
    name,
    status,
    progress,
    estimatedMinutes,
    actualMinutes,
    description,
    inputs,
    outputs,
    startedAt,
    completedAt,
    error,
    outputs: stageOutputs
  } = data;

  const isRunning = status === 'RUNNING';
  const isCompleted = status === 'COMPLETED';
  const hasFailed = status === 'FAILED';

  return (
    <div className={`
      relative p-4 rounded-lg border-2 shadow-lg transition-all duration-200
      ${getStatusColor(status)}
      ${selected ? 'ring-2 ring-indigo-500 ring-offset-2' : ''}
      ${isRunning ? 'animate-pulse' : ''}
      min-w-[280px] max-w-[320px]
    `}>
      {/* Input Handle */}
      {stageId > 1 && (
        <Handle
          type="target"
          position={Position.Left}
          style={{
            background: '#6366f1',
            border: '2px solid white',
            width: 12,
            height: 12,
          }}
        />
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-medium">
            {stageId}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm leading-tight">{name}</h3>
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          {getStatusIcon(status)}
        </div>
      </div>

      {/* Progress Bar */}
      {(isRunning || isCompleted) && (
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-600">Progress</span>
            <span className="text-xs font-medium text-gray-900">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-300 ${
                hasFailed ? 'bg-red-500' : isCompleted ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Timing Information */}
      <div className="flex items-center justify-between mb-3 text-xs text-gray-600">
        <div className="flex items-center space-x-1">
          <ClockIcon className="h-3 w-3" />
          <span>
            Est: {formatDuration(estimatedMinutes)}
            {actualMinutes && ` / Actual: ${formatDuration(actualMinutes)}`}
          </span>
        </div>
        {startedAt && (
          <div className="text-right">
            <div>Started: {new Date(startedAt).toLocaleTimeString()}</div>
            {completedAt && (
              <div>Completed: {new Date(completedAt).toLocaleTimeString()}</div>
            )}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Stage Outputs */}
      {stageOutputs && stageOutputs.length > 0 && (
        <div className="mb-3">
          <div className="text-xs font-medium text-gray-700 mb-2">Outputs:</div>
          <div className="space-y-1">
            {stageOutputs.map((output, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-white rounded border text-xs"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {output.fileName}
                  </div>
                  <div className="text-gray-500 truncate">
                    {output.contentPreview}
                  </div>
                </div>
                <div className="ml-2 text-gray-400">
                  {formatFileSize(output.fileSize)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input/Output Summary (for pending stages) */}
      {status === 'PENDING' && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <div className="font-medium text-gray-700 mb-1">Inputs:</div>
            <div className="space-y-1">
              {inputs.map((input, index) => (
                <div key={index} className="text-gray-600 bg-gray-100 rounded px-2 py-1">
                  {input}
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="font-medium text-gray-700 mb-1">Outputs:</div>
            <div className="space-y-1">
              {outputs.map((output, index) => (
                <div key={index} className="text-gray-600 bg-gray-100 rounded px-2 py-1">
                  {output}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Output Handle */}
      {stageId < 7 && (
        <Handle
          type="source"
          position={Position.Right}
          style={{
            background: '#6366f1',
            border: '2px solid white',
            width: 12,
            height: 12,
          }}
        />
      )}
    </div>
  );
});