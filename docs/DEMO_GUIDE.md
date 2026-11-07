# 🚀 Blue Ocean Research Demo Guide

## Overview
This app transforms market research data into innovative product ideas through a 7-stage AI-powered pipeline. All API keys are automatically loaded from AWS Secrets Manager using your `mvp` profile.

## 🔐 AWS Secrets Configuration
The app automatically loads these secrets from AWS:
- `ANTHROPIC_API_KEY`: arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6
- `OPENAI_API_KEY`: arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY
- `EXA_API_KEY`: arn:aws:secretsmanager:us-east-1:984906149037:secret:exa-key-N7ylem
- `COHERE_API_KEY`: arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j
- `GITHUB_TOKEN`: arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy

## 🎯 Quick Start Demo

### Option 1: Interactive Demo Script (Recommended)
```bash
cd /Users/williamprior/Development/GitHub/blue-ocean-research/multi-step-llm-app
source venv/bin/activate
export AWS_PROFILE=mvp

# Run the interactive demo
python demo_with_aws.py
```

This will:
1. Load all API keys from AWS Secrets Manager
2. Test the API connections
3. Show you demo options including:
   - Simple API test
   - Research Analyzer demo with sample data
   - Full pipeline walkthrough guide

### Option 2: Main App Demo
```bash
export AWS_PROFILE=mvp

# Test mode - quick API connection test
python main.py --test

# Interactive mode - step-by-step creative writing demo
python main.py

# Headless mode - automated workflow
python main.py --headless
```

### Option 3: Component Testing with Sample Data
```bash
export AWS_PROFILE=mvp

# List all testable components
python integration_test_cli.py --list-components

# Test research analyzer with sample SaaS data
python integration_test_cli.py --test research_analyzer

# Test with debug mode to see costs
python integration_test_cli.py --test research_analyzer --debug

# Run all component tests
python integration_test_cli.py --batch all
```

## 📊 Full Pipeline Demo

To see the complete market research → product ideation flow:

```bash
export AWS_PROFILE=mvp
cd /Users/williamprior/Development/GitHub/blue-ocean-research/multi-step-llm-app

# Stage 1: Analyze sample SaaS productivity research
python research_analyzer.py --input tests/fixtures/sample_research.json
# Output: pain_points.txt, personas.json, opportunities.json

# Stage 2: Research Jobs-to-be-Done (uses EXA search)
python jobs_researcher.py
# Output: jtbd_analysis.json

# Stage 3: Cluster JTBDs into opportunity zones
python cluster_jtbd.py pain_points.txt
# Output: opportunity_zones.json

# Stage 4: Map value curves for each zone
python value_curve_mapper.py opportunity_zones.json
# Output: value_curves.json

# Stage 5: Generate product ideas
python product_idea_generator.py --input value_curves.json
# Output: product_ideas.json, product_ideas_report.md

# Stage 6: Consolidate and enrich ideas (optional)
python idea_consolidator.py
# Output: consolidated_ideas.json

# Stage 7: Create GitHub repository with all results
python product_idea_generator.py --github --repo-name "saas-innovations-demo"
# Creates GitHub repo with README and issues for each idea
```

## 🧪 Sample Data Included

The app includes comprehensive sample data for a SaaS productivity tools market research scenario:
- **Customer Interviews**: 3 detailed interviews with Product Manager, Engineering Manager, Marketing Director
- **Survey Results**: Pain points from 150 respondents (78% want unified tools)
- **Market Analysis**: $45.2B market, 12.3% growth, competitive landscape
- **Behavioral Data**: Tool usage patterns and integration challenges

## 💡 What Each Stage Does

1. **Research Analyzer**: Runs 4 parallel AI analyses to extract pain points, create personas, identify opportunities
2. **Jobs Researcher**: Uses EXA search to find real-world JTBD examples and synthesizes them
3. **JTBD Clustering**: Uses Cohere embeddings + HDBSCAN to group similar jobs into zones
4. **Value Curve Mapper**: Analyzes competitive positioning for each opportunity zone
5. **Product Idea Generator**: Creates 10 ideas per zone using ERRC framework, filters by viability
6. **Idea Consolidator**: Enriches ideas with market sizing and business cases
7. **GitHub Integration**: Creates a repository with comprehensive documentation and trackable issues

## 🎨 Example Output

From the sample SaaS research, the pipeline generates ideas like:
- **UnifyHub**: AI-powered workspace integrator (Innovation: 8/10, Viability: 7.5/10)
- **FlowSync**: Real-time collaboration platform (Innovation: 7/10, Viability: 8/10)
- **DataMesh**: Unified analytics dashboard (Innovation: 6/10, Viability: 9/10)

Each idea includes:
- Core value proposition
- Key features aligned with ERRC grid
- Target customer segment
- Technical feasibility assessment
- Market readiness evaluation
- Implementation roadmap

## ⚡ Debug Mode

Add `DEBUG=true` to see cost tracking and model switching:
```bash
DEBUG=true python main.py --headless
DEBUG=true python product_idea_generator.py --test
```

This shows:
- Which AI models are being used
- Token counts and costs
- Performance metrics
- Potential savings from debug mode

## 🚨 Troubleshooting

If you see "ANTHROPIC_API_KEY not found":
1. Ensure `AWS_PROFILE=mvp` is set
2. Check AWS credentials: `aws sts get-caller-identity --profile mvp`
3. Test secret access: `aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6 --profile mvp`

## 📈 Performance Notes

- Full pipeline takes ~5-10 minutes depending on data size
- Each stage can be run independently
- Results are saved locally as JSON/text files
- GitHub integration is optional but recommended for tracking

Ready to transform market research into innovative products! 🎯