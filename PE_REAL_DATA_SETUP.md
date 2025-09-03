# 🔍 PE Acquisitions Real Data Integration Setup

This guide shows how to integrate real brokerage listings and Claude 4 Opus analysis into the PE acquisitions flavor.

## 🎯 Overview

The enrichment system provides two main capabilities:

1. **🌐 Firecrawl Web Scraping** - Respectfully scrapes brokerage sites for real listings
2. **🧠 Claude 4 Opus Analysis** - Estimates missing financial data and market intelligence

## 🔑 API Keys Required

### Firecrawl API (Required for real listings)
```bash
# Sign up at https://firecrawl.dev/
export FIRECRAWL_API_KEY="your_firecrawl_api_key_here"
```

### Anthropic API (Optional - built-in default available)
```bash
# Optional: Override default Claude API key
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install aiohttp asyncio
# Note: Firecrawl client library if available
```

### 2. Configure Investment Thesis
Edit `flavors/private_equity_acquisitions.yaml`:

```yaml
thesis_preferences:
  target_industries: 
    - "HVAC services"
    - "veterinary clinics" 
    - "dental practices"
    - "managed IT services"
  geography:
    include_states: ["VA", "NC", "SC", "MD", "PA", "TN", "GA"]
    cluster_radius_km: 300
  size_bounds:
    revenue_min: 1000000      # $1M
    revenue_max: 20000000     # $20M
    sde_min: 250000           # $250k
    sde_max: 4000000          # $4M
```

### 3. Run Enriched Pipeline
```bash
# With Firecrawl API key
export FIRECRAWL_API_KEY="your_key_here"
python run_pe_enriched_pipeline.py --flavor private_equity_acquisitions

# Demo mode (mock data)
python pe_enrichment_demo.py
```

## 📊 Data Sources Supported

### Brokerage Sites (via Firecrawl)
- **BizBuySell** - Primary source for small business listings
- **BizQuest** - Business broker network
- **DealStream** - M&A marketplace  
- **Transworld** - Business brokerage network
- **Sunbelt** - Business broker listings
- **Axial** - Private capital marketplace (where accessible)
- **Acquire.com** - Startup acquisition marketplace (where accessible)

### Enrichment Fields Extracted
```python
expected_fields = [
    "title",           # Business name/description
    "industry",        # Industry classification  
    "location",        # Geographic location
    "asking_price",    # Seller asking price
    "gross_rev",       # Annual revenue
    "cash_flow",       # Net cash flow/SDE
    "sde",            # Seller's Discretionary Earnings
    "ebitda",         # EBITDA if available
    "year_founded",   # Business establishment date
    "employees",      # Employee count
    "description",    # Business description
    "url",            # Listing URL
    "broker_contact"  # Broker information
]
```

## 🧠 Claude 4 Opus Enrichment

### Financial Estimates
- **Revenue Ranges** - Estimates missing revenue from market signals
- **SDE/EBITDA Margins** - Industry-specific profitability estimates  
- **Customer Concentration** - Risk assessment for client dependency
- **Recurring Revenue %** - Subscription/contract revenue analysis
- **Seasonal Variation** - Revenue volatility patterns
- **Working Capital** - Cash flow requirements
- **CapEx Needs** - Capital expenditure estimates

### Market Intelligence
- **Fragmentation Score** - Market consolidation opportunity (1-10)
- **Consolidation Activity** - Active PE/strategic buyer analysis
- **Success Factors** - Key business drivers for industry
- **Technology Opportunities** - Digitization and automation potential
- **Regulatory Complexity** - Compliance risk assessment
- **Acquisition Multiples** - Typical SDE/EBITDA multiples for exits
- **Strategic Buyers** - Exit pathway analysis

## 🎯 ACQUIRE Framework Integration

Real data flows through the ACQUIRE framework:

