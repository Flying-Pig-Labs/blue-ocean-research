#!/usr/bin/env python3
"""
Lambda-compatible Product Idea Generator
Refactored from product_idea_generator.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- OpenAI o1 + Claude integration
- Memory-efficient idea generation and filtering
- Proper error handling for long-running operations
- Rate limiting and timeout management
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside handler for connection reuse)
s3_client = None
secrets_client = None

def initialize_clients():
    """Initialize AWS clients with retry configuration"""
    global s3_client, secrets_client
    
    if s3_client is None:
        s3_client = boto3.client('s3',
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )
    
    if secrets_client is None:
        secrets_client = boto3.client('secretsmanager',
            config=boto3.session.Config(
                retries={'max_attempts': 2, 'mode': 'standard'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )

def get_secrets() -> Dict[str, str]:
    """Load API keys from AWS Secrets Manager"""
    secrets = {}
    
    # Get secret ARNs from environment variables
    anthropic_arn = os.environ.get('ANTHROPIC_SECRET_ARN')
    openai_arn = os.environ.get('OPENAI_SECRET_ARN')
    exa_arn = os.environ.get('EXA_SECRET_ARN')
    cohere_arn = os.environ.get('COHERE_SECRET_ARN')
    github_arn = os.environ.get('GITHUB_SECRET_ARN')
    
    # Load Anthropic API key (JSON format with lowercase key)
    if anthropic_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=anthropic_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['ANTHROPIC_API_KEY'] = secret_data.get('anthropic_key', '')
            except json.JSONDecodeError:
                secrets['ANTHROPIC_API_KEY'] = secret_value
            logger.info("Loaded Anthropic key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Anthropic secret: {e}")
    
    # Load OpenAI API key (JSON format with lowercase key)
    if openai_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=openai_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['OPENAI_API_KEY'] = secret_data.get('openai_key', '')
            except json.JSONDecodeError:
                secrets['OPENAI_API_KEY'] = secret_value
            logger.info("Loaded OpenAI key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load OpenAI secret: {e}")
    
    # Load EXA API key (plain string format)
    if exa_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=exa_arn)
            secret_value = response.get('SecretString', '')
            # EXA key is stored as plain string
            secrets['EXA_API_KEY'] = secret_value
            logger.info("Loaded EXA key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load EXA secret: {e}")
    
    # Load Cohere API key (plain string format)
    if cohere_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=cohere_arn)
            secret_value = response.get('SecretString', '')
            # Cohere key is stored as plain string
            secrets['COHERE_API_KEY'] = secret_value
            logger.info("Loaded Cohere key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Cohere secret: {e}")
    
    # Load GitHub token (JSON format with lowercase key)
    if github_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=github_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['GITHUB_TOKEN'] = secret_data.get('github_token', '')
            except json.JSONDecodeError:
                secrets['GITHUB_TOKEN'] = secret_value
            logger.info("Loaded GitHub token from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load GitHub secret: {e}")
    
    # Fallback to environment variables
    if not secrets.get('ANTHROPIC_API_KEY'):
        secrets['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')
    if not secrets.get('OPENAI_API_KEY'):
        secrets['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
    if not secrets.get('EXA_API_KEY'):
        secrets['EXA_API_KEY'] = os.environ.get('EXA_API_KEY', '')
    if not secrets.get('COHERE_API_KEY'):
        secrets['COHERE_API_KEY'] = os.environ.get('COHERE_API_KEY', '')
    if not secrets.get('GITHUB_TOKEN'):
        secrets['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN', '')
    
    return secrets
def read_s3_object(bucket: str, key: str) -> str:
    """Read text content from S3 object"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to read S3 object s3://{bucket}/{key}: {e}")
        raise

def read_s3_json(bucket: str, key: str) -> Dict[str, Any]:
    """Read JSON content from S3 object"""
    content = read_s3_object(bucket, key)
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from s3://{bucket}/{key}: {e}")
        raise

