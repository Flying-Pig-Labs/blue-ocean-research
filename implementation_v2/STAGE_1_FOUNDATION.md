# Stage 1: Foundation Setup (Week 1)

## Objective
Establish the core infrastructure for multi-domain pipeline support without breaking existing functionality.

## Prerequisites Checklist
- [ ] Current pipeline runs successfully with existing business ideas domain
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] AWS credentials configured for S3/Athena access
- [ ] Environment variables from CLAUDE.md are set

## Step 1.1: Create Domain Architecture (Day 1)

### 1.1.1 Create Domain Adapter Base Class
```bash
mkdir -p src/domain_adapters
touch src/domain_adapters/__init__.py
```

**Create**: `src/domain_adapters/base_adapter.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseDomainAdapter(ABC):
    """Base class for all domain-specific adapters"""
    
    def __init__(self, domain_type: str):
        self.domain_type = domain_type
        self.aws_datasets = self._initialize_aws_sources()
        self.api_sources = self._initialize_api_sources()
    
    @abstractmethod
    def get_opportunity_zone_data(self, input_params: Dict) -> Dict:
        """Fetch domain-specific data for opportunity zone analysis"""
        pass
    
    @abstractmethod
    def get_opportunity_dimensions(self) -> Dict[str, List[str]]:
        """Return domain-specific pain/opportunity dimensions"""
        pass
    
    @abstractmethod
    def generate_domain_output(self, zones: List[Dict]) -> Dict:
        """Generate domain-specific final output"""
        pass
    
    def _initialize_aws_sources(self) -> Dict:
        """Initialize AWS data source connections"""
        return {}
    
    def _initialize_api_sources(self) -> Dict:
        """Initialize external API connections"""
        return {}
```

