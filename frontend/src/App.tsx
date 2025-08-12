/**
 * Multi-Step LLM Pipeline Frontend - Main Application Component
 * 
 * Purpose: Root component that orchestrates the entire pipeline visualization interface,
 *          providing real-time monitoring and control of AWS Batch pipeline executions.
 * 
 * This component serves as the central hub for the innovation pipeline frontend,
 * managing execution state, GraphQL subscriptions, and coordinating all child
 * components for a seamless monitoring experience.
 * 
 * Key Responsibilities:
 * 1. Manage global application state (selected job, stage, modals)
 * 2. Handle GraphQL queries and mutations for execution management
 * 3. Coordinate component interactions and data flow
 * 4. Provide responsive layout with collapsible sidebar
 * 5. Display real-time execution status and progress
 * 
 * Component Architecture:
 * - ExecutionListPanel: Sidebar showing all pipeline executions
 * - PipelineFlowVisualization: Main canvas with ReactFlow pipeline diagram
 * - NewExecutionModal: Form for starting new pipeline runs
 * - StageDetailModal: Detailed view of individual stage outputs
 * 
 * GraphQL Integration:
 * - Queries: ListExecutions, GetExecution
 * - Mutations: StartExecution
 * - Subscriptions: Real-time updates handled in child components
 * 
 * State Management:
 * - selectedJobId: Currently selected pipeline execution
 * - selectedStageId: Currently selected stage for detail view
 * - showNewExecutionModal: Controls new execution modal visibility
 * - showExecutionList: Controls sidebar visibility
 * 
 * @author Multi-Step LLM Pipeline Team
 * @version 2.0.0
 * @date January 2025
 */

import React, { useState, useCallback } from 'react';
import { PipelineFlowVisualization } from './components/PipelineFlowVisualization';
import { StageDetailModal } from './components/StageDetailModal';
import { ExecutionListPanel } from './components/ExecutionListPanel';
import { NewExecutionModal } from './components/NewExecutionModal';
import { useGraphQLQuery, useGraphQLMutation } from './hooks/useGraphQLSubscription';
import { ExecutionUpdate, StartExecutionInput, StageUpdate } from './types/graphql';

import 'reactflow/dist/style.css';
import './App.css';

