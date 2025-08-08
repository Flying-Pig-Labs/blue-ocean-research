# Proposed API Enhancements

## Current State
The API currently has 2 endpoints:
- `POST /submit` - Submit a pipeline job
- `GET /logs/{researchId}` - Get logs for a research job

## Proposed Enhancements

### Critical Additions

#### 1. Enhanced POST /submit with Conflict Detection
**Why**: Prevent duplicate jobs from running simultaneously
```python
# Check for existing running jobs before submission
# Return 409 Conflict if job already running
# Add "force" flag to override
```

#### 2. GET /status/{jobId}
**Why**: Direct status lookup without needing researchId
- Faster status checks
- Direct job tracking
- Runtime metrics

#### 3. GET /results/{researchId}
**Why**: Retrieve pipeline outputs from S3
- Presigned URLs for secure downloads
- List all output files
- No need for direct S3 access

#### 4. GET /health
**Why**: System monitoring and alerting
- Check DynamoDB status
- Check Batch queue status
- Overall system health

### Nice-to-Have Additions

#### 5. GET /jobs
**Why**: View all jobs with filtering
- Pagination support
- Filter by status or researchId
- Historical job tracking

#### 6. DELETE /jobs/{jobId}
**Why**: Cancel running jobs
- Stop long-running pipelines
- Clean up stuck jobs
- Save compute costs

### Future Enhancements

#### 7. Rate Limiting
- API Gateway throttling
- Prevent abuse
- 10 req/sec per IP

#### 8. Webhook Support
- POST callbacks on job completion
- Event-driven architecture
- Real-time notifications

#### 9. Authentication
- API Key authentication
- JWT tokens for users
- Role-based access control

## Implementation Notes

To implement these enhancements:
1. Update the CDK stack with new Lambda functions
2. Add new API Gateway routes
3. Grant appropriate IAM permissions
4. Update DynamoDB schemas if needed
5. Test thoroughly before deployment

## Deployment Considerations

- These changes are backward compatible
- No breaking changes to existing endpoints
- Can be rolled out incrementally
- Monitor CloudWatch after deployment