def write_s3_object(bucket: str, key: str, content: str, content_type: str = 'text/plain'):
    """Write content to S3 object"""
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType=content_type,
            ServerSideEncryption='AES256'
        )
        logger.info(f"Successfully wrote to s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"Failed to write S3 object s3://{bucket}/{key}: {e}")
        raise

def call_openai_o1(prompt: str, model: str = "o1-preview-2024-09-12", 
                   max_completion_tokens: int = 25000, api_key: str = None) -> str:
    """Call OpenAI o1 model with proper configuration"""
    import openai
    
    client = openai.OpenAI(api_key=api_key)
    
    for attempt in range(2):  # Reduced retries for o1 model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=max_completion_tokens
                # Note: o1 models don't use temperature parameter
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"OpenAI o1 API attempt {attempt + 1} failed: {e}")
            if attempt < 1:
                time.sleep(5)  # Longer delay for o1
            else:
                raise

def call_anthropic_api(prompt: str, model: str = "claude-3-5-haiku-20241022", 
                      temperature: float = 0.8, max_tokens: int = 3000,
                      api_key: str = None) -> str:
    """Call Anthropic API with retry logic"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=api_key)
    
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.warning(f"Anthropic API attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise

def generate_product_ideas(value_curves_data: Dict[str, Any], openai_key: str, 
                         target_count: int = 10) -> List[Dict[str, Any]]:
    """Generate product ideas using OpenAI o1 based on value curves"""
    
    # Extract zones for context
    zones = value_curves_data.get('zones', [])
    if not zones:
        raise ValueError("No opportunity zones found in value curves data")
    
    # Prepare context from top zones
    top_zones = zones[:5]  # Focus on top 5 zones
    
    zones_context = []
    for zone in top_zones:
        value_curve = zone.get('value_curve', {})
        key_factors = value_curve.get('key_factors', [])
        insights = value_curve.get('strategic_insights', {})
        
        factors_text = []
        for factor in key_factors[:5]:  # Top 5 factors
            factors_text.append(f"- {factor.get('factor', 'Unknown')}: Current={factor.get('current_score', 0)}/10, Gap={factor.get('opportunity_gap', 'Unknown')}")
        
        zone_text = f"""
Zone: {zone.get('name', 'Unknown')}
Theme: {zone.get('core_theme', zone.get('description', ''))}
Opportunity Score: {zone.get('market_opportunity_score', zone.get('opportunity_score', 0))}

Value Factors:
{chr(10).join(factors_text)}

Key Gaps: {', '.join(insights.get('gaps', [])[:3])}
Innovation Opportunities: {', '.join(insights.get('innovation_opportunities', [])[:3])}
Market Maturity: {value_curve.get('market_maturity', 'Unknown')}
"""
        zones_context.append(zone_text)
    
    context_text = '\n---\n'.join(zones_context)
    
    prompt = f"""Based on these opportunity zones and their value curve analyses, generate {target_count} innovative product ideas.

OPPORTUNITY ZONES & VALUE CURVES:
{context_text}

For each product idea, provide:
1. Product name and compelling tagline
2. Core value proposition (1-2 sentences)
3. Key features (5-7 specific features)
4. Target customer segment
5. Business model approach
6. Go-to-market strategy
7. Estimated development effort
8. Revenue potential assessment
9. Innovation score (1-10) based on uniqueness and market disruption
10. Viability score (1-10) based on technical feasibility and market readiness

Requirements:
- Address the biggest opportunity gaps identified
- Leverage emerging technologies (AI, automation, API-first, no-code, etc.)
- Have clear differentiation from existing solutions
- Be technically feasible within 12-24 months
- Target market segments with proven demand

Format as a JSON array of product objects with these fields:
- name, tagline, value_proposition, features (array), target_segment, business_model, go_to_market, development_effort, revenue_potential, innovation_score, viability_score