### 1.1.2 Update Core Pipeline Configuration
**Modify**: `src/config.py` (create if doesn't exist)
```python
import os
from enum import Enum

class DomainType(Enum):
    BUSINESS_IDEAS = "business-ideas"
    CITY_REVITALIZATION = "city-revitalization" 
    CRYPTO_MINING = "crypto-mining"
    MEDTECH = "medtech"
    PRIVATE_EQUITY = "private-equity"

class PipelineConfig:
    def __init__(self):
        self.domain_type = DomainType(os.getenv('DOMAIN_TYPE', 'business-ideas'))
        self.output_format = os.getenv('OUTPUT_FORMAT', 'product-ideas')
        self.data_tier = os.getenv('DATA_TIER', 'free')  # free, enhanced, premium
        
    def get_adapter_class(self):
        """Return appropriate adapter class for domain"""
        if self.domain_type == DomainType.BUSINESS_IDEAS:
            return None  # Use existing pipeline
        elif self.domain_type == DomainType.CITY_REVITALIZATION:
            from .domain_adapters.city_revitalization_adapter import CityRevitalizationAdapter
            return CityRevitalizationAdapter
        # Add other domains as implemented
        else:
            raise ValueError(f"Unsupported domain: {self.domain_type}")
```

## Step 1.2: Create Data Integration Foundation (Day 2)

### 1.2.1 AWS Data Access Utility
**Create**: `src/utils/aws_data_client.py`
```python
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AWSDataClient:
    """Unified client for accessing AWS public datasets"""
    
    def __init__(self):
        # No-sign-request client for public data
        self.s3_unsigned = boto3.client('s3', 
            config=Config(signature_version=UNSIGNED))
        
        # Regular client for Athena queries
        self.athena = boto3.client('athena')
        self.s3 = boto3.client('s3')
        
    def get_census_data(self, location_filter: str) -> pd.DataFrame:
        """Get Census ACS data for location"""
        try:
            # Example: Download and filter census data
            bucket = 'uscensus-pms'
            key = 'acs2019_5yr/data.csv'
            
            obj = self.s3_unsigned.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(obj['Body'])
            
            # Apply location filter
            filtered_df = df[df['geography'].str.contains(location_filter, na=False)]
            logger.info(f"Retrieved {len(filtered_df)} census records for {location_filter}")
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error fetching census data: {e}")
            return pd.DataFrame()
    
    def get_energy_data(self, state: str) -> Dict[str, Any]:
        """Get NREL energy data for state"""
        try:
            # Access NREL NSRDB data
            bucket = 'nrel-pds-nsrdb'
            # Simplified example - actual implementation would handle HDF5 files
            logger.info(f"Fetching energy data for {state}")
            return {"solar_potential": "high", "wind_potential": "medium"}
            
        except Exception as e:
            logger.error(f"Error fetching energy data: {e}")
            return {}
    
    def query_athena(self, query: str, database: str = 'default') -> pd.DataFrame:
        """Execute Athena query and return results"""
        try:
            response = self.athena.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                WorkGroup='primary'
            )
            
            query_execution_id = response['QueryExecutionId']
            
            # Wait for query completion (simplified)
            # In production, implement proper polling
            
            results = self.athena.get_query_results(
                QueryExecutionId=query_execution_id
            )
            
            # Convert to DataFrame (simplified)
            return pd.DataFrame()  # Placeholder
            
        except Exception as e:
            logger.error(f"Athena query failed: {e}")
            return pd.DataFrame()
```

### 1.2.2 API Integration Manager
**Create**: `src/utils/api_manager.py`
```python
import os
import requests
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class APIManager:
    """Centralized API client for external data sources"""
    
    def __init__(self):
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.eia_api_key = os.getenv('EIA_API_KEY')  # Free registration
        self.base_urls = {
            'perplexity': 'https://api.perplexity.ai',
            'eia': 'https://api.eia.gov/v2',
            'fda': 'https://api.fda.gov',
            'edgar': 'https://www.sec.gov/edgar'
        }
    
    def perplexity_research(self, query: str, domain_context: str = "") -> Dict[str, Any]:
        """Execute Perplexity deep research query"""
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not configured")
            return {"error": "API key missing"}
            
        try:
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            enhanced_query = f"{domain_context} {query}" if domain_context else query
            
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{"role": "user", "content": enhanced_query}],
                "temperature": 0.2
            }
            
            response = requests.post(
                f"{self.base_urls['perplexity']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Perplexity API error: {response.status_code}")
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Perplexity API request failed: {e}")
            return {"error": str(e)}
    
    def get_energy_prices(self, state: str) -> Dict[str, Any]:
        """Get energy prices from EIA API"""
        if not self.eia_api_key:
            logger.warning("EIA API key not configured")
            return {"error": "API key missing"}
            
        try:
            url = f"{self.base_urls['eia']}/electricity/retail-sales/data/"
            params = {
                'api_key': self.eia_api_key,
                'frequency': 'monthly',
                'data[0]': 'price',
                'facets[stateid][]': state,
                'facets[sectorid][]': 'IND'  # Industrial rates
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"EIA API error: {response.status_code}")
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"EIA API request failed: {e}")
            return {"error": str(e)}
    
    def get_fda_device_data(self, device_type: str) -> Dict[str, Any]:
        """Get FDA device data"""
        try:
            url = f"{self.base_urls['fda']}/device/510k.json"
            params = {
                'search': f'device_name:"{device_type}"',
                'limit': 50
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"FDA API error: {response.status_code}")
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"FDA API request failed: {e}")
            return {"error": str(e)}
```

## Step 1.3: Update Main Pipeline (Day 3)

### 1.3.1 Modify run_pipeline.py
**Add to top of run_pipeline.py** (after existing imports):
```python
# Import new configuration
from src.config import PipelineConfig, DomainType
from src.utils.aws_data_client import AWSDataClient
from src.utils.api_manager import APIManager
```

**Add after argument parsing** (around line 150):
```python
# Initialize domain configuration
pipeline_config = PipelineConfig()
domain_adapter = None

# Initialize domain adapter if not using legacy business ideas
if pipeline_config.domain_type != DomainType.BUSINESS_IDEAS:
    adapter_class = pipeline_config.get_adapter_class()
    if adapter_class:
        domain_adapter = adapter_class(pipeline_config.domain_type.value)
        logger.info(f"Initialized {pipeline_config.domain_type.value} domain adapter")
```

### 1.3.2 Add Domain Detection Logic
**Add before Stage 1 execution** (around line 300):
```python
def should_use_domain_adapter(pipeline_config):
    """Determine if we should use domain adapter or legacy pipeline"""
    return pipeline_config.domain_type != DomainType.BUSINESS_IDEAS

def run_domain_pipeline(domain_adapter, research_data):
    """Execute domain-specific pipeline"""
    logger.info(f"Running domain pipeline: {domain_adapter.domain_type}")
    
    # Stage 1: Get domain-specific opportunity data
    opportunity_data = domain_adapter.get_opportunity_zone_data(research_data)
    
    # Stage 2: Use domain-specific dimensions for analysis
    dimensions = domain_adapter.get_opportunity_dimensions()
    
    # Stage 3: Generate domain output
    final_output = domain_adapter.generate_domain_output(opportunity_data)
    
    return final_output
```

## Step 1.4: Testing Foundation (Day 4)

### 1.4.1 Create Test Structure
```bash
mkdir -p tests/domain_adapters
touch tests/domain_adapters/__init__.py
```

**Create**: `tests/domain_adapters/test_base_adapter.py`
```python
import pytest
import os
from unittest.mock import Mock, patch
from src.domain_adapters.base_adapter import BaseDomainAdapter

class TestBaseDomainAdapter:
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly"""
        # Create a concrete implementation for testing
        class TestAdapter(BaseDomainAdapter):
            def get_opportunity_zone_data(self, input_params):
                return {"test": "data"}
            
            def get_opportunity_dimensions(self):
                return {"test_dimension": ["keyword1", "keyword2"]}
            
            def generate_domain_output(self, zones):
                return {"output": "test"}
        
        adapter = TestAdapter("test-domain")
        assert adapter.domain_type == "test-domain"
        assert isinstance(adapter.aws_datasets, dict)
        assert isinstance(adapter.api_sources, dict)
    
    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented"""
        with pytest.raises(TypeError):
            BaseDomainAdapter("test")
```

**Create**: `tests/utils/test_aws_data_client.py`
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from src.utils.aws_data_client import AWSDataClient

class TestAWSDataClient:
    
    @patch('boto3.client')
    def test_client_initialization(self, mock_boto3):
        """Test AWS client initializes correctly"""
        client = AWSDataClient()
        assert client is not None
        # Verify boto3 clients were created
        assert mock_boto3.call_count >= 2
    
    @patch('src.utils.aws_data_client.pd.read_csv')
    def test_get_census_data_success(self, mock_read_csv, aws_client):
        """Test successful census data retrieval"""
        # Mock DataFrame
        mock_df = pd.DataFrame({
            'geography': ['City A', 'City B', 'City C'],
            'population': [10000, 20000, 30000]
        })
        mock_read_csv.return_value = mock_df
        
        # Mock S3 response
        aws_client.s3_unsigned.get_object.return_value = {
            'Body': Mock()
        }
        
        result = aws_client.get_census_data('City A')
        assert len(result) == 1
        assert result.iloc[0]['geography'] == 'City A'

@pytest.fixture
def aws_client():
    with patch('boto3.client'):
        return AWSDataClient()
```

### 1.4.2 Validation Script
**Create**: `tests/validate_foundation.py`
```python
#!/usr/bin/env python3
"""
Validation script for Stage 1 foundation setup
"""
import sys
import os
import importlib
import pytest

def validate_imports():
    """Validate all new modules can be imported"""
    required_modules = [
        'src.config',
        'src.domain_adapters.base_adapter',
        'src.utils.aws_data_client',
        'src.utils.api_manager'
    ]
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} imports successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            return False
    
    return True

