const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const lambda = new AWS.Lambda();
const appsync = new AWS.AppSync();

const JOBS_TABLE = process.env.JOBS_TABLE;
const ENVIRONMENT = process.env.ENVIRONMENT || 'production';

/**
 * GraphQL resolver handler for complex operations
 */
exports.handler = async (event) => {
    console.log('Resolver event:', JSON.stringify(event, null, 2));
    
    try {
        const { field, arguments: args, identity } = event;
        
        switch (field) {
            case 'listExecutions':
                return await listExecutions(args);
            case 'startExecution':
                return await startExecution(args, identity);
            case 'updateStageProgress':
                return await updateStageProgress(args, identity);
            case 'cancelExecution':
                return await cancelExecution(args, identity);
            default:
                throw new Error(`Unknown field: ${field}`);
        }
    } catch (error) {
        console.error('Resolver error:', error);
        throw error;
    }
};

/**
 * List executions with pagination and filtering
 */
async function listExecutions(args) {
    const { username, status, limit = 20, nextToken } = args;
    
    try {
        let params = {
            TableName: JOBS_TABLE,
            Limit: limit
        };
        
        // Add pagination token if provided
        if (nextToken) {
            params.ExclusiveStartKey = JSON.parse(Buffer.from(nextToken, 'base64').toString());
        }
        
        // If filtering by username, use a GSI or scan with filter
        if (username) {
            params.FilterExpression = '#username = :username';
            params.ExpressionAttributeNames = {
                '#username': 'username'
            };
            params.ExpressionAttributeValues = {
                ':username': username
            };
            
            if (status) {
                params.FilterExpression += ' AND #status = :status';
                params.ExpressionAttributeNames['#status'] = 'status';
                params.ExpressionAttributeValues[':status'] = status;
            }
        } else if (status) {
            params.FilterExpression = '#status = :status';
            params.ExpressionAttributeNames = {
                '#status': 'status'
            };
            params.ExpressionAttributeValues = {
                ':status': status
            };
        }
        
        const result = await dynamodb.scan(params).promise();
        
        // Transform items to match GraphQL schema
        const items = result.Items.map(transformExecutionUpdate);
        
        // Create next token if there are more items
        let responseNextToken = null;
        if (result.LastEvaluatedKey) {
            responseNextToken = Buffer.from(JSON.stringify(result.LastEvaluatedKey)).toString('base64');
        }
        
        return {
            items,
            nextToken: responseNextToken
        };
        
    } catch (error) {
        console.error('Error listing executions:', error);
        throw error;
    }
}

/**
 * Start a new execution
 */
async function startExecution(args, identity) {
    const { input } = args;
    const { researchDocId, username, pipelineConfig } = input;
    
    try {
        // Check for existing running job
        const existingJob = await checkExistingJob(researchDocId, username);
        if (existingJob) {
            throw new Error(`Pipeline already running for research document ${researchDocId}`);
        }
        
        // Generate job ID
        const jobId = `job-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${uuidv4().slice(0, 8)}`;
        const now = new Date().toISOString();
        
        // Create job record
        const jobRecord = {
            jobId,
            researchDocId,
            username,
            status: 'QUEUED',
            currentStage: 0,
            stageName: 'Initializing',
            stageProgress: 0.0,
            overallProgress: 0.0,
            estimatedRemainingMinutes: 22,
            createdAt: now,
            updatedAt: now,
            ttl: Math.floor((Date.now() / 1000) + (30 * 24 * 60 * 60)), // 30 days
            stages: [
                { name: 'Research Analysis', status: 'PENDING', estimatedMinutes: 2 },
                { name: 'JTBD Research', status: 'PENDING', estimatedMinutes: 3 },
                { name: 'Pain Point Clustering', status: 'PENDING', estimatedMinutes: 1 },
                { name: 'Value Curve Mapping', status: 'PENDING', estimatedMinutes: 5 },
                { name: 'Product Idea Generation', status: 'PENDING', estimatedMinutes: 8 },
                { name: 'Idea Consolidation', status: 'PENDING', estimatedMinutes: 1 },
                { name: 'GitHub Repository Creation', status: 'PENDING', estimatedMinutes: 2 }
            ],
            metadata: {
                researchDocId,
                username,
                startedAt: now,
                totalStages: 7,
                estimatedTotalMinutes: 22,
                pipelineVersion: '1.0.0'
            },
            results: {
                githubRepoUrl: null,
                githubRepoName: null,
                issuesCreated: 0,
                analysisResults: null,
                finalPortfolio: null
            }
        };
        
        // Store in DynamoDB
        await dynamodb.put({
            TableName: JOBS_TABLE,
            Item: jobRecord
        }).promise();
        
        // Start the orchestrator Lambda
        await lambda.invoke({
            FunctionName: `pipeline-orchestrator-${ENVIRONMENT}`,
            InvocationType: 'Event',
            Payload: JSON.stringify({
                jobId,
                researchDocId,
                username,
                action: 'start_pipeline'
            })
        }).promise();
        
        return transformExecutionUpdate(jobRecord);
        
    } catch (error) {
        console.error('Error starting execution:', error);
        throw error;
    }
}

