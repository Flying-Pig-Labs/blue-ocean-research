const AWS = require('aws-sdk');
const https = require('https');
const crypto = require('crypto');
const urlParse = require('url').URL;

const GRAPHQL_API_URL = process.env.GRAPHQL_API_URL;
const GRAPHQL_API_ID = process.env.GRAPHQL_API_ID;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize AWS SDK
const credentials = new AWS.SharedIniFileCredentials({profile: process.env.AWS_PROFILE || 'default'});
AWS.config.credentials = credentials;
AWS.config.region = AWS_REGION;

/**
 * Process DynamoDB stream events and trigger GraphQL subscriptions
 */
exports.handler = async (event) => {
    console.log('Stream processor event:', JSON.stringify(event, null, 2));
    
    try {
        // Process each DynamoDB stream record
        for (const record of event.Records) {
            await processStreamRecord(record);
        }
        
        return {
            statusCode: 200,
            body: 'Successfully processed stream records'
        };
        
    } catch (error) {
        console.error('Stream processor error:', error);
        throw error;
    }
};

/**
 * Process individual DynamoDB stream record
 */
async function processStreamRecord(record) {
    const { eventName, dynamodb } = record;
    
    console.log(`Processing ${eventName} event for key:`, dynamodb.Keys);
    
    // Only process MODIFY events (INSERT and REMOVE less relevant for progress updates)
    if (eventName !== 'MODIFY') {
        console.log(`Skipping ${eventName} event`);
        return;
    }
    
    // Extract job data from DynamoDB image
    const newImage = dynamodb.NewImage;
    if (!newImage) {
        console.log('No new image in record');
        return;
    }
    
    // Convert DynamoDB image to regular object
    const jobData = unmarshallDynamoDBImage(newImage);
    
    // Transform to GraphQL format
    const executionUpdate = transformToExecutionUpdate(jobData);
    
    // Trigger GraphQL subscriptions
    await triggerSubscriptions(executionUpdate);
}

/**
 * Unmarshal DynamoDB image to regular JavaScript object
 */
function unmarshallDynamoDBImage(image) {
    const unmarshall = AWS.DynamoDB.Converter.unmarshall;
    return unmarshall(image);
}

/**
 * Transform job data to ExecutionUpdate format
 */
function transformToExecutionUpdate(jobData) {
    return {
        jobId: jobData.jobId,
        status: jobData.status,
        currentStage: jobData.currentStage || 0,
        stageName: jobData.stageName || 'Unknown',
        stageProgress: jobData.stageProgress || 0,
        overallProgress: jobData.overallProgress || 0,
        estimatedRemainingMinutes: jobData.estimatedRemainingMinutes || 0,
        completedStages: (jobData.stages || []).map((stage, index) => ({
            stageId: index + 1,
            name: stage.name,
            status: stage.status || 'PENDING',
            progress: stage.progress || 0,
            startedAt: stage.startedAt,
            completedAt: stage.completedAt,
            estimatedMinutes: stage.estimatedMinutes || 0,
            actualMinutes: stage.actualMinutes,
            outputs: stage.outputs || [],
            error: stage.error,
            metadata: stage.metadata
        })),
        currentStageUpdate: jobData.currentStage && jobData.stages && jobData.stages[jobData.currentStage - 1] ? {
            stageId: jobData.currentStage,
            name: jobData.stages[jobData.currentStage - 1].name,
            status: jobData.stages[jobData.currentStage - 1].status || 'RUNNING',
            progress: jobData.stageProgress || 0,
            startedAt: jobData.stages[jobData.currentStage - 1].startedAt,
            completedAt: jobData.stages[jobData.currentStage - 1].completedAt,
            estimatedMinutes: jobData.stages[jobData.currentStage - 1].estimatedMinutes || 0,
            actualMinutes: jobData.stages[jobData.currentStage - 1].actualMinutes,
            outputs: jobData.stages[jobData.currentStage - 1].outputs || [],
            error: jobData.stages[jobData.currentStage - 1].error,
            metadata: jobData.stages[jobData.currentStage - 1].metadata
        } : null,
        error: jobData.errorMessage,
        timestamp: jobData.updatedAt || jobData.createdAt,
        metadata: {
            researchDocId: jobData.researchDocId,
            username: jobData.username,
            startedAt: jobData.createdAt,
            completedAt: jobData.completedAt,
            totalStages: 7,
            estimatedTotalMinutes: jobData.estimatedTotalMinutes || 22,
            actualDurationMinutes: jobData.actualDurationMinutes,
            pipelineVersion: (jobData.metadata && jobData.metadata.pipelineVersion) || '1.0.0'
        },
        results: {
            githubRepoUrl: jobData.results && jobData.results.githubRepoUrl,
            githubRepoName: jobData.results && jobData.results.githubRepoName,
            issuesCreated: jobData.results && jobData.results.issuesCreated || 0,
            analysisResults: jobData.results && jobData.results.analysisResults,
            finalPortfolio: jobData.results && jobData.results.finalPortfolio
        }
    };
}

/**
 * Trigger GraphQL subscriptions by calling mutations
 */
async function triggerSubscriptions(executionUpdate) {
    try {
        // Mutation to trigger onExecutionUpdate subscription
        const mutation = `
            mutation TriggerExecutionUpdate($input: UpdateStageProgressInput!) {
                updateStageProgress(input: $input) {
                    jobId
                    status
                    currentStage
                    stageName
                    stageProgress
                    overallProgress
                    timestamp
                }
            }
        `;
        
        const variables = {
            input: {
                jobId: executionUpdate.jobId,
                stageId: executionUpdate.currentStage,
                progress: executionUpdate.stageProgress,
                status: executionUpdate.currentStageUpdate ? executionUpdate.currentStageUpdate.status : 'RUNNING'
            }
        };
        
        // Make signed GraphQL request
        await makeSignedGraphQLRequest(mutation, variables);
        
        console.log(`Triggered subscription for job ${executionUpdate.jobId}`);
        
    } catch (error) {
        console.error('Error triggering subscriptions:', error);
        // Don't throw - we don't want to fail stream processing if subscription fails
    }
}

/**
 * Make a signed GraphQL request to AppSync
 */
async function makeSignedGraphQLRequest(query, variables = {}) {
    const requestBody = JSON.stringify({ query, variables });
    
    // Parse the GraphQL URL
    const url = new urlParse(GRAPHQL_API_URL);
    const host = url.hostname;
    const path = url.pathname;
    
    // AWS signature version 4
    const service = 'appsync';
    const method = 'POST';
    const endpoint = `https://${host}`;
    
    // Create the request
    const request = {
        method,
        url: endpoint + path,
        body: requestBody,
        headers: {
            'Content-Type': 'application/json',
            'host': host
        }
    };
    
    // Sign the request
    const signer = new AWS.Signers.V4(request, service);
    signer.addAuthorization(AWS.config.credentials, new Date());
    
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: host,
            path: path,
            method: method,
            headers: request.headers
        }, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const response = JSON.parse(data);
                    if (response.errors) {
                        console.error('GraphQL errors:', response.errors);
                        reject(new Error(JSON.stringify(response.errors)));
                    } else {
                        resolve(response.data);
                    }
                } catch (error) {
                    reject(error);
                }
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        req.write(requestBody);
        req.end();
    });
}