```python
# Addressable Fragmentation (A) - Market consolidation opportunity
fragmentation_score = market_intel['market_fragmentation_score'] / 10.0

# Cashflow Quality (C) - Recurring revenue and predictability  
cashflow_score = financial_estimates['recurring_revenue_pct'] / 100.0

# Quality of Operations (Q) - Technology and process maturity
operations_score = tech_adoption_indicators + process_maturity

# Upside Levers (U) - Value creation opportunities
upside_score = consolidation_potential + digitization_opportunity

# Integration Readiness (I) - Cultural and operational fit
integration_score = management_quality + systems_compatibility

# Risk & Compliance (R) - Regulatory and legal risk (inverted)
risk_score = regulatory_complexity + litigation_risk

# Exit Pathways (E) - Strategic buyer universe
exit_score = buyer_universe + multiple_expansion_potential
```

## 📋 Output: Real LOIs Generated

### GitHub Issue Format
```markdown
# [PE LOI] Confidential HVAC Services, LLC – Richmond, VA

**Target**: Real company from BizBuySell listing
**ACQUIRE Score**: 0.72 (calculated from real data)
**Preliminary Offer**: $2.1M – $2.8M (based on $615k SDE)

## Real Market Data
- **Listing**: https://www.bizbuysell.com/listing/12345
- **Broker**: John Smith, TransWorld Business Advisors
- **Revenue**: $3.2M (from listing)
- **SDE**: $615k (from listing + Claude analysis)
- **Recurring**: 68% (Claude estimate with 0.8 confidence)

## ACQUIRE Analysis
- **Addressable Fragmentation**: 0.85 (market intel)
- **Cashflow Quality**: 0.78 (recurring revenue base)
- **Upside Levers**: 0.82 (consolidation + tech opportunity)

## Deal Structure (Preliminary)
- **Cash at Close**: 70% ($1.5M)
- **Seller Note**: 15% ($320k)  
- **Earnout**: 15% ($320k)
- **Metrics**: 12-mo customer retention ≥ 92%
```

## ⚡ Performance & Rate Limits

### Firecrawl Rate Limits
```python
rate_limit = {
    "per_minute": 20,      # Requests per minute
    "timeout": 30000,      # 30 second timeout
    "wait_for": 3000       # Wait for dynamic content
}
```

### Geographic Coverage
- Searches **2 states max** per run (configurable)
- **3 listings max** per industry/state combo  
- **10 total targets** enriched per run
- Automatic deduplication across broker sites

### Confidence Scoring
```python
confidence_levels = {
    "financial_estimates": 0.6-0.9,  # Based on data completeness
    "market_intelligence": 0.5-0.8,  # Based on industry knowledge  
    "overall_enrichment": average,    # Combined confidence
}
```

## 🛡️ Compliance & Ethics

### Respectful Scraping
- ✅ Rate limiting and delays between requests
- ✅ Robots.txt compliance via Firecrawl
- ✅ ToS-respectful data extraction
- ✅ No aggressive crawling or site overloading

### Data Usage
- ✅ Business intelligence and analysis only
- ✅ No redistribution of scraped data
- ✅ Attribution to original sources
- ✅ Preliminary/non-binding LOI disclaimers

## 🔧 Troubleshooting

### Common Issues
```bash
# Missing Firecrawl API key
Error: "Firecrawl API key not provided - returning mock data"
Solution: export FIRECRAWL_API_KEY="your_key"

# Rate limit exceeded  
Error: "429 Too Many Requests"
Solution: Reduce per_minute rate in config

# No listings found
Error: "No acquisition targets found"
Solution: Broaden geographic/industry criteria
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug logging
python pe_enrichment_demo.py --debug
```

## 📈 Expected Results

### Real Data Pipeline Output
- **10 GitHub Issues** with real acquisition targets
- **Preliminary LOIs** with actual broker contact info
- **ACQUIRE scores** based on real financial/market data
- **Deal structures** with industry-appropriate multiples
- **Due diligence** contingencies for actual risks found

### Sample Performance
```
🎯 Enrichment Results:
   • 7 real HVAC targets from BizBuySell
   • 3 veterinary clinics from BizQuest  
   • Average confidence: 0.74
   • Processing time: ~90 seconds
   • Top ACQUIRE score: 0.82
```

This system transforms the PE acquisitions flavor from synthetic demo data into a real deal sourcing and analysis platform! 🚀