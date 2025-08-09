/**
 * GraphQL type definitions for the multi-step pipeline
 */

export type ExecutionStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
export type StageStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';

export interface ExecutionUpdate {
  jobId: string;
  status: ExecutionStatus;
  currentStage: number;
  stageName: string;
  stageProgress: number;
  overallProgress: number;
  estimatedRemainingMinutes?: number;
  completedStages: StageUpdate[];
  currentStageUpdate?: StageUpdate;
  error?: string;
  timestamp: string;
  metadata?: ExecutionMetadata;
  results?: ExecutionResults;
}

export interface StageUpdate {
  stageId: number;
  name: string;
  status: StageStatus;
  progress: number;
  startedAt?: string;
  completedAt?: string;
  estimatedMinutes: number;
  actualMinutes?: number;
  outputs: StageOutput[];
  error?: string;
  metadata?: any;
}

export interface StageOutput {
  fileName: string;
  fileSize: number;
  contentPreview: string;
  s3Location?: string;
  generatedAt: string;
}

export interface ExecutionMetadata {
  researchDocId: string;
  username: string;
  startedAt: string;
  completedAt?: string;
  totalStages: number;
  estimatedTotalMinutes: number;
  actualDurationMinutes?: number;
  pipelineVersion: string;
}

export interface ExecutionResults {
  githubRepoUrl?: string;
  githubRepoName?: string;
  issuesCreated: number;
  analysisResults?: any;
  finalPortfolio?: any;
}

export interface ExecutionConnection {
  items: ExecutionUpdate[];
  nextToken?: string;
}

// Input types for mutations
export interface StartExecutionInput {
  researchDocId: string;
  username: string;
  pipelineConfig?: any;
}

export interface UpdateStageProgressInput {
  jobId: string;
  stageId: number;
  progress: number;
  status?: StageStatus;
  outputs?: StageOutputInput[];
  metadata?: any;
}

export interface StageOutputInput {
  fileName: string;
  fileSize: number;
  contentPreview: string;
  s3Location?: string;
}

// GraphQL operation types
export interface GraphQLResponse<T> {
  data?: T;
  errors?: Array<{
    message: string;
    locations?: Array<{
      line: number;
      column: number;
    }>;
    path?: string[];
    extensions?: any;
  }>;
}

// Query result types
export interface GetExecutionResponse {
  getExecution: ExecutionUpdate;
}

export interface ListExecutionsResponse {
  listExecutions: ExecutionConnection;
}

export interface GetExecutionHistoryResponse {
  getExecutionHistory: ExecutionUpdate[];
}

// Mutation result types
export interface StartExecutionResponse {
  startExecution: ExecutionUpdate;
}

export interface CancelExecutionResponse {
  cancelExecution: ExecutionUpdate;
}

export interface UpdateStageProgressResponse {
  updateStageProgress: ExecutionUpdate;
}

// Subscription result types
export interface OnExecutionUpdateSubscription {
  onExecutionUpdate: ExecutionUpdate;
}

export interface OnStageCompleteSubscription {
  onStageComplete: StageUpdate;
}

export interface OnExecutionStatusChangeSubscription {
  onExecutionStatusChange: ExecutionUpdate;
}

// Configuration types
export interface GraphQLConfig {
  url: string;
  apiKey: string;
  region?: string;
}

// Component prop types
export interface PipelineStageNodeData {
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
  outputs?: StageOutput[];
}

// Hook result types
export interface GraphQLSubscriptionResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
}

export interface GraphQLQueryResult<T> extends GraphQLSubscriptionResult<T> {
  refetch: () => Promise<void>;
}

export interface GraphQLMutationResult<T> {
  executeMutation: (mutation: string, variables?: Record<string, any>) => Promise<T>;
  loading: boolean;
  error: Error | null;
}

// WebSocket message types
export interface GraphQLWebSocketMessage {
  id?: string;
  type: 'connection_init' | 'connection_ack' | 'connection_error' | 'start' | 'data' | 'error' | 'complete' | 'stop' | 'ka';
  payload?: any;
}

// Real-time update event types
export interface PipelineProgressEvent {
  jobId: string;
  stage: number;
  progress: number;
  status: StageStatus;
  timestamp: string;
  outputs?: StageOutput[];
}

export interface PipelineStatusChangeEvent {
  jobId: string;
  status: ExecutionStatus;
  timestamp: string;
  error?: string;
  results?: ExecutionResults;
}

// Utility types for stage definitions
export interface StageDefinition {
  id: number;
  name: string;
  description: string;
  estimatedMinutes: number;
  inputs: string[];
  outputs: string[];
  dependencies: number[];
}

export const PIPELINE_STAGES: StageDefinition[] = [
  {
    id: 1,
    name: 'Research Analysis',
    description: 'Analyze market research with parallel LLM processing',
    estimatedMinutes: 2,
    inputs: ['Research Document'],
    outputs: ['Analysis Results', 'Pain Points', 'Personas', 'Verticals'],
    dependencies: [],
  },
  {
    id: 2,
    name: 'JTBD Research',
    description: 'Extract Jobs-to-be-Done from real-world sources',
    estimatedMinutes: 3,
    inputs: ['Analysis Results'],
    outputs: ['JTBD Research', 'Pain Points List'],
    dependencies: [1],
  },
  {
    id: 3,
    name: 'Pain Point Clustering',
    description: 'Cluster pain points using ML and generate opportunity zones',
    estimatedMinutes: 1,
    inputs: ['Pain Points List'],
    outputs: ['Opportunity Zones', 'Cluster Analysis'],
    dependencies: [2],
  },
  {
    id: 4,
    name: 'Value Curve Mapping',
    description: 'Map competitive value curves and identify disruption opportunities',
    estimatedMinutes: 5,
    inputs: ['Opportunity Zones'],
    outputs: ['Value Curves', 'Strategic Insights'],
    dependencies: [3],
  },
  {
    id: 5,
    name: 'Product Idea Generation',
    description: 'Generate innovative product ideas using ERRC framework',
    estimatedMinutes: 8,
    inputs: ['Value Curves'],
    outputs: ['Product Ideas', 'Viability Scores'],
    dependencies: [4],
  },
  {
    id: 6,
    name: 'Idea Consolidation',
    description: 'Consolidate ideas into comprehensive innovation portfolio',
    estimatedMinutes: 1,
    inputs: ['Product Ideas'],
    outputs: ['Innovation Portfolio', 'Summary Report'],
    dependencies: [5],
  },
  {
    id: 7,
    name: 'GitHub Integration',
    description: 'Create GitHub repository with issues and documentation',
    estimatedMinutes: 2,
    inputs: ['Innovation Portfolio'],
    outputs: ['GitHub Repository', 'Issues Created', 'Documentation'],
    dependencies: [5], // Can run in parallel with stage 6
  },
];

// Error types
export class GraphQLError extends Error {
  public extensions?: any;
  public locations?: Array<{ line: number; column: number }>;
  public path?: string[];

  constructor(
    message: string,
    extensions?: any,
    locations?: Array<{ line: number; column: number }>,
    path?: string[]
  ) {
    super(message);
    this.name = 'GraphQLError';
    this.extensions = extensions;
    this.locations = locations;
    this.path = path;
  }
}

export class WebSocketConnectionError extends Error {
  public code?: number;
  public reason?: string;

  constructor(message: string, code?: number, reason?: string) {
    super(message);
    this.name = 'WebSocketConnectionError';
    this.code = code;
    this.reason = reason;
  }
}