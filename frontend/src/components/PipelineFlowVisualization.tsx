/**
 * Pipeline Flow Visualization Component - ReactFlow-based Pipeline Diagram
 * 
 * Purpose: Renders an interactive flow diagram of the 7-stage innovation pipeline,
 *          showing real-time progress, stage connections, and execution status.
 * 
 * This component creates a visual representation of the pipeline execution using
 * ReactFlow library. It subscribes to GraphQL for real-time updates and animates
 * the flow as stages complete. Each stage is clickable for detailed information.
 * 
 * Key Features:
 * 1. Real-time stage status updates via GraphQL subscription
 * 2. Animated edges showing active data flow
 * 3. Color-coded stage nodes (pending, running, completed, failed)
 * 4. Progress bars and time estimates for each stage
 * 5. Interactive nodes with click handlers for details
 * 
 * Pipeline Structure:
 * - Stage 1: Research Analysis (parallel LLM processing)
 * - Stage 2: JTBD Research (Reddit API integration)
 * - Stage 3: Pain Point Clustering (ML clustering)
 * - Stage 4: Value Curve Mapping (competitive analysis)
 * - Stage 5: Product Idea Generation (ERRC framework)
 * - Stage 6: Idea Consolidation (portfolio creation)
 * - Stage 7: GitHub Integration (repository creation)
 * 
 * Visual Design:
 * - Nodes arranged in logical flow pattern
 * - Smoothstep edges for clean connections
 * - Animated edges for active transitions
 * - Color coding: gray (pending), blue (running), green (completed), red (failed)
 * 
 * @component
 * @author Multi-Step LLM Pipeline Team
 * @version 2.0.0
 * @date January 2025
 */

import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useGraphQLSubscription } from '../hooks/useGraphQLSubscription';
import { PipelineStageNode } from './PipelineStageNode';
import { ExecutionUpdate, StageStatus } from '../types/graphql';

// Custom node type registration for pipeline stages
// PipelineStageNode is a custom component that renders stage details
const nodeTypes: NodeTypes = {
  pipelineStage: PipelineStageNode,
};

interface PipelineFlowVisualizationProps {
  jobId: string;                           // AWS Batch job ID to monitor
  onStageClick?: (stageId: number) => void; // Callback when stage node is clicked
}

// Initial node configuration for the 7-stage pipeline
// Positions are carefully calculated for optimal visual flow
// Each node contains metadata about the stage including estimates and I/O
const initialNodes: Node[] = [
  {
    id: 'stage-1',
    type: 'pipelineStage',
    position: { x: 100, y: 100 },
    data: {
      stageId: 1,
      name: 'Research Analysis',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 2,
      description: 'Analyze market research with parallel LLM processing',
      inputs: ['Research Document'],
      outputs: ['Analysis Results', 'Pain Points', 'Personas', 'Verticals']
    },
  },
  {
    id: 'stage-2',
    type: 'pipelineStage',
    position: { x: 400, y: 100 },
    data: {
      stageId: 2,
      name: 'JTBD Research',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 3,
      description: 'Extract Jobs-to-be-Done from real-world sources',
      inputs: ['Analysis Results'],
      outputs: ['JTBD Research', 'Pain Points List']
    },
  },
  {
    id: 'stage-3',
    type: 'pipelineStage',
    position: { x: 700, y: 100 },
    data: {
      stageId: 3,
      name: 'Pain Point Clustering',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 1,
      description: 'Cluster pain points using ML and generate opportunity zones',
      inputs: ['Pain Points List'],
      outputs: ['Opportunity Zones', 'Cluster Analysis']
    },
  },
  {
    id: 'stage-4',
    type: 'pipelineStage',
    position: { x: 1000, y: 100 },
    data: {
      stageId: 4,
      name: 'Value Curve Mapping',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 5,
      description: 'Map competitive value curves and identify disruption opportunities',
      inputs: ['Opportunity Zones'],
      outputs: ['Value Curves', 'Strategic Insights']
    },
  },
  {
    id: 'stage-5',
    type: 'pipelineStage',
    position: { x: 550, y: 350 },
    data: {
      stageId: 5,
      name: 'Product Idea Generation',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 8,
      description: 'Generate innovative product ideas using ERRC framework',
      inputs: ['Value Curves'],
      outputs: ['Product Ideas', 'Viability Scores']
    },
  },
  {
    id: 'stage-6',
    type: 'pipelineStage',
    position: { x: 250, y: 350 },
    data: {
      stageId: 6,
      name: 'Idea Consolidation',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 1,
      description: 'Consolidate ideas into comprehensive innovation portfolio',
      inputs: ['Product Ideas'],
      outputs: ['Innovation Portfolio', 'Summary Report']
    },
  },
  {
    id: 'stage-7',
    type: 'pipelineStage',
    position: { x: 850, y: 350 },
    data: {
      stageId: 7,
      name: 'GitHub Integration',
      status: 'PENDING' as StageStatus,
      progress: 0,
      estimatedMinutes: 2,
      description: 'Create GitHub repository with issues and documentation',
      inputs: ['Innovation Portfolio'],
      outputs: ['GitHub Repository', 'Issues Created', 'Documentation']
    },
  },
];

// Edge configuration connecting pipeline stages
// Uses smoothstep type for aesthetic curved connections
// Animation is controlled dynamically based on execution state
const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: 'stage-1',
    target: 'stage-2',
    type: 'smoothstep',
    animated: false,
  },
  {
    id: 'e2-3',
    source: 'stage-2',
    target: 'stage-3',
    type: 'smoothstep',
    animated: false,
  },
  {
    id: 'e3-4',
    source: 'stage-3',
    target: 'stage-4',
    type: 'smoothstep',
    animated: false,
  },
  {
    id: 'e4-5',
    source: 'stage-4',
    target: 'stage-5',
    type: 'smoothstep',
    animated: false,
  },
  {
    id: 'e5-6',
    source: 'stage-5',
    target: 'stage-6',
    type: 'smoothstep',
    animated: false,
  },
  {
    id: 'e5-7',
    source: 'stage-5',
    target: 'stage-7',
    type: 'smoothstep',
    animated: false,
  },
];