/**
 * Update stage progress with real-time subscription trigger
 */
async function updateStageProgress(args, identity) {
    const { input } = args;
    const { jobId, stageId, progress, status, outputs, metadata } = input;
    
    try {
        const now = new Date().toISOString();
        
        // Get current job
        const currentJob = await dynamodb.get({
            TableName: JOBS_TABLE,
            Key: { jobId }
        }).promise();
        
        if (!currentJob.Item) {
            throw new Error(`Job ${jobId} not found`);
        }
        
        const job = currentJob.Item;
        
        // Update stage information
        const stages = [...job.stages];
        if (stages[stageId - 1]) {
            stages[stageId - 1] = {
                ...stages[stageId - 1],
                progress: progress || 0,
                status: status || 'RUNNING'
            };
            
            // If stage is completed, set completion time
            if (status === 'COMPLETED') {
                stages[stageId - 1].completedAt = now;
                
                // Calculate actual duration
                if (stages[stageId - 1].startedAt) {
                    const startTime = new Date(stages[stageId - 1].startedAt);
                    const endTime = new Date(now);
                    stages[stageId - 1].actualMinutes = Math.round((endTime - startTime) / (1000 * 60));
                }
            }
            
            // Add outputs if provided
            if (outputs && outputs.length > 0) {
                stages[stageId - 1].outputs = outputs.map(output => ({
                    ...output,
                    generatedAt: now
                }));
            }
        }
        
        // Calculate overall progress
        const completedStages = stages.filter(s => s.status === 'COMPLETED').length;
        const overallProgress = (completedStages / stages.length) * 100;
        
        // Update DynamoDB item
        const updateParams = {
            TableName: JOBS_TABLE,
            Key: { jobId },
            UpdateExpression: 'SET #stages = :stages, currentStage = :currentStage, stageName = :stageName, stageProgress = :stageProgress, overallProgress = :overallProgress, updatedAt = :updatedAt',
            ExpressionAttributeNames: {
                '#stages': 'stages'
            },
            ExpressionAttributeValues: {
                ':stages': stages,
                ':currentStage': stageId,
                ':stageName': stages[stageId - 1]?.name || 'Unknown Stage',
                ':stageProgress': progress || 0,
                ':overallProgress': overallProgress,
                ':updatedAt': now
            },
            ReturnValues: 'ALL_NEW'
        };
        
        // Add metadata updates if provided
        if (metadata) {
            updateParams.UpdateExpression += ', #metadata = :metadata';
            updateParams.ExpressionAttributeNames['#metadata'] = 'metadata';
            updateParams.ExpressionAttributeValues[':metadata'] = {
                ...job.metadata,
                ...metadata
            };
        }
        
        const result = await dynamodb.update(updateParams).promise();
        
        return transformExecutionUpdate(result.Attributes);
        
    } catch (error) {
        console.error('Error updating stage progress:', error);
        throw error;
    }
}

/**
 * Cancel a running execution
 */
