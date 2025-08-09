import React from 'react';
import { 
  XMarkIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { StageUpdate, ExecutionUpdate } from '../types/graphql';

interface StageDetailModalProps {
  stage: StageUpdate;
  execution?: ExecutionUpdate | null;
  onClose: () => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1048576) return `${Math.round(bytes / 1024)}KB`;
  return `${Math.round(bytes / 1048576 * 10) / 10}MB`;
};

const formatTime = (dateString?: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
};

const formatDuration = (minutes?: number) => {
  if (!minutes) return 'N/A';
  if (minutes < 1) return '<1min';
  if (minutes < 60) return `${minutes}min`;
  const hours = Math.floor(minutes / 60);
  const remainingMins = minutes % 60;
  return `${hours}h ${remainingMins}m`;
};

export const StageDetailModal: React.FC<StageDetailModalProps> = ({
  stage,
  execution,
  onClose,
}) => {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleDownloadOutput = (output: any) => {
    if (output.s3Location) {
      // In a real implementation, this would handle S3 downloads
      console.log('Download from:', output.s3Location);
    } else {
      // Create a blob with the content preview
      const blob = new Blob([output.contentPreview || ''], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = output.fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] w-full mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Stage {stage.stageId}: {stage.name}
            </h2>
            <div className="flex items-center space-x-4 mt-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                stage.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                stage.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                stage.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {stage.status}
              </span>
              <span className="text-sm text-gray-600">
                Progress: {Math.round(stage.progress)}%
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - General Info */}
            <div className="space-y-6">
              {/* Timing */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Timing</h3>
                <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Estimated Duration:</span>
                    <span className="text-sm font-medium">{formatDuration(stage.estimatedMinutes)}</span>
                  </div>
                  {stage.actualMinutes && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Actual Duration:</span>
                      <span className="text-sm font-medium">{formatDuration(stage.actualMinutes)}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Started At:</span>
                    <span className="text-sm font-medium">{formatTime(stage.startedAt)}</span>
                  </div>
                  {stage.completedAt && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Completed At:</span>
                      <span className="text-sm font-medium">{formatTime(stage.completedAt)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Progress</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Completion</span>
                    <span className="text-sm font-medium">{Math.round(stage.progress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all duration-300 ${
                        stage.status === 'FAILED' ? 'bg-red-500' :
                        stage.status === 'COMPLETED' ? 'bg-green-500' :
                        'bg-blue-500'
                      }`}
                      style={{ width: `${stage.progress}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Error */}
              {stage.error && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Error Details</h3>
                  <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                    <p className="text-sm text-red-800">{stage.error}</p>
                  </div>
                </div>
              )}

              {/* Metadata */}
              {stage.metadata && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Metadata</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                      {JSON.stringify(stage.metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - Outputs */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Stage Outputs ({stage.outputs.length})
              </h3>
              
              {stage.outputs.length === 0 ? (
                <div className="bg-gray-50 p-8 rounded-lg text-center">
                  <DocumentTextIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">No outputs generated yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {stage.outputs.map((output, index) => (
                    <div
                      key={index}
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <DocumentTextIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                            <h4 className="text-sm font-medium text-gray-900 truncate">
                              {output.fileName}
                            </h4>
                          </div>
                          
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                            <span>{formatFileSize(output.fileSize)}</span>
                            {output.generatedAt && (
                              <span>Generated: {formatTime(output.generatedAt)}</span>
                            )}
                          </div>
                          
                          {output.contentPreview && (
                            <div className="mt-3">
                              <div className="text-xs text-gray-600 mb-1">Preview:</div>
                              <div className="bg-gray-50 p-2 rounded text-xs text-gray-700 max-h-24 overflow-y-auto">
                                {output.contentPreview}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => handleDownloadOutput(output)}
                          className="ml-3 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                          title="Download file"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                        </button>
                      </div>
                      
                      {output.s3Location && (
                        <div className="mt-2 text-xs text-gray-500 font-mono bg-gray-50 p-1 rounded truncate">
                          {output.s3Location}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-600">
            {execution && (
              <span>
                Execution: {execution.jobId} • 
                Research: {execution.metadata?.researchDocId}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};