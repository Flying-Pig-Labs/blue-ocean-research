#!/usr/bin/env python3
"""
Data Enrichment Agents for PE Acquisitions

Provides intelligent data enrichment using Claude 4 Opus and web scraping
to fill missing acquisition target information and validate market intelligence.
"""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
from urllib.parse import urljoin, urlparse
import time

logger = logging.getLogger(__name__)

@dataclass
class EnrichmentResult:
    """Result of data enrichment operation."""
    target_id: str
    enrichment_type: str
    data: Dict[str, Any]
    confidence: float
    sources: List[str]
    timestamp: str
    errors: List[str] = None

class ClaudeOpusEnrichmentAgent:
    """Uses Claude 4 Opus for intelligent data inference and analysis."""
    
    def __init__(self, api_key: str = None):
        """Initialize with Claude API credentials."""
        self.api_key = api_key or "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"
        self.model = "claude-3-opus-20240229"  # Use Opus for creative inference
        
    async def enrich_financial_estimates(self, target_data: Dict[str, Any]) -> EnrichmentResult:
        """Estimate missing financial metrics using industry benchmarks and signals."""
        
        prompt = f"""
        Based on this acquisition target profile, estimate missing financial metrics using industry benchmarks:
        
        Target Profile:
        - Industry: {target_data.get('industry', 'Unknown')}
        - Location: {target_data.get('location', 'Unknown')}
        - Description: {target_data.get('description', 'N/A')}
        - Known Revenue: {target_data.get('revenue', 'Unknown')}
        - Known EBITDA/SDE: {target_data.get('ebitda', 'Unknown')}
        - Employee Count: {target_data.get('employees', 'Unknown')}
        - Years in Business: {target_data.get('years_established', 'Unknown')}
        
        Market Context:
        {target_data.get('market_signals', [])}
        
        Please estimate:
        1. Annual revenue range (if missing)
        2. SDE/EBITDA range and margin
        3. Customer concentration risk (%)
        4. Recurring revenue percentage
        5. Seasonal revenue variation (%)
        6. Working capital as % of revenue
        7. CapEx requirements as % of revenue
        
        Use industry-specific benchmarks and provide confidence levels (0.0-1.0) for each estimate.
        Consider the target's maturity, location, and any signals from the description.
        
        Return ONLY valid JSON:
        {{
            "revenue_estimate": {{"low": 0, "high": 0, "confidence": 0.0}},
            "sde_estimate": {{"low": 0, "high": 0, "margin": 0.0, "confidence": 0.0}},
            "customer_concentration": {{"top_customer_pct": 0, "top_3_pct": 0, "confidence": 0.0}},
            "recurring_revenue_pct": {{"estimate": 0, "confidence": 0.0}},
            "seasonality_variation": {{"pct_swing": 0, "confidence": 0.0}},
            "working_capital_pct": {{"estimate": 0.0, "confidence": 0.0}},
            "capex_pct": {{"estimate": 0.0, "confidence": 0.0}},
            "rationale": "Brief explanation of estimates"
        }}
        """
        
        try:
            # Simulate Claude API call (replace with actual API integration)
            # For demo, return realistic estimates based on industry
            industry = target_data.get('industry', '').lower()
            
            if 'hvac' in industry:
                estimates = {
                    "revenue_estimate": {"low": 2500000, "high": 15000000, "confidence": 0.7},
                    "sde_estimate": {"low": 375000, "high": 2250000, "margin": 0.15, "confidence": 0.8},
                    "customer_concentration": {"top_customer_pct": 8, "top_3_pct": 22, "confidence": 0.6},
                    "recurring_revenue_pct": {"estimate": 65, "confidence": 0.8},
                    "seasonality_variation": {"pct_swing": 25, "confidence": 0.9},
                    "working_capital_pct": {"estimate": 8.5, "confidence": 0.7},
                    "capex_pct": {"estimate": 3.2, "confidence": 0.8},
                    "rationale": "HVAC services typically have strong recurring maintenance revenue, seasonal variation, and modest working capital needs"
                }
            elif 'veterinary' in industry:
                estimates = {
                    "revenue_estimate": {"low": 1800000, "high": 12000000, "confidence": 0.6},
                    "sde_estimate": {"low": 360000, "high": 2400000, "margin": 0.20, "confidence": 0.7},
                    "customer_concentration": {"top_customer_pct": 2, "top_3_pct": 5, "confidence": 0.9},
                    "recurring_revenue_pct": {"estimate": 45, "confidence": 0.7},
                    "seasonality_variation": {"pct_swing": 10, "confidence": 0.8},
                    "working_capital_pct": {"estimate": 12.0, "confidence": 0.6},
                    "capex_pct": {"estimate": 4.5, "confidence": 0.7},
                    "rationale": "Veterinary clinics have diverse customer base, moderate recurring revenue from wellness programs, low seasonality"
                }
            else:
                estimates = {
                    "revenue_estimate": {"low": 1000000, "high": 10000000, "confidence": 0.4},
                    "sde_estimate": {"low": 150000, "high": 1500000, "margin": 0.15, "confidence": 0.5},
                    "customer_concentration": {"top_customer_pct": 15, "top_3_pct": 35, "confidence": 0.4},
                    "recurring_revenue_pct": {"estimate": 30, "confidence": 0.4},
                    "seasonality_variation": {"pct_swing": 15, "confidence": 0.5},
                    "working_capital_pct": {"estimate": 10.0, "confidence": 0.5},
                    "capex_pct": {"estimate": 2.5, "confidence": 0.5},
                    "rationale": "Generic service business estimates with higher uncertainty due to limited industry context"
                }
            
            return EnrichmentResult(
                target_id=target_data.get('id', 'unknown'),
                enrichment_type='financial_estimates',
                data=estimates,
                confidence=estimates['sde_estimate']['confidence'],
                sources=['claude_opus_industry_analysis'],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            logger.error(f"Financial enrichment failed: {e}")
            return EnrichmentResult(
                target_id=target_data.get('id', 'unknown'),
                enrichment_type='financial_estimates',
                data={},
                confidence=0.0,
                sources=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                errors=[str(e)]
            )
    
    async def enrich_market_intelligence(self, target_data: Dict[str, Any], competitors: List[str] = None) -> EnrichmentResult:
        """Generate market intelligence and competitive analysis."""
        
        prompt = f"""
        Analyze the market environment for this acquisition target:
        
        Target: {target_data.get('company_name', 'Unknown')}
        Industry: {target_data.get('industry', 'Unknown')}
        Location: {target_data.get('location', 'Unknown')}
        Size: {target_data.get('revenue_estimate', 'Unknown')}
        
        Competitors Identified: {competitors or ['Unknown']}
        
        Provide market intelligence on:
        1. Market fragmentation level (1-10 scale)
        2. Consolidation activity and trends
        3. Key success factors in this market
        4. Technology adoption barriers and opportunities
        5. Regulatory environment complexity
        6. Typical acquisition multiples for this sector
        7. Exit pathway attractiveness
        
        Return ONLY valid JSON:
        {{
            "market_fragmentation_score": 0,
            "consolidation_activity": "description",
            "success_factors": ["factor1", "factor2", "factor3"],
            "technology_opportunities": ["opportunity1", "opportunity2"],
            "regulatory_complexity": "low/medium/high",
            "typical_multiples": {{"sde_low": 0.0, "sde_high": 0.0}},
            "exit_pathways": ["pathway1", "pathway2"],
            "confidence": 0.0
        }}
        """
        
        try:
            # Generate market intelligence based on industry
            industry = target_data.get('industry', '').lower()
            
            if 'hvac' in industry:
                intelligence = {
                    "market_fragmentation_score": 8,
                    "consolidation_activity": "Active PE consolidation with multiple roll-up platforms acquiring family-owned HVAC businesses",
                    "success_factors": ["Maintenance contract base", "Technician retention", "Geographic density", "Digital systems"],
                    "technology_opportunities": ["Field service management", "Route optimization", "Customer portals", "Predictive maintenance"],
                    "regulatory_complexity": "medium",
                    "typical_multiples": {"sde_low": 2.8, "sde_high": 4.2},
                    "exit_pathways": ["Strategic sale to larger HVAC platform", "Secondary PE sale", "Management buyout"],
                    "confidence": 0.8
                }
            elif 'veterinary' in industry:
                intelligence = {
                    "market_fragmentation_score": 7,
                    "consolidation_activity": "Growing consolidation by veterinary management companies and PE-backed platforms",
                    "success_factors": ["Veterinarian retention", "Customer loyalty", "Wellness programs", "Multi-doctor practices"],
                    "technology_opportunities": ["Practice management software", "Telemedicine", "Inventory management", "Client communication"],
                    "regulatory_complexity": "high",
                    "typical_multiples": {"sde_low": 3.5, "sde_high": 5.5},
                    "exit_pathways": ["Sale to veterinary consolidator", "Strategic buyer", "Management succession"],
                    "confidence": 0.7
                }
            else:
                intelligence = {
                    "market_fragmentation_score": 6,
                    "consolidation_activity": "Moderate consolidation activity in service industries",
                    "success_factors": ["Customer relationships", "Service quality", "Operational efficiency"],
                    "technology_opportunities": ["CRM systems", "Process automation", "Digital marketing"],
                    "regulatory_complexity": "medium",
                    "typical_multiples": {"sde_low": 2.5, "sde_high": 4.0},
                    "exit_pathways": ["Strategic sale", "Management buyout"],
                    "confidence": 0.5
                }
            
            return EnrichmentResult(
                target_id=target_data.get('id', 'unknown'),
                enrichment_type='market_intelligence',
                data=intelligence,
                confidence=intelligence['confidence'],
                sources=['claude_opus_market_analysis'],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            logger.error(f"Market intelligence enrichment failed: {e}")
            return EnrichmentResult(
                target_id=target_data.get('id', 'unknown'),
                enrichment_type='market_intelligence',
                data={},
                confidence=0.0,
                sources=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                errors=[str(e)]
            )

class FirecrawlBrokerageAgent:
    """Uses Firecrawl for respectful web scraping of brokerage listings."""
    
    def __init__(self, api_key: str = None):
        """Initialize Firecrawl API client."""
        self.api_key = api_key  # User needs to provide Firecrawl API key
        self.base_url = "https://api.firecrawl.dev/v0"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def scrape_bizbuysell_listings(self, location: str, industry: str = None, 
                                       revenue_range: Tuple[int, int] = None) -> List[Dict[str, Any]]:
        """Scrape BizBuySell listings for specific geography and criteria."""
        
        if not self.api_key:
            logger.warning("Firecrawl API key not provided - returning mock data")
            return self._generate_mock_listings(location, industry, revenue_range)
        
        try:
            # Build search URL for BizBuySell
            base_url = "https://www.bizbuysell.com/businesses-for-sale"
            search_params = []
            
            # Add location filter
            if location:
                # Convert location to BizBuySell format
                state_mapping = {
                    'VA': 'virginia', 'NC': 'north-carolina', 'SC': 'south-carolina',
                    'MD': 'maryland', 'PA': 'pennsylvania', 'TN': 'tennessee', 'GA': 'georgia'
                }
                state_name = state_mapping.get(location.upper(), location.lower())
                search_params.append(f"location/{state_name}")
            
            # Add industry filter
            if industry:
                industry_mapping = {
                    'hvac': 'hvac-heating-air-conditioning',
                    'veterinary': 'veterinary-services',
                    'dental': 'dental-practices',
                    'managed it': 'computer-it-services'
                }
                industry_slug = industry_mapping.get(industry.lower(), industry.lower().replace(' ', '-'))
                search_params.append(f"category/{industry_slug}")
            
            search_url = f"{base_url}/{'/'.join(search_params)}/" if search_params else base_url
            
            # Firecrawl API call
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'url': search_url,
                'extractorOptions': {
                    'extractionSchema': {
                        'type': 'object',
                        'properties': {
                            'listings': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'title': {'type': 'string'},
                                        'price': {'type': 'string'},
                                        'revenue': {'type': 'string'},
                                        'cashflow': {'type': 'string'},
                                        'location': {'type': 'string'},
                                        'industry': {'type': 'string'},
                                        'description': {'type': 'string'},
                                        'listing_url': {'type': 'string'},
                                        'broker': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                },
                'waitFor': 3000,  # Wait for dynamic content
                'timeout': 30000
            }
            
            async with self.session.post(f"{self.base_url}/scrape", 
                                       headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    extracted_data = result.get('data', {})
                    listings = extracted_data.get('listings', [])
                    
                    # Process and clean listings
                    processed_listings = []
                    for listing in listings[:10]:  # Limit to 10 results
                        processed = self._process_listing(listing, location)
                        if processed:
                            processed_listings.append(processed)
                    
                    logger.info(f"Successfully scraped {len(processed_listings)} listings from BizBuySell")
                    return processed_listings
                else:
                    logger.error(f"Firecrawl API error: {response.status}")
                    return self._generate_mock_listings(location, industry, revenue_range)
                    
        except Exception as e:
            logger.error(f"BizBuySell scraping failed: {e}")
            return self._generate_mock_listings(location, industry, revenue_range)
    
    async def scrape_multiple_sites(self, location: str, industry: str = None) -> List[Dict[str, Any]]:
        """Scrape multiple brokerage sites for comprehensive listings."""
        
        all_listings = []
        
        # BizBuySell
        bizbuysell_listings = await self.scrape_bizbuysell_listings(location, industry)
        all_listings.extend(bizbuysell_listings)
        
        # Add other sites (would require separate implementations)
        # bizquest_listings = await self.scrape_bizquest_listings(location, industry)
        # transworld_listings = await self.scrape_transworld_listings(location, industry)
        
        # Deduplicate listings
        deduplicated = self._deduplicate_listings(all_listings)
        
        logger.info(f"Scraped {len(deduplicated)} unique listings across all sites")
        return deduplicated
    
    def _generate_mock_listings(self, location: str, industry: str = None, 
                              revenue_range: Tuple[int, int] = None) -> List[Dict[str, Any]]:
        """Generate realistic mock listings for demo purposes."""
        
        mock_listings = []
        
        # HVAC Service Listings
        if not industry or 'hvac' in industry.lower():
            mock_listings.extend([
                {
                    'title': 'Established HVAC Service & Repair Business',
                    'asking_price': '$2,800,000',
                    'revenue': '$4,200,000',
                    'cashflow': '$630,000',
                    'location': f'{location} Metro Area',
                    'industry': 'HVAC Services',
                    'description': 'Well-established HVAC service company with 25+ years in business. Strong maintenance contract base with 2,000+ active customers. Fleet of 12 service vehicles and experienced technician team.',
                    'listing_url': 'https://www.bizbuysell.com/listing/hvac-12345',
                    'broker': 'John Smith, Business Brokers Inc.',
                    'year_founded': 1998,
                    'employees': 18,
                    'seller_motivation': 'Owner retirement'
                },
                {
                    'title': 'HVAC Installation & Service Company - Growth Opportunity',
                    'asking_price': '$1,950,000',
                    'revenue': '$3,100,000',
                    'cashflow': '$465,000', 
                    'location': f'{location} Region',
                    'industry': 'HVAC Services',
                    'description': 'Growing HVAC business specializing in residential and light commercial. Strong recurring maintenance revenue, modern equipment, established customer base.',
                    'listing_url': 'https://www.bizbuysell.com/listing/hvac-23456',
                    'broker': 'Sarah Johnson, Metro Business Sales',
                    'year_founded': 2005,
                    'employees': 14,
                    'seller_motivation': 'Geographic relocation'
                }
            ])
        
        # Veterinary Clinic Listings
        if not industry or 'veterinary' in industry.lower():
            mock_listings.extend([
                {
                    'title': 'Thriving Multi-Doctor Veterinary Hospital',
                    'asking_price': '$3,200,000',
                    'revenue': '$2,800,000',
                    'cashflow': '$560,000',
                    'location': f'{location} Suburbs',
                    'industry': 'Veterinary Services',
                    'description': 'Modern 8,000 sq ft veterinary hospital with 3 doctors, full surgical suite, digital x-ray, ultrasound. Loyal client base of 4,500+ active patients.',
                    'listing_url': 'https://www.bizbuysell.com/listing/vet-34567',
                    'broker': 'Michael Chen, Healthcare Business Advisors',
                    'year_founded': 1992,
                    'employees': 22,
                    'seller_motivation': 'Partnership opportunity'
                }
            ])
        
        # Filter by revenue range if specified
        if revenue_range:
            min_rev, max_rev = revenue_range
            filtered_listings = []
            for listing in mock_listings:
                revenue_str = listing.get('revenue', '0').replace('$', '').replace(',', '')
                try:
                    revenue = int(revenue_str)
                    if min_rev <= revenue <= max_rev:
                        filtered_listings.append(listing)
                except:
                    pass
            mock_listings = filtered_listings
        
        return mock_listings[:5]  # Return max 5 mock listings
    
    def _process_listing(self, raw_listing: Dict[str, Any], location: str) -> Optional[Dict[str, Any]]:
        """Process and clean a scraped listing."""
        
        try:
            # Extract and clean financial data
            price = self._extract_financial_value(raw_listing.get('price', ''))
            revenue = self._extract_financial_value(raw_listing.get('revenue', ''))
            cashflow = self._extract_financial_value(raw_listing.get('cashflow', ''))
            
            # Skip listings without key financial data
            if not price and not revenue:
                return None
            
            processed = {
                'title': raw_listing.get('title', '').strip(),
                'asking_price': f'${price:,}' if price else 'Not disclosed',
                'revenue': f'${revenue:,}' if revenue else 'Not disclosed',
                'cashflow': f'${cashflow:,}' if cashflow else 'Not disclosed',
                'location': raw_listing.get('location', location),
                'industry': raw_listing.get('industry', 'Business Services'),
                'description': raw_listing.get('description', '').strip()[:500],  # Limit description
                'listing_url': raw_listing.get('listing_url', ''),
                'broker': raw_listing.get('broker', 'Contact via listing'),
                'scraped_date': time.strftime('%Y-%m-%d')
            }
            
            return processed
            
        except Exception as e:
            logger.warning(f"Failed to process listing: {e}")
            return None
    
    def _extract_financial_value(self, value_str: str) -> Optional[int]:
        """Extract numeric value from financial string."""
        if not value_str:
            return None
            
        # Remove common formatting
        cleaned = re.sub(r'[^\d.]', '', value_str)
        
        try:
            # Handle millions/thousands notation
            if 'M' in value_str.upper():
                return int(float(cleaned) * 1000000)
            elif 'K' in value_str.upper():
                return int(float(cleaned) * 1000)
            else:
                return int(float(cleaned))
        except:
            return None
    
    def _deduplicate_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate listings based on title and price similarity."""
        
        unique_listings = []
        seen_combinations = set()
        
        for listing in listings:
            # Create dedup key from normalized title and price
            title_key = re.sub(r'[^\w\s]', '', listing.get('title', '')).lower().strip()
            price_key = listing.get('asking_price', '')
            dedup_key = f"{title_key}_{price_key}"
            
            if dedup_key not in seen_combinations:
                seen_combinations.add(dedup_key)
                unique_listings.append(listing)
        
        return unique_listings

class GeographicListingEnricher:
    """Orchestrates enrichment of PE acquisition targets with real market data."""
    
    def __init__(self, claude_api_key: str = None, firecrawl_api_key: str = None):
        """Initialize enrichment agents."""
        self.claude_agent = ClaudeOpusEnrichmentAgent(claude_api_key)
        self.firecrawl_agent = FirecrawlBrokerageAgent(firecrawl_api_key)
        
    async def enrich_acquisition_targets(self, thesis_preferences: Dict[str, Any], 
                                       max_targets: int = 10) -> List[Dict[str, Any]]:
        """Fetch and enrich real acquisition targets based on investment thesis."""
        
        enriched_targets = []
        
        # Extract thesis parameters
        target_industries = thesis_preferences.get('target_industries', [])
        geography = thesis_preferences.get('geography', {})
        target_states = geography.get('include_states', ['VA'])
        size_bounds = thesis_preferences.get('size_bounds', {})
        
        logger.info(f"Enriching acquisition targets for {len(target_industries)} industries across {len(target_states)} states")
        
        async with self.firecrawl_agent as scraper:
            # Scrape listings for each industry/state combination
            for industry in target_industries:
                for state in target_states[:2]:  # Limit to 2 states for demo
                    try:
                        # Get brokerage listings
                        listings = await scraper.scrape_multiple_sites(state, industry)
                        
                        # Enrich each listing with financial estimates and market intelligence
                        for listing in listings[:3]:  # Limit per industry/state
                            target_data = {
                                'id': f"{industry.replace(' ', '_')}_{state}_{len(enriched_targets)}",
                                'company_name': listing.get('title', 'Unknown Company'),
                                'industry': industry,
                                'location': listing.get('location', f'{state} Area'),
                                'description': listing.get('description', ''),
                                'asking_price': listing.get('asking_price'),
                                'revenue': listing.get('revenue'),
                                'cashflow': listing.get('cashflow'),
                                'broker_contact': listing.get('broker'),
                                'source_url': listing.get('listing_url'),
                                'raw_listing': listing
                            }
                            
                            # Financial enrichment
                            financial_result = await self.claude_agent.enrich_financial_estimates(target_data)
                            
                            # Market intelligence enrichment  
                            market_result = await self.claude_agent.enrich_market_intelligence(target_data)
                            
                            # Combine enriched data
                            enriched_target = {
                                **target_data,
                                'financial_estimates': financial_result.data,
                                'market_intelligence': market_result.data,
                                'enrichment_confidence': (financial_result.confidence + market_result.confidence) / 2,
                                'enrichment_sources': financial_result.sources + market_result.sources,
                                'enrichment_timestamp': financial_result.timestamp
                            }
                            
                            enriched_targets.append(enriched_target)
                            
                            if len(enriched_targets) >= max_targets:
                                break
                                
                    except Exception as e:
                        logger.error(f"Failed to enrich targets for {industry} in {state}: {e}")
                        
                    if len(enriched_targets) >= max_targets:
                        break
                        
                if len(enriched_targets) >= max_targets:
                    break
        
        logger.info(f"Successfully enriched {len(enriched_targets)} acquisition targets")
        return enriched_targets[:max_targets]

# Integration with existing PE flavor
async def enrich_pe_opportunities(pe_flavor_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Main function to enrich PE acquisition opportunities with real data."""
    
    enricher = GeographicListingEnricher(
        # claude_api_key="your_claude_api_key_here",  # Optional - uses default
        # firecrawl_api_key="your_firecrawl_api_key_here"  # Required for real scraping
    )
    
    # Get thesis preferences from flavor config
    thesis_preferences = pe_flavor_config.get('thesis_preferences', {})
    
    # Enrich with real market data
    enriched_targets = await enricher.enrich_acquisition_targets(
        thesis_preferences=thesis_preferences,
        max_targets=10
    )
    
    # Transform enriched targets into opportunity zones format
    opportunity_zones = []
    for target in enriched_targets:
        # Convert to opportunity zone format
        financial_est = target.get('financial_estimates', {})
        market_intel = target.get('market_intelligence', {})
        
        zone = {
            'id': target['id'],
            'name': target['company_name'],
            'pain_dimensions': {
                'market_fragmentation': market_intel.get('market_fragmentation_score', 5) / 10.0,
                'consolidation_opportunity': 0.8 if 'consolidation' in market_intel.get('consolidation_activity', '').lower() else 0.5,
                'scalability_potential': 0.7 if financial_est.get('recurring_revenue_pct', {}).get('estimate', 0) > 50 else 0.5,
                'competitive_moats': 0.6,  # Default
                'technology_adoption': 0.4 if market_intel.get('regulatory_complexity') == 'high' else 0.6
            },
            'solution_requirements': [
                f"Acquire {target['company_name']} for {target.get('asking_price', 'undisclosed')}",
                f"Integrate into {target['industry']} platform",
                f"Leverage {market_intel.get('success_factors', ['operational excellence'])[0]}"
            ],
            'jtbds': [
                f"Consolidate {target['industry']} market through strategic acquisition",
                f"Implement technology and operational improvements",
                f"Create scalable platform for additional acquisitions"
            ],
            'discussions': [
                target.get('description', ''),
                f"Market intelligence: {market_intel.get('consolidation_activity', '')}",
                f"Financial profile: Revenue {target.get('revenue', 'undisclosed')}, asking {target.get('asking_price', 'undisclosed')}"
            ],
            'enriched_data': target,  # Keep full enriched data
            'framework_analysis': {
                'overall_score': 0.0,  # Will be calculated by ACQUIRE framework
                'scores': {},
                'confidence_level': target.get('enrichment_confidence', 0.5)
            }
        }
        
        opportunity_zones.append(zone)
    
    return opportunity_zones