import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { StartExecutionInput } from '../types/graphql';

interface NewExecutionModalProps {
  onClose: () => void;
  onSubmit: (input: StartExecutionInput) => Promise<void>;
  loading: boolean;
}

export const NewExecutionModal: React.FC<NewExecutionModalProps> = ({
  onClose,
  onSubmit,
  loading,
}) => {
  const [formData, setFormData] = useState({
    researchDocId: '',
    username: 'fprior',
    pipelineConfig: '{}',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !loading) {
      onClose();
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.researchDocId.trim()) {
      newErrors.researchDocId = 'Research document ID is required';
    }

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (formData.pipelineConfig) {
      try {
        JSON.parse(formData.pipelineConfig);
      } catch (e) {
        newErrors.pipelineConfig = 'Pipeline config must be valid JSON';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      const input: StartExecutionInput = {
        researchDocId: formData.researchDocId.trim(),
        username: formData.username.trim(),
        pipelineConfig: formData.pipelineConfig ? JSON.parse(formData.pipelineConfig) : undefined,
      };

      await onSubmit(input);
    } catch (error) {
      console.error('Failed to submit form:', error);
    }
  };

  const handleInputChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const sampleConfigs = [
    {
      name: 'Default',
      config: {}
    },
    {
      name: 'Fast Mode',
      config: {
        skipDetailedAnalysis: true,
        maxIdeasPerZone: 5,
        enableParallelProcessing: true
      }
    },
    {
      name: 'Comprehensive',
      config: {
        enableAdvancedClustering: true,
        maxIdeasPerZone: 20,
        includeMarketValidation: true,
        generateExtraDocumentation: true
      }
    }
  ];

  const applySampleConfig = (config: any) => {
    setFormData(prev => ({
      ...prev,
      pipelineConfig: JSON.stringify(config, null, 2)
    }));
    setErrors(prev => ({
      ...prev,
      pipelineConfig: ''
    }));
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Start New Pipeline Execution
          </h2>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Research Document ID */}
            <div>
              <label htmlFor="researchDocId" className="block text-sm font-medium text-gray-700 mb-2">
                Research Document ID *
              </label>
              <input
                type="text"
                id="researchDocId"
                value={formData.researchDocId}
                onChange={handleInputChange('researchDocId')}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.researchDocId ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., market-research-2024-01"
                disabled={loading}
              />
              {errors.researchDocId && (
                <p className="mt-1 text-sm text-red-600">{errors.researchDocId}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Unique identifier for the research document stored in S3
              </p>
            </div>

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Username *
              </label>
              <input
                type="text"
                id="username"
                value={formData.username}
                onChange={handleInputChange('username')}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.username ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., fprior"
                disabled={loading}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Your username for accessing S3 resources and creating GitHub repositories
              </p>
            </div>

            {/* Pipeline Configuration */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="pipelineConfig" className="block text-sm font-medium text-gray-700">
                  Pipeline Configuration (Optional)
                </label>
                <div className="flex space-x-2">
                  {sampleConfigs.map((sample) => (
                    <button
                      key={sample.name}
                      type="button"
                      onClick={() => applySampleConfig(sample.config)}
                      disabled={loading}
                      className="text-xs px-2 py-1 text-indigo-600 border border-indigo-300 rounded hover:bg-indigo-50 disabled:opacity-50"
                    >
                      {sample.name}
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                id="pipelineConfig"
                rows={8}
                value={formData.pipelineConfig}
                onChange={handleInputChange('pipelineConfig')}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm ${
                  errors.pipelineConfig ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter JSON configuration (optional)"
                disabled={loading}
              />
              {errors.pipelineConfig && (
                <p className="mt-1 text-sm text-red-600">{errors.pipelineConfig}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Advanced configuration options in JSON format. Leave empty for default settings.
              </p>
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading || !formData.researchDocId.trim() || !formData.username.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {loading && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {loading ? 'Starting...' : 'Start Execution'}
          </button>
        </div>
      </div>
    </div>
  );
};