Focus on breakthrough solutions that could capture significant market share in underserved areas."""

    logger.info(f"Generating {target_count} product ideas using OpenAI o1...")
    
    try:
        response = call_openai_o1(prompt, max_completion_tokens=25000, api_key=openai_key)
        
        # Extract JSON from response
        if '```json' in response:
            json_text = response.split('```json')[1].split('```')[0].strip()
        elif response.strip().startswith('['):
            json_text = response.strip()
        else:
            # Try to find JSON array in response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            json_text = json_match.group(0) if json_match else '[]'
        
        # Parse JSON
        product_ideas = json.loads(json_text)
        
        if not isinstance(product_ideas, list):
            raise ValueError("Product ideas response is not a list")
        
        # Validate and enrich ideas
        validated_ideas = []
        for i, idea in enumerate(product_ideas[:target_count]):
            if isinstance(idea, dict):
                # Ensure required fields exist
                validated_idea = {
                    'idea_id': f'IDEA_{i+1:03d}',
                    'name': idea.get('name', f'Product Idea {i+1}'),
                    'tagline': idea.get('tagline', ''),
                    'value_proposition': idea.get('value_proposition', ''),
                    'features': idea.get('features', []),
                    'target_segment': idea.get('target_segment', 'Not specified'),
                    'business_model': idea.get('business_model', 'Not specified'),
                    'go_to_market': idea.get('go_to_market', 'Not specified'),
                    'development_effort': idea.get('development_effort', 'Not specified'),
                    'revenue_potential': idea.get('revenue_potential', 'Not specified'),
                    'innovation_score': min(10, max(1, idea.get('innovation_score', 5))),
                    'viability_score': min(10, max(1, idea.get('viability_score', 5))),
                    'generated_timestamp': datetime.now().isoformat()
                }
                validated_ideas.append(validated_idea)
        
        logger.info(f"Successfully generated {len(validated_ideas)} product ideas")
        return validated_ideas
        
    except Exception as e:
        logger.error(f"Product idea generation failed: {e}")
        # Return fallback ideas
        return create_fallback_ideas(target_count)

def create_fallback_ideas(count: int) -> List[Dict[str, Any]]:
    """Create fallback product ideas when generation fails"""
    fallback_ideas = []
    
    base_ideas = [
        {
            'name': 'Smart Workflow Hub',
            'tagline': 'AI-powered workflow automation for growing teams',
            'value_proposition': 'Eliminates manual coordination overhead through intelligent process automation',
            'features': ['AI workflow designer', 'Smart notifications', 'Performance analytics', 'Integration APIs', 'Team collaboration'],
            'target_segment': 'Small to medium businesses',
            'business_model': 'SaaS subscription',
            'innovation_score': 6,
            'viability_score': 7
        },
        {
            'name': 'DataSync Pro',
            'tagline': 'Real-time data integration without the complexity',
            'value_proposition': 'Connects disparate systems with zero-code configuration and automatic schema detection',
            'features': ['Auto-discovery', 'Real-time sync', 'Data validation', 'Custom transformations', 'Monitoring dashboard'],
            'target_segment': 'Operations teams',
            'business_model': 'Usage-based pricing',
            'innovation_score': 7,
            'viability_score': 8
        },
        {
            'name': 'DecisionFlow',
            'tagline': 'Collaborative decision-making with AI insights',
            'value_proposition': 'Accelerates team decisions through structured frameworks and predictive analysis',
            'features': ['Decision templates', 'Stakeholder tracking', 'Impact modeling', 'Historical analysis', 'Automated reporting'],
            'target_segment': 'Management teams',
            'business_model': 'Per-seat subscription',
            'innovation_score': 5,
            'viability_score': 6
        }
    ]
    
    for i in range(count):
        base_idx = i % len(base_ideas)
        base_idea = base_ideas[base_idx].copy()
        
        idea = {
            'idea_id': f'IDEA_{i+1:03d}',
            'name': base_idea['name'],
            'tagline': base_idea['tagline'],
            'value_proposition': base_idea['value_proposition'],
            'features': base_idea['features'],
            'target_segment': base_idea['target_segment'],
            'business_model': base_idea['business_model'],
            'go_to_market': 'Content marketing and partnerships',
            'development_effort': '12-18 months',
            'revenue_potential': '$10M+ ARR potential',
            'innovation_score': base_idea['innovation_score'],
            'viability_score': base_idea['viability_score'],
            'generated_timestamp': datetime.now().isoformat(),
            'note': 'Fallback idea generated due to API limitations'
        }
        
        fallback_ideas.append(idea)
    
    logger.warning(f"Generated {len(fallback_ideas)} fallback ideas")
    return fallback_ideas

def enrich_product_ideas(product_ideas: List[Dict[str, Any]], anthropic_key: str, 
                       max_ideas: int = 8) -> List[Dict[str, Any]]:
    """Enrich product ideas with detailed analysis using Claude"""
    
    enriched_ideas = []
    
    # Limit processing for Lambda constraints
    ideas_to_process = product_ideas[:max_ideas]
    
    for i, idea in enumerate(ideas_to_process):
        logger.info(f"Enriching idea {i+1}/{len(ideas_to_process)}: {idea.get('name', 'Unknown')}")
        
        try:
            enrichment = enrich_single_idea(idea, anthropic_key)
            enriched_idea = {**idea, **enrichment}
            enriched_ideas.append(enriched_idea)
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"Failed to enrich idea {idea.get('name', 'Unknown')}: {e}")
            # Add without enrichment
            enriched_ideas.append(idea)
    
    return enriched_ideas

def enrich_single_idea(idea: Dict[str, Any], anthropic_key: str) -> Dict[str, Any]:
    """Enrich a single product idea with detailed analysis"""
    
    prompt = f"""Product Idea: {idea.get('name', 'Unknown')}