function App() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [selectedStageId, setSelectedStageId] = useState<number | null>(null);
  const [showNewExecutionModal, setShowNewExecutionModal] = useState(false);
  const [showExecutionList, setShowExecutionList] = useState(true);

  // GraphQL query to fetch all pipeline executions
  // Returns up to 20 most recent executions with metadata and progress info
  // Used to populate the sidebar execution list panel
  const { 
    data: executionsData, 
    loading: executionsLoading, 
    refetch: refetchExecutions 
  } = useGraphQLQuery<{ listExecutions: { items: ExecutionUpdate[] } }>(
    `
    query ListExecutions {
      listExecutions(limit: 20) {
        items {
          jobId
          status
          currentStage
          stageName
          stageProgress
          overallProgress
          estimatedRemainingMinutes
          timestamp
          metadata {
            researchDocId
            username
            startedAt
            estimatedTotalMinutes
          }
          results {
            githubRepoUrl
            githubRepoName
          }
        }
        nextToken
      }
    }
    `
  );

  // GraphQL mutation for starting new pipeline executions
  // Triggers AWS Batch job submission and returns job ID
  // Used by NewExecutionModal when user submits the form
  const { executeMutation: startExecution, loading: startingExecution } = useGraphQLMutation<{
    startExecution: ExecutionUpdate;
  }>();

  // GraphQL query for detailed execution data of selected job
  // Fetches complete stage information, outputs, and results
  // Only runs when selectedJobId is set (conditional query)
  const { data: currentExecutionData } = useGraphQLQuery<{ getExecution: ExecutionUpdate }>(
    `
    query GetExecution($jobId: ID!) {
      getExecution(jobId: $jobId) {
        jobId
        status
        currentStage
        stageName
        stageProgress
        overallProgress
        estimatedRemainingMinutes
        completedStages {
          stageId
          name
          status
          progress
          startedAt
          completedAt
          estimatedMinutes
          actualMinutes
          outputs {
            fileName
            fileSize
            contentPreview
            s3Location
            generatedAt
          }
          error
        }
        currentStageUpdate {
          stageId
          name
          status
          progress
          outputs {
            fileName
            fileSize
            contentPreview
          }
        }
        error
        timestamp
        metadata {
          researchDocId
          username
          startedAt
          completedAt
          totalStages
          estimatedTotalMinutes
          actualDurationMinutes
          pipelineVersion
        }
        results {
          githubRepoUrl
          githubRepoName
          issuesCreated
          analysisResults
          finalPortfolio
        }
      }
    }
    `,
    selectedJobId ? { jobId: selectedJobId } : undefined
  );

  const executions = executionsData?.listExecutions?.items || [];
  const currentExecution = currentExecutionData?.getExecution;

  /**
   * Handle execution selection from the sidebar panel.
   * Updates selected job and clears any selected stage.
   * Triggers re-fetch of execution details via GraphQL.
   * 
   * @param jobId - AWS Batch job ID to select
   */
  const handleExecutionSelect = useCallback((jobId: string) => {
    setSelectedJobId(jobId);
    setSelectedStageId(null); // Clear stage selection when switching executions
  }, []);

  /**
   * Handle stage node click from the pipeline visualization.
   * Opens the stage detail modal with outputs and logs.
   * 
   * @param stageId - Pipeline stage ID (1-7)
   */
  const handleStageClick = useCallback((stageId: number) => {
    setSelectedStageId(stageId);
  }, []);

  /**
   * Handle new execution submission from modal form.
   * Executes GraphQL mutation to start AWS Batch job.
   * Updates UI state and refreshes execution list on success.
   * 
   * @param input - Execution parameters (research ID, configuration)
   * @returns Promise that resolves when execution starts
   * @throws Error if mutation fails (handled by mutation hook)
   */
  const handleNewExecution = useCallback(async (input: StartExecutionInput) => {
    try {
      const mutation = `
        mutation StartExecution($input: StartExecutionInput!) {
          startExecution(input: $input) {
            jobId
            status
            timestamp
            metadata {
              researchDocId
              username
              startedAt
            }
          }
        }
      `;

      const result = await startExecution(mutation, { input });
      const newJobId = result.startExecution.jobId;
      
      setSelectedJobId(newJobId);
      setShowNewExecutionModal(false);
      
      // Refresh the executions list
      await refetchExecutions();
      
    } catch (error) {
      console.error('Failed to start execution:', error);
      // Error handling is managed by the mutation hook
    }
  }, [startExecution, refetchExecutions]);

  /**
   * Compute selected stage data from execution state.
   * Checks both completed stages and current running stage.
   * Memoized to prevent unnecessary re-renders.
   * 
   * @returns Stage data for modal display or null if not found
   */
  const selectedStage = React.useMemo(() => {
    if (!currentExecution || !selectedStageId) return null;
    
    // First check completed stages, then check if it's the current running stage
    return currentExecution.completedStages.find(stage => stage.stageId === selectedStageId) ||
           (currentExecution.currentStageUpdate?.stageId === selectedStageId 
             ? currentExecution.currentStageUpdate 
             : null);
  }, [currentExecution, selectedStageId]);

  return (
    <div className="h-screen flex bg-gray-100">
      {/* Sidebar - Execution List */}
      {showExecutionList && (
        <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h1 className="text-lg font-semibold text-gray-900">
                Pipeline Executions
              </h1>
              <button
                onClick={() => setShowNewExecutionModal(true)}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                New Execution
              </button>
            </div>
          </div>
          
          <ExecutionListPanel
            executions={executions}
            selectedJobId={selectedJobId}
            loading={executionsLoading}
            onExecutionSelect={handleExecutionSelect}
            onRefresh={refetchExecutions}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowExecutionList(!showExecutionList)}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h2 className="text-xl font-semibold text-gray-900">
                Multi-Step LLM Pipeline
              </h2>
              {selectedJobId && (
                <span className="text-sm text-gray-500">
                  Job: {selectedJobId}
                </span>
              )}
            </div>
            
            {currentExecution?.status && (
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  currentExecution.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                  currentExecution.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                  currentExecution.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {currentExecution.status}
                </span>
                
                {currentExecution.results?.githubRepoUrl && (
                  <a
                    href={currentExecution.results.githubRepoUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-indigo-700 bg-indigo-100 hover:bg-indigo-200"
                  >
                    View Repository
                  </a>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Pipeline Visualization */}
        <div className="flex-1 p-4">
          {selectedJobId ? (
            <PipelineFlowVisualization
              jobId={selectedJobId}
              onStageClick={handleStageClick}
            />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Execution Selected
                </h3>
                <p className="text-gray-500 mb-4">
                  Select an execution from the sidebar or create a new one to view the pipeline visualization.
                </p>
                <button
                  onClick={() => setShowNewExecutionModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Create New Execution
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showNewExecutionModal && (
        <NewExecutionModal
          onClose={() => setShowNewExecutionModal(false)}
          onSubmit={handleNewExecution}
          loading={startingExecution}
        />
      )}

      {selectedStage && (
        <StageDetailModal
          stage={selectedStage}
          execution={currentExecution}
          onClose={() => setSelectedStageId(null)}
        />
      )}
    </div>
  );
}

export default App;