def validate_environment():
    """Check required environment variables"""
    required_env = [
        'ANTHROPIC_API_KEY',
        'GITHUB_TOKEN'
    ]
    
    optional_env = [
        'PERPLEXITY_API_KEY',
        'EIA_API_KEY',
        'DOMAIN_TYPE',
        'DATA_TIER'
    ]
    
    for var in required_env:
        if not os.getenv(var):
            print(f"❌ Required environment variable missing: {var}")
            return False
        print(f"✅ {var} is set")
    
    for var in optional_env:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️ Optional environment variable not set: {var}")
    
    return True

def validate_tests():
    """Run foundation tests"""
    try:
        exit_code = pytest.main([
            'tests/domain_adapters/test_base_adapter.py',
            'tests/utils/test_aws_data_client.py',
            '-v'
        ])
        return exit_code == 0
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Validating Stage 1 Foundation Setup...")
    
    success = True
    
    print("\n📦 Validating imports...")
    success &= validate_imports()
    
    print("\n🔧 Validating environment...")
    success &= validate_environment()
    
    print("\n🧪 Running tests...")
    success &= validate_tests()
    
    if success:
        print("\n✅ Stage 1 Foundation validation passed!")
        print("👉 Proceed to Stage 2: Data Integration")
        sys.exit(0)
    else:
        print("\n❌ Stage 1 Foundation validation failed!")
        print("🔧 Fix the issues above before proceeding")
        sys.exit(1)
```

## Step 1.5: Documentation and Handoff (Day 5)

### 1.5.1 Update Requirements
**Create**: `requirements-domain.txt`
```txt
# Additional dependencies for multi-domain support
boto3>=1.26.0
botocore>=1.29.0
pandas>=1.5.0
requests>=2.28.0
python-dotenv>=0.19.0
```

**Update**: `requirements.txt` (append)
```txt
-r requirements-domain.txt
```

### 1.5.2 Environment Configuration
**Create**: `.env.example.domain`
```env
# Domain Configuration
DOMAIN_TYPE=business-ideas  # business-ideas, city-revitalization, crypto-mining, medtech, private-equity
OUTPUT_FORMAT=product-ideas
DATA_TIER=free  # free, enhanced, premium

# API Keys (Optional for enhanced functionality)
PERPLEXITY_API_KEY=your_key_here
EIA_API_KEY=your_key_here  # Free at https://www.eia.gov/opendata/register.php
```

## Validation Checklist

Before proceeding to Stage 2, verify:

- [ ] All new modules import without errors
- [ ] Tests pass: `python tests/validate_foundation.py`
- [ ] Existing pipeline still works: `python run_pipeline.py --skip-github`
- [ ] AWS credentials configured (for data access)
- [ ] Environment variables set (copy from .env.example.domain)
- [ ] No breaking changes to current functionality

## Next Steps

Upon successful validation:
1. Commit changes: `git add . && git commit -m "feat: Stage 1 - Multi-domain foundation setup"`
2. Proceed to `STAGE_2_DATA_INTEGRATION.md`
3. Begin implementing specific domain adapters

## Troubleshooting

**Import Errors**: Ensure `src/` is in Python path or install package in development mode
```bash
pip install -e .
```

**AWS Access Issues**: Verify credentials with:
```bash
aws sts get-caller-identity
```

**Test Failures**: Run individual tests with verbose output:
```bash
python -m pytest tests/domain_adapters/test_base_adapter.py -v -s
```