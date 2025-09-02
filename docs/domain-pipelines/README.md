# Domain-Specific Pipeline Documentation

This directory contains comprehensive specifications for each domain-specific pipeline variation. Each domain transforms the base Blue Ocean Research pipeline to generate industry-specific outputs instead of generic product ideas.

## Available Domain Specifications

### 🏙️ [City Revitalization](./city-revitalization.md)
**Output**: Complete RFP (Request for Proposal) packages for municipal revitalization projects
**Status**: ✅ Specification Complete
**Key Features**: Census data integration, grant alignment, evidence pack generation

### 💰 [Private Equity](./private-equity.md) 
**Output**: Investment-grade acquisition proposals for target companies
**Status**: 🔄 In Development
**Key Features**: Financial modeling, due diligence frameworks, market analysis

### 🏥 [Medical Devices](./medical-devices.md)
**Output**: FDA-compliant device specifications with prototype roadmaps  
**Status**: 📋 Planned
**Key Features**: Regulatory pathway analysis, clinical validation, safety assessment

### 🏢 [Data Center](./data-center.md)
**Output**: Site-specific micro-zone deployment strategies with land acquisition plans
**Status**: 📋 Planned  
**Key Features**: Infrastructure analysis, geographic optimization, deployment planning

## Documentation Structure

Each domain specification follows this standardized format:

```
1. Domain Overview & Objectives
2. Opportunity Zone Methodology (Alternative to Reddit)  
3. Data Sources & API Integration Points
4. Pipeline Modifications Required
5. Output Structure & Templates
6. Implementation Roadmap
7. Testing & Validation Strategy
```

## Integration with Base Pipeline

All domain specifications build upon the existing 7-stage Blue Ocean Research pipeline:

**Stage 1**: Research Analysis (Enhanced with domain-specific context)
**Stage 2**: JTBD & Discovery (Modified data sources per domain)  
**Stage 3**: Opportunity Zone Analysis (Domain-specific zone creation)
**Stage 4**: Solution Generation (Domain-specific templates & prompts)
**Stage 5**: Consolidation (Domain-specific enrichment)
**Stage 6**: Output Generation (Domain-specific formatting)
**Stage 7**: Deployment (Domain-specific repository structure)

## Environment Variable Configuration

Each domain is activated via environment variable:

```bash
IDEATION_TYPE=city-revitalization
OUTPUT_FORMAT=rfp-package  
DOMAIN_CONFIG_PATH=config/domains/city-revitalization.json
```

## Getting Started

1. **Choose Domain**: Select the appropriate domain specification
2. **Review Requirements**: Understand data sources and API integrations needed
3. **Configure Environment**: Set domain-specific environment variables
4. **Deploy & Test**: Follow the implementation roadmap for your chosen domain

## Contributing

When adding new domain specifications:

1. Follow the standardized documentation structure
2. Include comprehensive API integration details
3. Provide clear implementation roadmaps
4. Add testing and validation strategies
5. Update this README with the new domain entry