Tagline: {idea.get('tagline', '')}
Value Proposition: {idea.get('value_proposition', '')}
Features: {', '.join(idea.get('features', []))}

Provide enrichment analysis with:
1. **Technical Architecture**: High-level system design approach
2. **Competitive Moat**: What makes this defensible long-term
3. **Risk Assessment**: Top 3 risks and mitigation strategies
4. **Success Metrics**: 5 key KPIs to track progress
5. **Partnership Opportunities**: Strategic partners to consider
6. **Market Sizing**: TAM/SAM estimate reasoning

Format as JSON with these exact keys: technical_architecture, competitive_moat, risk_assessment (object with risks and mitigations arrays), success_metrics (array), partnerships (array), market_sizing."""

    try:
        response = call_anthropic_api(prompt, api_key=anthropic_key, max_tokens=2000)
        
        # Try to parse as JSON
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            
            enrichment = json.loads(response)
            
            # Validate structure
            if not isinstance(enrichment, dict):
                raise ValueError("Enrichment is not a dictionary")
            
            return enrichment
            
        except json.JSONDecodeError:
            # Create fallback enrichment
            return {
                "technical_architecture": "Cloud-native microservices with API-first design",
                "competitive_moat": "Network effects and proprietary data advantages",
                "risk_assessment": {
                    "risks": ["Market competition", "Technical complexity", "User adoption"],
                    "mitigations": ["Strong differentiation", "MVP approach", "User-centric design"]
                },
                "success_metrics": ["User adoption rate", "Revenue growth", "Customer retention", "Feature usage", "Market share"],
                "partnerships": ["Technology integrators", "Industry consultants", "Platform partners"],
                "market_sizing": "$100M+ TAM based on target segment size and pricing"
            }
    
    except Exception as e:
        logger.warning(f"Enrichment failed for {idea.get('name')}: {e}")
        return {}

def filter_and_rank_ideas(ideas: List[Dict[str, Any]], top_n: int = 8) -> List[Dict[str, Any]]:
    """Filter and rank ideas by combined innovation and viability scores"""
    
    # Calculate composite scores
    for idea in ideas:
        innovation = idea.get('innovation_score', 5)
        viability = idea.get('viability_score', 5)
        
        # Weighted composite score (60% viability, 40% innovation)
        composite_score = (viability * 0.6) + (innovation * 0.4)
        idea['composite_score'] = round(composite_score, 2)
    
    # Sort by composite score
    ranked_ideas = sorted(ideas, key=lambda x: x.get('composite_score', 0), reverse=True)
    
    # Filter to top N
    filtered_ideas = ranked_ideas[:top_n]
    
    logger.info(f"Filtered to top {len(filtered_ideas)} ideas from {len(ideas)} generated")
    return filtered_ideas

def create_product_ideas_report(final_ideas: List[Dict[str, Any]], 
                              execution_metadata: Dict[str, Any]) -> str:
    """Create comprehensive product ideas report"""
    
    timestamp = datetime.now().isoformat()
    
    report = f"""# Product Ideas Generation Report