async function cancelExecution(args, identity) {
    const { jobId } = args;
    
    try {
        const now = new Date().toISOString();
        
        const result = await dynamodb.update({
            TableName: JOBS_TABLE,
            Key: { jobId },
            UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt',
            ExpressionAttributeNames: {
                '#status': 'status'
            },
            ExpressionAttributeValues: {
                ':status': 'CANCELLED',
                ':updatedAt': now
            },
            ReturnValues: 'ALL_NEW'
        }).promise();
        
        return transformExecutionUpdate(result.Attributes);
        
    } catch (error) {
        console.error('Error cancelling execution:', error);
        throw error;
    }
}

/**
 * Check for existing running job
 */
async function checkExistingJob(researchDocId, username) {
    try {
        const params = {
            TableName: JOBS_TABLE,
            FilterExpression: 'researchDocId = :docId AND username = :user AND (#status = :running OR #status = :queued)',
            ExpressionAttributeNames: {
                '#status': 'status'
            },
            ExpressionAttributeValues: {
                ':docId': researchDocId,
                ':user': username,
                ':running': 'RUNNING',
                ':queued': 'QUEUED'
            }
        };
        
        const result = await dynamodb.scan(params).promise();
        
        if (result.Items && result.Items.length > 0) {
            // Return the most recent job
            return result.Items.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))[0];
        }
        
        return null;
    } catch (error) {
        console.error('Error checking existing job:', error);
        return null;
    }
}

/**
 * Transform DynamoDB item to GraphQL ExecutionUpdate format
 */
function transformExecutionUpdate(item) {
    if (!item) return null;
    
    return {
        jobId: item.jobId,
        status: item.status,
        currentStage: item.currentStage || 0,
        stageName: item.stageName || 'Unknown',
        stageProgress: item.stageProgress || 0,
        overallProgress: item.overallProgress || 0,
        estimatedRemainingMinutes: item.estimatedRemainingMinutes || 0,
        completedStages: (item.stages || [])
            .map((stage, index) => ({
                stageId: index + 1,
                name: stage.name,
                status: stage.status || 'PENDING',
                progress: stage.progress || 0,
                startedAt: stage.startedAt || null,
                completedAt: stage.completedAt || null,
                estimatedMinutes: stage.estimatedMinutes || 0,
                actualMinutes: stage.actualMinutes || null,
                outputs: stage.outputs || [],
                error: stage.error || null,
                metadata: stage.metadata || null
            })),
        currentStageUpdate: item.currentStage && item.stages && item.stages[item.currentStage - 1] ? {
            stageId: item.currentStage,
            name: item.stages[item.currentStage - 1].name,
            status: item.stages[item.currentStage - 1].status || 'RUNNING',
            progress: item.stageProgress || 0,
            startedAt: item.stages[item.currentStage - 1].startedAt || null,
            completedAt: item.stages[item.currentStage - 1].completedAt || null,
            estimatedMinutes: item.stages[item.currentStage - 1].estimatedMinutes || 0,
            actualMinutes: item.stages[item.currentStage - 1].actualMinutes || null,
            outputs: item.stages[item.currentStage - 1].outputs || [],
            error: item.stages[item.currentStage - 1].error || null,
            metadata: item.stages[item.currentStage - 1].metadata || null
        } : null,
        error: item.errorMessage || null,
        timestamp: item.updatedAt || item.createdAt,
        metadata: {
            researchDocId: item.researchDocId,
            username: item.username,
            startedAt: item.createdAt,
            completedAt: item.completedAt || null,
            totalStages: 7,
            estimatedTotalMinutes: item.estimatedTotalMinutes || 22,
            actualDurationMinutes: item.actualDurationMinutes || null,
            pipelineVersion: (item.metadata && item.metadata.pipelineVersion) || '1.0.0'
        },
        results: {
            githubRepoUrl: item.results && item.results.githubRepoUrl,
            githubRepoName: item.results && item.results.githubRepoName,
            issuesCreated: item.results && item.results.issuesCreated || 0,
            analysisResults: item.results && item.results.analysisResults,
            finalPortfolio: item.results && item.results.finalPortfolio
        }
    };
}