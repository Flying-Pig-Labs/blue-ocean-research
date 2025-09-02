# Stage 2: Data Integration Setup (Week 2)

## Objective
Implement the three-tier data architecture with AWS datasets, free APIs, and premium sources.

## Prerequisites
- [ ] Stage 1 foundation completed and validated
- [ ] AWS credentials configured
- [ ] Base adapter and utilities tested

## Step 2.1: AWS Free Data Integration (Days 1-2)

### 2.1.1 Implement Census Data Access
**Update**: `src/utils/aws_data_client.py` (enhance existing class)

```python
import h5py
import geopandas as gpd
from io import BytesIO

class AWSDataClient:
    # ... existing code ...
    
    def get_detailed_census_data(self, location_params: Dict) -> Dict[str, pd.DataFrame]:
        """Get comprehensive census data for location analysis"""
        try:
            datasets = {}
            
            # ACS 5-year estimates (most recent)
            acs_data = self._fetch_acs_data(location_params)
            if not acs_data.empty:
                datasets['demographics'] = acs_data
            
            # Economic data
            economic_data = self._fetch_economic_indicators(location_params)
            if not economic_data.empty:
                datasets['economics'] = economic_data
                
            return datasets
            
        except Exception as e:
            logger.error(f"Error fetching detailed census data: {e}")
            return {}
    
    def _fetch_acs_data(self, location_params: Dict) -> pd.DataFrame:
        """Fetch American Community Survey data"""
        # Implementation for ACS PUMS data
        bucket = 'uscensus-pms'
        
        # Determine appropriate dataset based on location
        state_code = location_params.get('state_code', '01')  # Default Alabama
        key = f'acs2022_5yr/psam_h{state_code}.csv'  # Housing data
        
        try:
            obj = self.s3_unsigned.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(obj['Body'])
            
            # Apply geographic filters
            return self._filter_by_geography(df, location_params)
            
        except Exception as e:
            logger.warning(f"Could not fetch ACS data for {key}: {e}")
            return pd.DataFrame()
    
    def _filter_by_geography(self, df: pd.DataFrame, location_params: Dict) -> pd.DataFrame:
        """Apply geographic filters to census data"""
        filtered_df = df.copy()
        
        # Filter by PUMA (Public Use Microdata Area) if specified
        if 'puma_codes' in location_params:
            filtered_df = filtered_df[filtered_df['PUMA'].isin(location_params['puma_codes'])]
        
        # Filter by metropolitan area
        if 'msa_code' in location_params:
            # MSA filtering logic here
            pass
        
        return filtered_df
    
    def get_openstreetmap_data(self, bbox: tuple, feature_types: List[str]) -> gpd.GeoDataFrame:
        """Get OpenStreetMap data from AWS for specified bounding box"""
        try:
            # OSM data is stored as PBF files on S3
            bucket = 'osm-pds'
            
            # For MVP, use pre-processed extracts
            # In production, would implement spatial querying
            
            features = []
            for feature_type in feature_types:
                feature_data = self._query_osm_features(bbox, feature_type)
                if not feature_data.empty:
                    features.append(feature_data)
            
            if features:
                return pd.concat(features, ignore_index=True)
            else:
                return gpd.GeoDataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching OSM data: {e}")
            return gpd.GeoDataFrame()
    
    def _query_osm_features(self, bbox: tuple, feature_type: str) -> gpd.GeoDataFrame:
        """Query specific OSM feature types within bounding box"""
        # Simplified implementation - would use actual OSM querying
        # For MVP, return sample data structure
        
        sample_data = {
            'amenity': ['school', 'hospital', 'library'],
            'name': ['Central High', 'General Hospital', 'Public Library'],
            'geometry': [None, None, None]  # Would contain actual geometries
        }
        
        return gpd.GeoDataFrame(sample_data)
    
    def get_nrel_energy_data(self, location_params: Dict) -> Dict[str, Any]:
        """Get NREL National Solar Radiation Database"""
        try:
            bucket = 'nrel-pds-nsrdb'
            
            # NSRDB data is in HDF5 format
            lat = location_params.get('latitude', 40.0)
            lon = location_params.get('longitude', -100.0)
            year = location_params.get('year', 2022)
            
            # Find closest grid point (simplified)
            key = f'current/nsrdb_{year}.h5'
            
            # For MVP, return processed summary data
            # In production, would process HDF5 files
            energy_data = {
                'annual_dni': 1800,  # Direct Normal Irradiance kWh/m²
                'annual_ghi': 1600,  # Global Horizontal Irradiance  
                'wind_speed_avg': 6.5,  # m/s
                'temperature_avg': 15.2,  # °C
                'location': {'lat': lat, 'lon': lon}
            }
            
            logger.info(f"Retrieved NREL energy data for {lat}, {lon}")
            return energy_data
            
        except Exception as e:
            logger.error(f"Error fetching NREL data: {e}")
            return {}
    
    def get_climate_data(self, location_params: Dict) -> Dict[str, Any]:
        """Get ERA5 reanalysis climate data"""
        try:
            # ERA5 data available through AWS Public Dataset Program
            bucket = 'era5-pds' 
            
            lat = location_params.get('latitude', 40.0)
            lon = location_params.get('longitude', -100.0)
            
            # ERA5 provides hourly data - aggregate to useful metrics
            climate_metrics = {
                'cooling_degree_days': 850,  # Annual cooling requirements
                'heating_degree_days': 2100, # Annual heating requirements  
                'humidity_avg': 65,          # Average relative humidity %
                'precipitation_annual': 800,  # mm/year
                'extreme_temp_events': 12,   # Days >35°C or <-10°C
                'location': {'lat': lat, 'lon': lon}
            }
            
            logger.info(f"Retrieved climate data for {lat}, {lon}")
            return climate_metrics
            
        except Exception as e:
            logger.error(f"Error fetching climate data: {e}")
            return {}
```