export const PipelineFlowVisualization: React.FC<PipelineFlowVisualizationProps> = ({
  jobId,
  onStageClick,
}) => {
  // ReactFlow state management for nodes and edges
  // Nodes represent pipeline stages, edges represent data flow
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  // Local state for execution updates from GraphQL subscription
  const [executionUpdate, setExecutionUpdate] = useState<ExecutionUpdate | null>(null);

  // GraphQL subscription for real-time pipeline updates
  // Receives updates every time a stage progresses or completes
  // Includes stage outputs, errors, and timing information
  const { data: subscriptionData, error: subscriptionError } = useGraphQLSubscription(
    `
    subscription OnExecutionUpdate($jobId: ID!) {
      onExecutionUpdate(jobId: $jobId) {
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
          startedAt
          completedAt
          actualDurationMinutes
        }
        results {
          githubRepoUrl
          githubRepoName
          issuesCreated
        }
      }
    }
    `,
    { jobId }
  );

  /**
   * Effect to update visual state when subscription data changes.
   * Updates node status, progress, and outputs based on execution state.
   * Also animates edges between completed and running stages.
   */
  useEffect(() => {
    if (subscriptionData?.onExecutionUpdate) {
      const update = subscriptionData.onExecutionUpdate;
      setExecutionUpdate(update);

      // Update node data with latest execution information
      // Each node's visual state reflects its execution status
      setNodes((prevNodes) =>
        prevNodes.map((node) => {
          const stageId = parseInt(node.id.split('-')[1]); // Extract numeric stage ID
          const stageUpdate = update.completedStages.find(s => s.stageId === stageId);
          
          // Update completed stages with final data
          if (stageUpdate) {
            return {
              ...node,
              data: {
                ...node.data,
                status: stageUpdate.status,
                progress: stageUpdate.progress,
                actualMinutes: stageUpdate.actualMinutes,
                outputs: stageUpdate.outputs,
                error: stageUpdate.error,
                startedAt: stageUpdate.startedAt,
                completedAt: stageUpdate.completedAt,
              },
            };
          }
          
          // Update currently running stage with live progress
          // Shows intermediate outputs and progress percentage
          if (stageId === update.currentStage && update.currentStageUpdate) {
            return {
              ...node,
              data: {
                ...node.data,
                status: update.currentStageUpdate.status,
                progress: update.currentStageUpdate.progress,
                outputs: update.currentStageUpdate.outputs,
              },
            };
          }
          
          return node;
        })
      );

      // Dynamic edge styling based on pipeline flow
      // Animates edges between completed source and running target
      // Changes color to green for completed connections
      setEdges((prevEdges) =>
        prevEdges.map((edge) => {
          const sourceStageId = parseInt(edge.source.split('-')[1]);
          const targetStageId = parseInt(edge.target.split('-')[1]);
          
          const sourceCompleted = update.completedStages.some(
            s => s.stageId === sourceStageId && s.status === 'COMPLETED'
          );
          const targetRunning = targetStageId === update.currentStage;
          
          return {
            ...edge,
            animated: sourceCompleted && targetRunning,
            style: {
              ...edge.style,
              stroke: sourceCompleted ? '#10b981' : '#94a3b8',
              strokeWidth: sourceCompleted ? 2 : 1,
            },
          };
        })
      );
    }
  }, [subscriptionData, setNodes, setEdges]);

  /**
   * Handle new edge connections (not used in production).
   * Included for ReactFlow completeness but pipeline has fixed topology.
   */
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  /**
   * Handle clicks on stage nodes to show detailed information.
   * Extracts stage ID from node ID and triggers parent callback.
   * 
   * @param event - Mouse event (unused)
   * @param node - Clicked node containing stage data
   */
  const handleNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      const stageId = parseInt(node.id.split('-')[1]);
      onStageClick?.(stageId); // Trigger parent component's handler
    },
    [onStageClick]
  );

  return (
    <div className="h-full w-full">
      <div className="mb-4 p-4 bg-white rounded-lg shadow">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Pipeline Execution: {jobId}
            </h2>
            {executionUpdate && (
              <div className="mt-2 flex items-center space-x-4">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  executionUpdate.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                  executionUpdate.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                  executionUpdate.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {executionUpdate.status}
                </span>
                <span className="text-sm text-gray-600">
                  Stage {executionUpdate.currentStage}/7: {executionUpdate.stageName}
                </span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${executionUpdate.overallProgress}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-600">
                    {Math.round(executionUpdate.overallProgress)}%
                  </span>
                </div>
                {executionUpdate.estimatedRemainingMinutes > 0 && (
                  <span className="text-sm text-gray-500">
                    ~{executionUpdate.estimatedRemainingMinutes}min remaining
                  </span>
                )}
              </div>
            )}
          </div>
          {executionUpdate?.results?.githubRepoUrl && (
            <a
              href={executionUpdate.results.githubRepoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              View GitHub Repository
            </a>
          )}
        </div>
      </div>
      
      <div className="flex-1 bg-gray-50 rounded-lg">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <Background color="#f3f4f6" gap={16} />
        </ReactFlow>
      </div>
      
      {subscriptionError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="text-red-800">
            <strong>Subscription Error:</strong> {subscriptionError.message}
          </div>
        </div>
      )}
    </div>
  );
};