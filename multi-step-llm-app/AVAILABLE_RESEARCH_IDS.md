# Available Research IDs for Testing

## Working Research Reports in S3

The following research IDs have `report.md` files and can be used for testing the pipeline:

### Red Team Research
```json
{
  "researchId": "47069bf6-aeda-4c9b-b979-4f4b8daa3a09",
  "team": "red"
}
```

```json
{
  "researchId": "482ea7df-4406-45eb-b6d5-4ee03bcf0ddb",
  "team": "red"
}
```

```json
{
  "researchId": "df6fe952-7296-4185-9dd5-4a9fab20cd54",
  "team": "red"
}
```

### Black Team Research
```json
{
  "researchId": "d5863711-6cab-4391-84b3-a01bc75415bd",
  "team": "black"
}
```

## Testing Commands

### Test with curl:
```bash
# Red team example
curl -X POST "https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit" \
  -H "Content-Type: application/json" \
  -d '{"researchId": "47069bf6-aeda-4c9b-b979-4f4b8daa3a09", "team": "red"}'

# Black team example
curl -X POST "https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit" \
  -H "Content-Type: application/json" \
  -d '{"researchId": "d5863711-6cab-4391-84b3-a01bc75415bd", "team": "black"}'
```

## S3 Path Structure
Research reports are stored at:
```
s3://color-code-research-results-984906149037/users/fprior/research/{team}/{researchId}/report.md
```

Where:
- `{team}` is one of: red, black, white
- `{researchId}` is a UUID
- The file must be named `report.md`

## Common Issues

### 404 Error - Research Not Found
If you get this error, it means:
1. The research ID doesn't exist in S3
2. The team parameter is wrong
3. The research doesn't have a `report.md` file

### How to Check if Research Exists
```bash
# List all research IDs for a team
aws s3 ls s3://color-code-research-results-984906149037/users/fprior/research/red/ --profile mvp

# Check if specific research has report.md
aws s3 ls s3://color-code-research-results-984906149037/users/fprior/research/red/YOUR_RESEARCH_ID/ --profile mvp
```

## Frontend Integration

The frontend should:
1. Get the research ID from the Color Code Research system
2. Know which team the research belongs to (red/black/white)
3. Send both `researchId` and `team` in the request body

Example frontend code:
```javascript
const response = await fetch('https://9hv22ga3uh.execute-api.us-east-1.amazonaws.com/prod/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    researchId: 'actual-research-id-from-color-code',
    team: 'red'  // or 'black' or 'white'
  })
});
```