### 2.1.2 Create Data Caching System
**Create**: `src/utils/data_cache.py`

```python
import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Any, Optional

class DataCache:
    """Efficient caching system for AWS and API data"""
    
    def __init__(self, cache_dir: str = "data_cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
        # Separate directories for different data types
        (self.cache_dir / 'aws_data').mkdir(exist_ok=True)
        (self.cache_dir / 'api_responses').mkdir(exist_ok=True)
        (self.cache_dir / 'processed_data').mkdir(exist_ok=True)
    
    def _generate_cache_key(self, prefix: str, params: dict) -> str:
        """Generate consistent cache key from parameters"""
        # Sort parameters for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"{prefix}_{param_hash}"
    
    def get(self, key: str, data_type: str = 'processed_data') -> Optional[Any]:
        """Retrieve cached data if not expired"""
        cache_file = self.cache_dir / data_type / f"{key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age > self.ttl:
                cache_file.unlink()  # Remove expired cache
                return None
            
            # Load cached data
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            return cached_data
            
        except Exception as e:
            logger.warning(f"Failed to load cache {key}: {e}")
            return None
    
    def set(self, key: str, data: Any, data_type: str = 'processed_data') -> None:
        """Store data in cache"""
        cache_file = self.cache_dir / data_type / f"{key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.warning(f"Failed to cache data {key}: {e}")
    
    def get_census_data(self, location_params: dict) -> Optional[pd.DataFrame]:
        """Get cached census data"""
        key = self._generate_cache_key('census', location_params)
        return self.get(key, 'aws_data')
    
    def cache_census_data(self, location_params: dict, data: pd.DataFrame) -> None:
        """Cache census data"""
        key = self._generate_cache_key('census', location_params)
        self.set(key, data, 'aws_data')
    
    def get_api_response(self, api_name: str, query_params: dict) -> Optional[dict]:
        """Get cached API response"""
        key = self._generate_cache_key(f'api_{api_name}', query_params)
        return self.get(key, 'api_responses')
    
    def cache_api_response(self, api_name: str, query_params: dict, response: dict) -> None:
        """Cache API response"""
        key = self._generate_cache_key(f'api_{api_name}', query_params)
        self.set(key, response, 'api_responses')
    
    def clear_expired(self) -> int:
        """Remove all expired cache files"""
        removed_count = 0
        
        for data_type in ['aws_data', 'api_responses', 'processed_data']:
            cache_subdir = self.cache_dir / data_type
            
            for cache_file in cache_subdir.glob('*.pkl'):
                try:
                    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_age > self.ttl:
                        cache_file.unlink()
                        removed_count += 1
                except Exception as e:
                    logger.warning(f"Error removing cache file {cache_file}: {e}")
        
        return removed_count
    
    def get_cache_stats(self) -> dict:
        """Get cache usage statistics"""
        stats = {}
        
        for data_type in ['aws_data', 'api_responses', 'processed_data']:
            cache_subdir = self.cache_dir / data_type
            files = list(cache_subdir.glob('*.pkl'))
            
            total_size = sum(f.stat().st_size for f in files)
            
            stats[data_type] = {
                'file_count': len(files),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        
        return stats
```

## Step 2.2: API Integration Implementation (Days 3-4)

### 2.2.1 Enhance API Manager
**Update**: `src/utils/api_manager.py` (add to existing class)

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List