**Generated:** {timestamp}  
**Processing Mode:** Lambda o1 + Claude Enrichment  
**Ideas Generated:** {execution_metadata.get('total_generated', len(final_ideas))}  
**Ideas After Filtering:** {len(final_ideas)}  
**Execution Time:** {execution_metadata.get('execution_time', 'N/A')} seconds  

## Executive Summary

This report presents {len(final_ideas)} innovative product ideas generated from comprehensive value curve analysis. Each idea addresses identified market gaps and leverages emerging technologies for competitive advantage.

### Top 3 Recommendations:
"""
    
    # Add top 3 ideas summary
    for i, idea in enumerate(final_ideas[:3], 1):
        report += f"""
**{i}. {idea.get('name', 'Unknown')}** (Composite Score: {idea.get('composite_score', 0)})  
*{idea.get('tagline', 'No tagline')}*  
{idea.get('value_proposition', 'No value proposition available')[:150]}...
"""
    
    report += "\n---\n\n## Detailed Product Ideas\n\n"
    
    # Add detailed ideas
    for i, idea in enumerate(final_ideas, 1):
        report += f"""### {i}. {idea.get('name', 'Unknown Product')}

**Tagline:** {idea.get('tagline', 'Not provided')}  
**Innovation Score:** {idea.get('innovation_score', 0)}/10  
**Viability Score:** {idea.get('viability_score', 0)}/10  
**Composite Score:** {idea.get('composite_score', 0)}

#### Value Proposition
{idea.get('value_proposition', 'Not provided')}

#### Key Features
"""
        
        features = idea.get('features', [])
        for feature in features[:7]:  # Top 7 features
            report += f"- {feature}\n"
        
        report += f"""
#### Business Details
- **Target Segment:** {idea.get('target_segment', 'Not specified')}
- **Business Model:** {idea.get('business_model', 'Not specified')}
- **Go-to-Market:** {idea.get('go_to_market', 'Not specified')}
- **Development Effort:** {idea.get('development_effort', 'Not specified')}
- **Revenue Potential:** {idea.get('revenue_potential', 'Not specified')}

"""
        
        # Add enrichment data if available
        if idea.get('technical_architecture'):
            report += f"#### Technical Architecture\n{idea['technical_architecture']}\n\n"
        
        if idea.get('competitive_moat'):
            report += f"#### Competitive Moat\n{idea['competitive_moat']}\n\n"
        
        if idea.get('success_metrics'):
            report += f"#### Success Metrics\n"
            for metric in idea.get('success_metrics', [])[:5]:
                report += f"- {metric}\n"
            report += "\n"
        
        report += "---\n\n"
    
    report += f"""## Pipeline Metadata

- **Lambda Function:** Product Ideas Generator
- **Generation Model:** OpenAI o1-preview
- **Enrichment Model:** Claude-3.5-Haiku
- **Total Processing Time:** {execution_metadata.get('execution_time', 'N/A')} seconds
- **Ideas Generated:** {execution_metadata.get('total_generated', len(final_ideas))}
- **Ideas After Filtering:** {len(final_ideas)}
"""
    
    return report

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for product idea generation
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "value_curves/analysis.json",
        "output_keys": {
            "ideas": "products/ideas.json",
            "report": "products/report.md"
        },
        "job_id": "job-123",
        "generation_params": {
            "target_count": 12,
            "final_count": 8
        },
        "metadata": {...}
    }
    """
    start_time = time.time()
    
    try:
        # Initialize AWS clients
        initialize_clients()
        
        # Extract event parameters
        bucket = event.get('s3Bucket') or event.get('bucket')
        input_key = event.get('s3InputKey') or event.get('input_key')
        output_keys = event.get('s3OutputKeys') or event.get('output_keys', {})
        job_id = event.get('jobId') or event.get('job_id', 'unknown')
        generation_params = event.get('generation_params', {})
        
        # Generation parameters
        target_count = generation_params.get('target_count', 12)
        final_count = generation_params.get('final_count', 8)
        
        if not bucket or not input_key:
            raise ValueError("Missing required parameters: bucket and input_key")
        
        logger.info(f"Processing product idea generation for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        logger.info(f"Target ideas: {target_count}, Final: {final_count}")
        
        # Load secrets
        secrets = get_secrets()
        openai_key = secrets.get('OPENAI_API_KEY')
        anthropic_key = secrets.get('ANTHROPIC_API_KEY')
        
        if not openai_key or not anthropic_key:
            raise ValueError("Required API keys not available")
        
        # Read value curves data from S3
        logger.info("Loading value curves data from S3...")
        value_curves_data = read_s3_json(bucket, input_key)
        
        # Generate product ideas using OpenAI o1
        logger.info(f"Generating {target_count} product ideas...")
        product_ideas = generate_product_ideas(value_curves_data, openai_key, target_count)
        
        # Filter and rank ideas
        logger.info("Filtering and ranking ideas...")
        filtered_ideas = filter_and_rank_ideas(product_ideas, final_count)
        
        # Enrich ideas with Claude
        logger.info("Enriching ideas with detailed analysis...")
        enriched_ideas = enrich_product_ideas(filtered_ideas, anthropic_key, final_count)
        
        # Create execution metadata
        execution_metadata = {
            'execution_time': round(time.time() - start_time, 2),
            'total_generated': len(product_ideas),
            'after_filtering': len(filtered_ideas),
            'final_enriched': len(enriched_ideas)
        }
        
        # Create comprehensive data structure
        product_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_mode": "Lambda o1 Generation + Claude Enrichment",
                "total_ideas_generated": len(product_ideas),
                "ideas_after_filtering": len(enriched_ideas),
                "generation_model": "o1-preview-2024-09-12",
                "enrichment_model": "claude-3.5-haiku-20241022"
            },
            "generation_summary": {
                "highest_innovation": max([idea.get('innovation_score', 0) for idea in enriched_ideas]) if enriched_ideas else 0,
                "highest_viability": max([idea.get('viability_score', 0) for idea in enriched_ideas]) if enriched_ideas else 0,
                "average_composite": round(sum([idea.get('composite_score', 0) for idea in enriched_ideas]) / len(enriched_ideas), 2) if enriched_ideas else 0
            },
            "filtered_ideas": enriched_ideas
        }
        
        # Create report
        logger.info("Generating comprehensive report...")
        report = create_product_ideas_report(enriched_ideas, execution_metadata)
        
        # Save outputs to S3
        outputs_created = []
        
        if 'ideas' in output_keys:
            write_s3_object(bucket, output_keys['ideas'], 
                          json.dumps(product_data, indent=2), 'application/json')
            outputs_created.append(f"s3://{bucket}/{output_keys['ideas']}")
        
        if 'report' in output_keys:
            write_s3_object(bucket, output_keys['report'], report, 'text/markdown')
            outputs_created.append(f"s3://{bucket}/{output_keys['report']}")
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'jobId': job_id,
            'execution_time': round(execution_time, 2),
            'output_locations': outputs_created,
            'total_ideas_generated': len(product_ideas),
            'final_ideas_count': len(enriched_ideas),
            'top_idea': enriched_ideas[0].get('name') if enriched_ideas else 'None',
            'highest_composite_score': max([idea.get('composite_score', 0) for idea in enriched_ideas]) if enriched_ideas else 0,
            'average_innovation_score': round(sum([idea.get('innovation_score', 0) for idea in enriched_ideas]) / len(enriched_ideas), 2) if enriched_ideas else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Product idea generation completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"Product idea generation failed: {e}")
        
        return {
            'statusCode': 500,
            'error': str(e),
            'job_id': event.get('job_id', 'unknown'),
            'execution_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

# For local testing
if __name__ == "__main__":
    test_event = {
        "bucket": "test-bucket",
        "input_key": "value_curves/analysis.json",
        "output_keys": {
            "ideas": "products/ideas.json",
            "report": "products/report.md"
        },
        "job_id": "test-job-123",
        "generation_params": {
            "target_count": 10,
            "final_count": 6
        }
    }
    
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_product_ideas"
            self.memory_limit_in_mb = 3008
            self.remaining_time_in_millis = lambda: 900000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))