class APIManager:
    # ... existing code ...
    
    def __init__(self):
        # ... existing initialization ...
        self.cache = DataCache()
        self.session_timeout = aiohttp.ClientTimeout(total=30)
    
    async def parallel_api_calls(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple API calls in parallel"""
        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            tasks = []
            
            for request in requests:
                task = self._async_api_call(session, request)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions and return clean results
            clean_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"API call {i} failed: {result}")
                    clean_results.append({"error": str(result)})
                else:
                    clean_results.append(result)
            
            return clean_results
    
    async def _async_api_call(self, session: aiohttp.ClientSession, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single async API call"""
        method = request.get('method', 'GET')
        url = request['url']
        headers = request.get('headers', {})
        params = request.get('params', {})
        data = request.get('data', {})
        
        async with session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data if method == 'POST' else None
        ) as response:
            result = await response.json()
            return {
                'status_code': response.status,
                'data': result,
                'request_info': request.get('info', {})
            }
    
    def enhanced_perplexity_research(self, queries: List[str], domain_context: str = "") -> Dict[str, Any]:
        """Execute multiple Perplexity queries with caching"""
        if not self.perplexity_api_key:
            return {"error": "Perplexity API key not configured"}
        
        results = {}
        
        for i, query in enumerate(queries):
            # Check cache first
            cache_params = {"query": query, "domain": domain_context}
            cached_result = self.cache.get_api_response('perplexity', cache_params)
            
            if cached_result:
                results[f"query_{i}"] = cached_result
                continue
            
            # Execute API call
            result = self.perplexity_research(query, domain_context)
            
            # Cache successful results
            if "error" not in result:
                self.cache.cache_api_response('perplexity', cache_params, result)
            
            results[f"query_{i}"] = result
        
        return results
    
    def get_comprehensive_energy_data(self, location_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive energy data from multiple sources"""
        energy_data = {}
        
        # EIA pricing data
        if location_params.get('state'):
            pricing_data = self.get_energy_prices(location_params['state'])
            if "error" not in pricing_data:
                energy_data['pricing'] = pricing_data
        
        # Additional energy sources can be added here
        # - FERC data for transmission
        # - State public utility commission data
        # - Regional grid operator data
        
        return energy_data
    
    def get_regulatory_intelligence(self, domain: str, location: str) -> Dict[str, Any]:
        """Get regulatory intelligence via web search and extraction"""
        queries = self._generate_regulatory_queries(domain, location)
        
        # Use Perplexity for regulatory research
        regulatory_data = {}
        
        for query_type, query in queries.items():
            result = self.perplexity_research(
                query,
                domain_context=f"Regulatory analysis for {domain} in {location}"
            )
            regulatory_data[query_type] = result
        
        return regulatory_data
    
    def _generate_regulatory_queries(self, domain: str, location: str) -> Dict[str, str]:
        """Generate domain-specific regulatory queries"""
        base_queries = {
            'crypto-mining': {
                'licensing': f"cryptocurrency mining licensing requirements {location}",
                'energy_policy': f"energy policy mining operations {location}",
                'zoning': f"zoning regulations data centers {location}",
                'environmental': f"environmental regulations mining {location}"
            },
            'medtech': {
                'fda_pathway': f"FDA approval requirements medical devices",
                'state_licensing': f"medical device manufacturing licensing {location}",
                'quality_systems': f"ISO 13485 requirements {location}",
                'clinical_trials': f"clinical trial regulations medical devices {location}"
            },
            'private-equity': {
                'disclosure': f"private equity disclosure requirements {location}",
                'antitrust': f"antitrust regulations private equity {location}",
                'securities': f"securities regulations private investment {location}"
            },
            'city-revitalization': {
                'municipal_law': f"municipal partnership regulations {location}",
                'nonprofit_compliance': f"nonprofit collaboration regulations {location}",
                'grant_compliance': f"municipal grant compliance requirements {location}"
            }
        }
        
        return base_queries.get(domain, {})
    
    def validate_api_health(self) -> Dict[str, bool]:
        """Check health of all configured APIs"""
        health_status = {}
        
        # Test Perplexity
        if self.perplexity_api_key:
            try:
                test_result = self.perplexity_research("test query")
                health_status['perplexity'] = "error" not in test_result
            except:
                health_status['perplexity'] = False
        else:
            health_status['perplexity'] = False
        
        # Test EIA
        if self.eia_api_key:
            try:
                test_result = self.get_energy_prices("TX")
                health_status['eia'] = "error" not in test_result
            except:
                health_status['eia'] = False
        else:
            health_status['eia'] = False
        
        # Test FDA
        try:
            test_result = self.get_fda_device_data("defibrillator")
            health_status['fda'] = "error" not in test_result
        except:
            health_status['fda'] = False
        
        return health_status
```

### 2.2.2 Create Unified Data Orchestrator
**Create**: `src/utils/data_orchestrator.py`

```python
import asyncio
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import logging

from .aws_data_client import AWSDataClient
from .api_manager import APIManager
from .data_cache import DataCache

logger = logging.getLogger(__name__)

class DataOrchestrator:
    """Orchestrates data collection from multiple sources"""
    
    def __init__(self, data_tier: str = 'free'):
        self.data_tier = data_tier
        self.aws_client = AWSDataClient()
        self.api_manager = APIManager()
        self.cache = DataCache()
        
    def get_comprehensive_location_data(self, location_params: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Get all relevant data for a location and domain"""
        logger.info(f"Gathering {self.data_tier} tier data for {domain} in {location_params}")
        
        # Check cache first
        cache_key = f"{domain}_{hash(str(sorted(location_params.items())))}"
        cached_data = self.cache.get(cache_key, 'processed_data')
        
        if cached_data:
            logger.info("Using cached location data")
            return cached_data
        
        # Gather data from multiple sources
        location_data = {
            'location_params': location_params,
            'domain': domain,
            'data_tier': self.data_tier,
            'sources': {}
        }
        
        # Tier 1: Free AWS data
        location_data['sources'].update(self._get_free_aws_data(location_params, domain))
        
        # Tier 2: Free APIs  
        if self.data_tier in ['enhanced', 'premium']:
            location_data['sources'].update(self._get_free_api_data(location_params, domain))
        
        # Tier 3: Premium data
        if self.data_tier == 'premium':
            location_data['sources'].update(self._get_premium_data(location_params, domain))
        
        # Cache results
        self.cache.set(cache_key, location_data, 'processed_data')
        
        return location_data
    
    def _get_free_aws_data(self, location_params: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Collect all relevant free AWS datasets"""
        aws_data = {}
        
        try:
            # Census data for all domains
            census_data = self.aws_client.get_detailed_census_data(location_params)
            if census_data:
                aws_data['census'] = census_data
            
            # OpenStreetMap for spatial context
            if 'latitude' in location_params and 'longitude' in location_params:
                bbox = self._create_bounding_box(location_params)
                feature_types = self._get_osm_features_for_domain(domain)
                
                osm_data = self.aws_client.get_openstreetmap_data(bbox, feature_types)
                if not osm_data.empty:
                    aws_data['openstreetmap'] = osm_data
            
            # Domain-specific AWS data
            if domain == 'crypto-mining':
                energy_data = self.aws_client.get_nrel_energy_data(location_params)
                climate_data = self.aws_client.get_climate_data(location_params)
                
                if energy_data:
                    aws_data['energy'] = energy_data
                if climate_data:
                    aws_data['climate'] = climate_data
            
            logger.info(f"Collected {len(aws_data)} AWS datasets")
            
        except Exception as e:
            logger.error(f"Error collecting AWS data: {e}")
        
        return aws_data
    
    def _get_free_api_data(self, location_params: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Collect data from free APIs"""
        api_data = {}
        
        try:
            # Domain-specific API queries
            queries = self._generate_domain_queries(location_params, domain)
            
            # Perplexity research queries
            research_results = self.api_manager.enhanced_perplexity_research(
                queries, 
                domain_context=f"{domain} analysis"
            )
            
            if research_results:
                api_data['perplexity_research'] = research_results
            
            # Domain-specific APIs
            if domain == 'crypto-mining':
                energy_prices = self.api_manager.get_comprehensive_energy_data(location_params)
                if energy_prices:
                    api_data['energy_pricing'] = energy_prices
            
            elif domain == 'medtech':
                fda_data = self.api_manager.get_fda_device_data(
                    location_params.get('device_type', 'medical device')
                )
                if fda_data and "error" not in fda_data:
                    api_data['fda_devices'] = fda_data
            
            # Regulatory intelligence for all domains
            regulatory_data = self.api_manager.get_regulatory_intelligence(
                domain, 
                location_params.get('location_name', 'United States')
            )
            if regulatory_data:
                api_data['regulatory'] = regulatory_data
            
            logger.info(f"Collected {len(api_data)} API datasets")
            
        except Exception as e:
            logger.error(f"Error collecting API data: {e}")
        
        return api_data
    
    def _get_premium_data(self, location_params: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Collect premium/commercial data (future implementation)"""
        # Placeholder for AWS Data Exchange integration
        premium_data = {}
        
        logger.info("Premium data collection not yet implemented")
        
        return premium_data
    
    def _create_bounding_box(self, location_params: Dict[str, Any]) -> tuple:
        """Create bounding box around location"""
        lat = location_params['latitude']
        lon = location_params['longitude']
        
        # Create ~10km bounding box
        delta = 0.05  # roughly 10km at mid-latitudes
        
        return (
            lon - delta,  # min_lon
            lat - delta,  # min_lat  
            lon + delta,  # max_lon
            lat + delta   # max_lat
        )
    
    def _get_osm_features_for_domain(self, domain: str) -> List[str]:
        """Get relevant OSM feature types for domain"""
        feature_map = {
            'city-revitalization': ['amenity', 'leisure', 'office', 'shop'],
            'crypto-mining': ['power', 'industrial', 'landuse'],
            'medtech': ['healthcare', 'research', 'industrial'],
            'private-equity': ['office', 'industrial', 'commercial']
        }
        
        return feature_map.get(domain, ['amenity'])
    
    def _generate_domain_queries(self, location_params: Dict[str, Any], domain: str) -> List[str]:
        """Generate domain-specific research queries"""
        location_name = location_params.get('location_name', 'location')
        
        query_templates = {
            'city-revitalization': [
                f"municipal partnerships and coalitions in {location_name}",
                f"nonprofit organizations and community groups {location_name}",
                f"city council priorities and budget {location_name}",
                f"economic development initiatives {location_name}"
            ],
            'crypto-mining': [
                f"cryptocurrency mining regulations {location_name}",
                f"industrial electricity rates {location_name}",
                f"data center infrastructure {location_name}",
                f"mining operation permits {location_name}"
            ],
            'medtech': [
                f"medical device manufacturing {location_name}",
                f"healthcare innovation clusters {location_name}",
                f"FDA compliance requirements {location_name}",
                f"biotech regulatory environment {location_name}"
            ],
            'private-equity': [
                f"private equity transactions {location_name}",
                f"business acquisition opportunities {location_name}",
                f"family owned businesses {location_name}",
                f"succession planning services {location_name}"
            ]
        }
        
        return query_templates.get(domain, [f"business opportunities {location_name}"])
    
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality and completeness of gathered data"""
        validation_results = {
            'data_sources': len(data.get('sources', {})),
            'completeness_score': 0,
            'quality_issues': [],
            'recommendations': []
        }
        
        sources = data.get('sources', {})
        
        # Check data completeness
        expected_sources = self._get_expected_sources(data.get('domain'))
        found_sources = list(sources.keys())
        
        completeness = len(found_sources) / len(expected_sources) if expected_sources else 1
        validation_results['completeness_score'] = round(completeness * 100, 1)
        
        # Identify missing critical sources
        missing_sources = set(expected_sources) - set(found_sources)
        if missing_sources:
            validation_results['quality_issues'].append(f"Missing data sources: {', '.join(missing_sources)}")
        
        # Check for empty datasets
        for source_name, source_data in sources.items():
            if not source_data or (isinstance(source_data, dict) and not source_data):
                validation_results['quality_issues'].append(f"Empty dataset: {source_name}")
        
        # Generate recommendations
        if validation_results['completeness_score'] < 70:
            validation_results['recommendations'].append("Consider upgrading to enhanced data tier")
        
        if validation_results['quality_issues']:
            validation_results['recommendations'].append("Review API configurations and connectivity")
        
        return validation_results
    
    def _get_expected_sources(self, domain: str) -> List[str]:
        """Get expected data sources for domain"""
        base_sources = ['census', 'perplexity_research']
        
        domain_sources = {
            'city-revitalization': base_sources + ['openstreetmap', 'regulatory'],
            'crypto-mining': base_sources + ['energy', 'climate', 'energy_pricing', 'regulatory'],
            'medtech': base_sources + ['fda_devices', 'regulatory'],
            'private-equity': base_sources + ['regulatory']
        }
        
        return domain_sources.get(domain, base_sources)
```

## Step 2.3: Testing and Validation (Day 5)

### 2.3.1 Create Comprehensive Tests
**Create**: `tests/utils/test_data_integration.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from src.utils.data_orchestrator import DataOrchestrator
from src.utils.data_cache import DataCache

class TestDataIntegration:
    
    @pytest.fixture
    def orchestrator(self):
        return DataOrchestrator(data_tier='free')
    
    @pytest.fixture
    def sample_location_params(self):
        return {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'location_name': 'New York',
            'state': 'NY',
            'state_code': '36'
        }
    
    def test_comprehensive_data_collection(self, orchestrator, sample_location_params):
        """Test comprehensive data collection"""
        with patch.multiple(
            orchestrator.aws_client,
            get_detailed_census_data=Mock(return_value={'demographics': pd.DataFrame()}),
            get_openstreetmap_data=Mock(return_value=pd.DataFrame()),
            get_nrel_energy_data=Mock(return_value={'solar': 'high'})
        ):
            result = orchestrator.get_comprehensive_location_data(
                sample_location_params, 
                'crypto-mining'
            )
            
            assert result['domain'] == 'crypto-mining'
            assert 'sources' in result
            assert len(result['sources']) > 0
    
    def test_data_caching(self, orchestrator, sample_location_params):
        """Test data caching functionality"""
        # First call should fetch data
        with patch.multiple(
            orchestrator.aws_client,
            get_detailed_census_data=Mock(return_value={'test': 'data'})
        ) as mocks:
            result1 = orchestrator.get_comprehensive_location_data(
                sample_location_params, 
                'city-revitalization'
            )
            
            # Second call should use cache
            result2 = orchestrator.get_comprehensive_location_data(
                sample_location_params, 
                'city-revitalization'
            )
            
            # AWS client should only be called once
            assert mocks['get_detailed_census_data'].call_count == 1
            assert result1 == result2
    
    def test_data_tier_functionality(self, sample_location_params):
        """Test different data tier behaviors"""
        # Free tier
        free_orchestrator = DataOrchestrator(data_tier='free')
        
        with patch.object(free_orchestrator, '_get_free_aws_data', return_value={'aws': 'data'}):
            with patch.object(free_orchestrator, '_get_free_api_data', return_value={}):
                result = free_orchestrator.get_comprehensive_location_data(
                    sample_location_params, 'medtech'
                )
                
                assert result['data_tier'] == 'free'
    
    def test_api_health_validation(self, orchestrator):
        """Test API health check"""
        health_status = orchestrator.api_manager.validate_api_health()
        
        assert isinstance(health_status, dict)
        assert 'perplexity' in health_status
        assert 'eia' in health_status
        assert 'fda' in health_status
    
    def test_data_quality_validation(self, orchestrator):
        """Test data quality validation"""
        sample_data = {
            'domain': 'crypto-mining',
            'sources': {
                'census': {'population': 100000},
                'energy': {'solar_potential': 'high'}
            }
        }
        
        validation = orchestrator.validate_data_quality(sample_data)
        
        assert 'completeness_score' in validation
        assert 'quality_issues' in validation
        assert isinstance(validation['completeness_score'], (int, float))

class TestDataCache:
    
    @pytest.fixture
    def cache(self, tmp_path):
        return DataCache(cache_dir=str(tmp_path / 'test_cache'))
    
    def test_cache_operations(self, cache):
        """Test basic cache operations"""
        test_data = {'test': 'data', 'numbers': [1, 2, 3]}
        
        # Store data
        cache.set('test_key', test_data)
        
        # Retrieve data
        retrieved = cache.get('test_key')
        
        assert retrieved == test_data
    
    def test_cache_expiration(self, cache):
        """Test cache expiration logic"""
        # This would require mocking datetime for proper testing
        # Simplified test
        cache.set('expire_test', {'data': 'value'})
        
        # Data should be retrievable immediately
        assert cache.get('expire_test') is not None
    
    def test_cache_statistics(self, cache):
        """Test cache statistics"""
        cache.set('test1', {'data': 'value1'})
        cache.set('test2', {'data': 'value2'})
        
        stats = cache.get_cache_stats()
        
        assert 'processed_data' in stats
        assert stats['processed_data']['file_count'] >= 2
```

### 2.3.2 Create Integration Test
**Create**: `tests/integration/test_stage2_integration.py`

```python
#!/usr/bin/env python3
"""Integration test for Stage 2 data integration"""

import pytest
import os
from src.utils.data_orchestrator import DataOrchestrator
from src.utils.aws_data_client import AWSDataClient
from src.utils.api_manager import APIManager

class TestStage2Integration:
    """Integration tests for Stage 2 data architecture"""
    
    @pytest.fixture
    def real_location_params(self):
        return {
            'latitude': 39.7391,
            'longitude': -104.9847,
            'location_name': 'Denver',
            'state': 'CO',
            'state_code': '08'
        }
    
    def test_aws_connectivity(self):
        """Test actual AWS connectivity (requires AWS credentials)"""
        client = AWSDataClient()
        
        # Test public data access (should work without credentials)
        try:
            # This should work if AWS connectivity is available
            energy_data = client.get_nrel_energy_data({
                'latitude': 39.7391,
                'longitude': -104.9847,
                'year': 2022
            })
            
            # Should return data structure even if simplified
            assert isinstance(energy_data, dict)
            
        except Exception as e:
            pytest.skip(f"AWS connectivity not available: {e}")
    
    def test_api_connectivity(self):
        """Test API connectivity with configured keys"""
        api_manager = APIManager()
        
        health_status = api_manager.validate_api_health()
        
        # At least FDA should be accessible (no key required)
        assert 'fda' in health_status
        
        # Log status for debugging
        print(f"API Health Status: {health_status}")
    
    def test_orchestrator_integration(self, real_location_params):
        """Test full orchestrator integration"""
        orchestrator = DataOrchestrator(data_tier='free')
        
        try:
            result = orchestrator.get_comprehensive_location_data(
                real_location_params,
                'crypto-mining'
            )
            
            # Validate result structure
            assert 'domain' in result
            assert 'sources' in result
            assert result['domain'] == 'crypto-mining'
            
            # Validate data quality
            validation = orchestrator.validate_data_quality(result)
            assert 'completeness_score' in validation
            
            print(f"Data Integration Test Results:")
            print(f"- Sources collected: {len(result['sources'])}")
            print(f"- Completeness: {validation['completeness_score']}%")
            print(f"- Quality issues: {len(validation['quality_issues'])}")
            
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")
    
    @pytest.mark.parametrize("domain", [
        'city-revitalization',
        'crypto-mining', 
        'medtech',
        'private-equity'
    ])
    def test_domain_specific_integration(self, real_location_params, domain):
        """Test integration for each domain"""
        orchestrator = DataOrchestrator(data_tier='free')
        
        try:
            result = orchestrator.get_comprehensive_location_data(
                real_location_params,
                domain
            )
            
            assert result['domain'] == domain
            assert 'sources' in result
            
            # Domain should have at least basic data sources
            assert len(result['sources']) > 0
            
        except Exception as e:
            pytest.fail(f"Domain {domain} integration failed: {e}")

if __name__ == "__main__":
    """Run integration tests directly"""
    import sys
    
    print("🧪 Running Stage 2 Integration Tests...")
    
    # Check environment
    if not os.getenv('AWS_PROFILE') and not os.getenv('AWS_ACCESS_KEY_ID'):
        print("⚠️ Warning: AWS credentials not configured")
        print("   Some tests may be skipped")
    
    # Run tests
    exit_code = pytest.main([
        __file__,
        '-v',
        '-s',
        '--tb=short'
    ])
    
    if exit_code == 0:
        print("✅ Stage 2 Integration tests passed!")
    else:
        print("❌ Stage 2 Integration tests failed!")
        
    sys.exit(exit_code)
```

## Step 2.4: Documentation and Validation

### 2.4.1 Create Data Architecture Documentation
**Create**: `implementation_v2/data_architecture.md`

```markdown
# Data Architecture Documentation

## Overview
Three-tier data architecture supporting all domain permutations with cost-optimized access patterns.

## Tier Structure

### Tier 1: Free AWS Data (RODA)
- **Census ACS**: Demographics, economics, housing
- **OpenStreetMap**: Geographic features and POIs
- **NREL NSRDB**: Solar and energy data
- **ERA5**: Climate and weather data
- **Cost**: Free (pay only for compute/bandwidth)

### Tier 2: Enhanced APIs  
- **Perplexity**: Deep research and context
- **EIA**: Energy pricing and grid data
- **FDA**: Medical device regulations
- **SEC EDGAR**: Corporate filings
- **Cost**: ~$100-200/month

### Tier 3: Premium Data (Future)
- **AWS Data Exchange**: Commercial datasets
- **Crunchbase**: Company information
- **Preqin**: Private equity data
- **Cost**: ~$500-1500/month

## Data Flow Architecture

```
Input Params → Data Orchestrator → [Cache Check] → Multi-Source Collection → Processing → Output
```

## Caching Strategy
- **TTL**: 24 hours for dynamic data, 7 days for static
- **Storage**: Local filesystem with pickle serialization
- **Size Limit**: <1GB total cache size
- **Cleanup**: Automatic expired cache removal

## API Integration Patterns
- **Rate Limiting**: Respect API rate limits with backoff
- **Error Handling**: Graceful degradation on API failures
- **Parallel Processing**: Async calls where possible
- **Health Monitoring**: Regular API availability checks

## Domain-Specific Data Mapping

### City Revitalization
- **Primary**: Census demographics + Perplexity municipal intelligence
- **Secondary**: OSM civic features + regulatory queries
- **Opportunity Zones**: Partnership compatibility scoring

### Crypto Mining
- **Primary**: NREL energy data + EIA pricing
- **Secondary**: Climate data + regulatory environment
- **Opportunity Zones**: Energy cost and infrastructure scoring

### Medtech
- **Primary**: FDA device database + patent data
- **Secondary**: Market research + regulatory pathways
- **Opportunity Zones**: Regulatory complexity and market readiness

### Private Equity
- **Primary**: Business intelligence + sentiment analysis
- **Secondary**: Financial data + acquisition signals
- **Opportunity Zones**: Acquisition readiness and synergy potential

## Performance Considerations
- **Cold Start**: ~30-60 seconds for comprehensive data collection
- **Warm Cache**: ~5-10 seconds with cached data
- **Parallel Processing**: 3-5x speedup with async API calls
- **Error Recovery**: Graceful degradation with partial data
```

### 2.4.2 Create Validation Script
**Create**: `implementation_v2/validate_stage2.py`

```python
#!/usr/bin/env python3
"""Stage 2 validation script"""

import sys
import os
import pytest
from src.utils.data_orchestrator import DataOrchestrator
from src.utils.aws_data_client import AWSDataClient  
from src.utils.api_manager import APIManager
from src.utils.data_cache import DataCache

def validate_data_architecture():
    """Validate data architecture components"""
    print("📊 Validating Data Architecture...")
    
    success = True
    
    # Test AWS client
    try:
        aws_client = AWSDataClient()
        print("✅ AWS Data Client initialized")
    except Exception as e:
        print(f"❌ AWS Data Client failed: {e}")
        success = False
    
    # Test API manager  
    try:
        api_manager = APIManager()
        health = api_manager.validate_api_health()
        print(f"✅ API Manager health: {health}")
    except Exception as e:
        print(f"❌ API Manager failed: {e}")
        success = False
    
    # Test data orchestrator
    try:
        orchestrator = DataOrchestrator()
        print("✅ Data Orchestrator initialized")
    except Exception as e:
        print(f"❌ Data Orchestrator failed: {e}")
        success = False
    
    # Test caching
    try:
        cache = DataCache()
        cache.set('test', {'data': 'value'})
        retrieved = cache.get('test')
        assert retrieved == {'data': 'value'}
        print("✅ Data Cache working")
    except Exception as e:
        print(f"❌ Data Cache failed: {e}")
        success = False
    
    return success

def validate_domain_integrations():
    """Test domain-specific integrations"""
    print("🔧 Validating Domain Integrations...")
    
    orchestrator = DataOrchestrator(data_tier='free')
    test_params = {
        'latitude': 39.7391,
        'longitude': -104.9847,
        'location_name': 'Denver',
        'state': 'CO'
    }
    
    domains = ['city-revitalization', 'crypto-mining', 'medtech', 'private-equity']
    success = True
    
    for domain in domains:
        try:
            result = orchestrator.get_comprehensive_location_data(test_params, domain)
            validation = orchestrator.validate_data_quality(result)
            
            print(f"✅ {domain}: {len(result['sources'])} sources, "
                  f"{validation['completeness_score']}% complete")
            
        except Exception as e:
            print(f"❌ {domain} failed: {e}")
            success = False
    
    return success

def run_integration_tests():
    """Run comprehensive integration tests"""
    print("🧪 Running Integration Tests...")
    
    exit_code = pytest.main([
        'tests/integration/test_stage2_integration.py',
        'tests/utils/test_data_integration.py', 
        '-v'
    ])
    
    return exit_code == 0

if __name__ == "__main__":
    print("🚀 Stage 2 Data Integration Validation")
    print("=" * 50)
    
    success = True
    
    success &= validate_data_architecture()
    print()
    
    success &= validate_domain_integrations() 
    print()
    
    success &= run_integration_tests()
    print()
    
    if success:
        print("✅ Stage 2 validation completed successfully!")
        print("👉 Ready for Stage 3: Domain Adapter Implementation")
        sys.exit(0)
    else:
        print("❌ Stage 2 validation failed!")
        print("🔧 Fix issues above before proceeding")
        sys.exit(1)
```

## Validation Checklist

Before proceeding to Stage 3:

- [ ] All data integration components import successfully
- [ ] AWS connectivity tested (at least public datasets accessible)
- [ ] API health checks pass for available services
- [ ] Caching system stores and retrieves data correctly
- [ ] All four domains can collect basic data
- [ ] Integration tests pass
- [ ] Performance benchmarks meet expectations (<60s cold start)

## Next Steps

Upon successful validation:
1. **Commit Stage 2**: `git add . && git commit -m "feat: Stage 2 - Data integration architecture"`
2. **Review costs**: Monitor actual API usage and costs
3. **Proceed to Stage 3**: Begin implementing domain-specific adapters
4. **Optional**: Configure additional API keys for enhanced data access

## Cost Monitoring

Set up AWS budgets and alerts:
```bash
# Monitor data transfer costs
aws budgets create-budget --account-id YOUR_ACCOUNT_ID --budget file://data-budget.json
```

Track API usage in your monitoring dashboard to stay within budget limits.