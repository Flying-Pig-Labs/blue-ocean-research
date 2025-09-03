# 📋 Frontend Form Configuration Reference

This document maps the frontend form fields to our modular pipeline system flavors and ensures complete alignment between user input and research execution.

## 🎯 Research Type Mapping

Our modular system flavors align with these 5 research types:

| Frontend Research Type | Pipeline Flavor | Framework Used |
|----------------------|-----------------|----------------|
| `innovation` | `baseline` | ERRC (Blue Ocean) |
| `medical-device` | `medical_devices` | SPEC-TRACE |
| `private-equity` | `private_equity_acquisitions` | ACQUIRE |
| `city-revitalization` | `city_revitalization` | UNIFY |
| `crypto-mining` | `crypto_mining_viability` | Mining Viability (9 Modules) |

---

## 📝 Page 1: Research Configuration (Use-Case Specific)

### 💡 Innovation Research → `baseline` Flavor
```yaml
# Maps to baseline ERRC configuration
form_fields:
  forest_description: 
    type: textarea
    required: true
    placeholder: "Tell us about the market landscape, competitive environment, or product space you want to explore..."
    maps_to: research_analysis.context_description
  
  company_project_name:
    type: text
    required: false
    placeholder: "Your company or project"
    maps_to: github.repo_naming_pattern
  
  industry_focus:
    type: text
    required: false
    placeholder: "e.g., SaaS, Healthcare, FinTech"
    maps_to: reddit_strategy.seed_terms
```

### 🏥 Medical Device Research → `medical_devices` Flavor
```yaml
# Maps to SPEC-TRACE framework configuration
form_fields:
  clinical_area:
    type: text
    required: true
    placeholder: "e.g., Cardiology, orthopedic spine surgery, type 2 diabetes management, glaucoma"
    maps_to: reddit_strategy.seed_terms + framework.analysis_dimensions
  
  fda_regulatory_pathway:
    type: two_button_selector
    options: ["510(k) Clearance", "PMA Approval"]
    maps_to: output.required_fields.regulatory_pathway
  
  primary_care_setting:
    type: three_pill_buttons
    options: ["Outpatient", "Inpatient", "Home Care"]
    maps_to: output.required_fields.target_setting
  
  technology_maturity_level:
    type: three_step_slider
    levels: ["1-Early stage", "2-Working prototype", "3-Clinical validation"]
    maps_to: framework.params.category_overrides
```

### 💰 Private Equity Research → `private_equity_acquisitions` Flavor
```yaml
# Maps to ACQUIRE framework configuration
form_fields:
  target_fragmented_industry:
    type: text
    required: true
    placeholder: "e.g., HVAC services, veterinary clinics, dental practices, managed IT services"
    maps_to: thesis_preferences.target_industries
  
  target_company_profile:
    type: three_vertical_buttons
    options: ["Founder-Led", "Family-Owned", "Management-Owned"]
    maps_to: thesis_preferences.ownership_types
  
  primary_value_driver:
    type: four_pill_buttons
    options: ["Consolidation", "Digitization", "Geographic Expansion", "Operational Excellence"]
    maps_to: thesis_preferences.primary_value_drivers
  
  seller_motivation:
    type: dropdown
    options: [
      "Founder Retirement",
      "Succession Planning", 
      "Growth Capital Needs",
      "Liquidity Event",
      "Strategic Pivot",
      "Market Pressure"
    ]
    maps_to: thesis_preferences.seller_motivation_weights
```

### 🏙️ City Revitalization Research → `city_revitalization` Flavor
```yaml
# Maps to UNIFY framework configuration
form_fields:
  city_municipality_county:
    type: text
    required: true
    placeholder: "e.g., Richmond, Virginia; Franklin County, Ohio; Bronzeville neighborhood in Chicago"
    maps_to: reddit_strategy.subreddit_hints + framework.clustering.required_dimensions
  
  development_focus_area:
    type: dropdown
    options: [
      "Downtown Revitalization",
      "Residential Development", 
      "Mixed-Use Districts",
      "Industrial Redevelopment",
      "Waterfront Development",
      "Historic Preservation",
      "Transit-Oriented Development"
    ]
    maps_to: reddit_strategy.seed_terms + framework.analysis_dimensions
  
  target_population:
    type: two_button_selector
    options: ["Existing Residents", "New Residents"]
    maps_to: framework.params.callouts.gather_stakeholders
  
  local_government_contribution:
    type: three_button_selector
    options: ["Funding", "Land", "Regulatory"]
    maps_to: output.required_fields.funding_channels
```

### ⛏️ Crypto Mining Research → `crypto_mining_viability` Flavor
```yaml
# Maps to Mining Viability framework with 9 core modules (M1-M9)
form_fields:
  target_mining_regions:
    type: text
    required: true
    placeholder: "e.g., Texas, Paraguay, Quebec, Norway, Kazakhstan"
    maps_to: user_inputs.preferred_regions + reddit_strategy.seed_terms
  
  investment_budget:
    type: four_button_selector
    options: ["$1-5M", "$5-15M", "$15-50M", "$50M+"]
    maps_to: user_inputs.budget_usd
  
  power_arrangement_preference:
    type: three_pill_buttons
    options: ["Grid Power", "PPA/Renewables", "Stranded/Flare Gas"]
    maps_to: user_inputs.power_pref
  
  timeline_to_production:
    type: three_button_selector
    options: ["Fast (<4 months)", "Standard (4-8 months)", "Extended (8+ months)"]
    maps_to: user_inputs.timeline_days
  
  mining_scale_preference:
    type: three_step_slider
    levels: ["1-Small (1-5MW)", "2-Medium (5-20MW)", "3-Large (20MW+)"]
    maps_to: user_inputs.min_scale_mw + user_inputs.max_scale_mw
  
  power_cost_tolerance:
    type: slider_with_numeric
    min: 0.02
    max: 0.10
    step: 0.005
    default: 0.05
    unit: "$/kWh"
    maps_to: user_inputs.max_kwh
```

---

## ⚙️ Page 2: Strategic Configuration (Applies to All Research Types)

### 💵 Investment Scale → All Flavors
```yaml
investment_scale:
  type: four_grid_button_selector
  options: [
    "Seed ($0-1M)",
    "Growth ($1-25M)", 
    "Scale ($25-100M)",
    "Enterprise ($100M+)"
  ]
  maps_to:
    private_equity: thesis_preferences.size_bounds
    medical_device: framework.params.category_overrides
    city_revitalization: output.required_fields.funding_channels
    crypto_mining: user_inputs.budget_usd
    innovation: stage_overrides.idea_generation.total_ideas
```

### ⏱️ Timeline → All Flavors
```yaml
timeline:
  type: three_button_selector_with_icons
  options: [
    "Short-term (<2 years)",
    "Medium-term (2-5 years)", 
    "Long-term (5+ years)"
  ]
  maps_to:
    private_equity: synthesis.default_terms.diligence_period_days
    medical_device: output.required_fields.time_to_market
    city_revitalization: output.required_fields.timeline_milestones
    crypto_mining: user_inputs.timeline_days
    innovation: stage_overrides.opportunity_zones.stage2_reasoning_effort
```

### 📊 Risk Profile → All Flavors
```yaml
risk_profile:
  type: three_button_selector_with_icons
  options: [
    "Conservative (Lower risk)",
    "Moderate (Balanced)",
    "Aggressive (Higher risk)"
  ]
  maps_to:
    private_equity: 
      - thesis_preferences.negative_screens
      - framework.params.weights.R (risk weight)
    medical_device: framework.params.weights.SR (safety risk)
    city_revitalization: framework.params.weights.RS (resilience)
    crypto_mining: user_inputs.risk_tolerance
    innovation: framework.clustering.pain_dimension_threshold
```

### 🌐 Research Topology → All Flavors
```yaml
research_topology:
  type: three_button_selector_special_styling
  options: [
    "hierarchical",
    "byzantine", 
    "federated" # recommended - highlighted in amber
  ]
  maps_to:
    ALL_FLAVORS: framework.clustering.algorithm
  special_handling:
    federated: 
      recommended: true
      style: amber_highlight
      maps_to: "hierarchical" # Backend translation
```

---

## 🔄 Form-to-Pipeline Mapping Logic

### Configuration Translation Function
```python
def translate_form_to_flavor_config(form_data: Dict[str, Any], research_type: str) -> Dict[str, Any]:
    """Translate frontend form data to pipeline flavor configuration."""
    
    # Base mapping by research type
    flavor_mapping = {
        'innovation': 'baseline',
        'medical-device': 'medical_devices', 
        'private-equity': 'private_equity_acquisitions',
        'city-revitalization': 'city_revitalization',
        'crypto-mining': 'crypto_mining_viability'
    }
    
    flavor_name = flavor_mapping[research_type]
    
    # Load base flavor config
    registry = FlavorRegistry(flavors_dir="flavors")
    base_config = registry.get_flavor(flavor_name)
    
    # Apply form-specific overrides
    if research_type == 'private-equity':
        # Map PE-specific fields
        base_config.thesis_preferences['target_industries'] = [form_data['target_fragmented_industry']]
        base_config.thesis_preferences['ownership_types'] = [form_data['target_company_profile']]
        base_config.thesis_preferences['primary_value_drivers'] = [form_data['primary_value_driver']]
        
        # Map investment scale to size bounds
        scale_mapping = {
            'Seed ($0-1M)': {'revenue_min': 0, 'revenue_max': 1000000},
            'Growth ($1-25M)': {'revenue_min': 1000000, 'revenue_max': 25000000},
            'Scale ($25-100M)': {'revenue_min': 25000000, 'revenue_max': 100000000},
            'Enterprise ($100M+)': {'revenue_min': 100000000, 'revenue_max': 1000000000}
        }
        base_config.thesis_preferences['size_bounds'] = scale_mapping[form_data['investment_scale']]
        
    elif research_type == 'medical-device':
        # Map medical device fields
        base_config.reddit_strategy.seed_terms.append(form_data['clinical_area'])
        base_config.output.required_fields.append('regulatory_pathway')
        
        # Map FDA pathway to SPEC-TRACE weights
        if form_data['fda_regulatory_pathway'] == 'PMA Approval':
            base_config.framework.params['weights']['RC'] = 0.20  # Higher regulatory complexity
            
    elif research_type == 'city-revitalization':
        # Map city revitalization fields
        location = form_data['city_municipality_county']
        base_config.reddit_strategy.seed_terms.extend([
            location,
            form_data['development_focus_area'].lower()
        ])
        
    elif research_type == 'crypto-mining':
        # Map crypto mining fields
        regions = form_data['target_mining_regions'].split(', ')
        base_config.user_inputs['preferred_regions'] = [r.strip() for r in regions]
        
        # Map investment budget to USD value
        budget_mapping = {
            '$1-5M': 3000000,      # Mid-range of $1-5M
            '$5-15M': 10000000,    # Mid-range of $5-15M
            '$15-50M': 32000000,   # Mid-range of $15-50M
            '$50M+': 75000000      # Large scale
        }
        base_config.user_inputs['budget_usd'] = budget_mapping[form_data['investment_budget']]
        
        # Map power arrangement preference
        power_mapping = {
            'Grid Power': ['grid'],
            'PPA/Renewables': ['ppa', 'renewable'],
            'Stranded/Flare Gas': ['flare', 'stranded']
        }
        base_config.user_inputs['power_pref'] = power_mapping[form_data['power_arrangement_preference']]
        
        # Map timeline to days
        timeline_mapping = {
            'Fast (<4 months)': 120,      # 4 months
            'Standard (4-8 months)': 180,  # 6 months
            'Extended (8+ months)': 300    # 10 months
        }
        base_config.user_inputs['timeline_days'] = timeline_mapping[form_data['timeline_to_production']]
        
        # Map mining scale to MW
        scale_mapping = {
            '1-Small (1-5MW)': {'min': 1.0, 'max': 5.0},
            '2-Medium (5-20MW)': {'min': 5.0, 'max': 20.0},
            '3-Large (20MW+)': {'min': 20.0, 'max': 50.0}
        }
        scale = scale_mapping[form_data['mining_scale_preference']]
        base_config.user_inputs['min_scale_mw'] = scale['min']
        base_config.user_inputs['max_scale_mw'] = scale['max']
        
        # Map power cost tolerance
        base_config.user_inputs['max_kwh'] = form_data['power_cost_tolerance']
        
    # Apply universal strategic configuration
    risk_mapping = {
        'Conservative (Lower risk)': 0.3,
        'Moderate (Balanced)': 0.5,
        'Aggressive (Higher risk)': 0.7
    }
    base_config.framework.clustering.pain_dimension_threshold = risk_mapping[form_data['risk_profile']]
    
    # Map topology (all use hierarchical backend)
    base_config.framework.clustering.algorithm = "hierarchical"
    
    return base_config
```

---

## ✅ Alignment Verification Checklist

### Current Implementation Status
- [x] **Innovation** → `baseline` flavor with ERRC framework ✅
- [x] **Medical Device** → `medical_devices` flavor with SPEC-TRACE framework ✅
- [x] **Private Equity** → `private_equity_acquisitions` flavor with ACQUIRE framework ✅
- [x] **City Revitalization** → `city_revitalization` flavor with UNIFY framework ✅
- [x] **Crypto Mining** → `crypto_mining_viability` flavor with Mining Viability framework (9 modules) ✅

### Required Form Integration Points
- [ ] **Form-to-Config Translation Layer** (needs implementation)
- [ ] **Dynamic Flavor Selection** based on research_type
- [ ] **Strategic Config Application** across all flavors
- [ ] **Research Topology Mapping** (federated → hierarchical)
- [ ] **Investment Scale Size Bounds** mapping

### Pipeline Execution Flow
```bash
# Frontend form submission triggers:
1. Form data → translate_form_to_flavor_config()
2. Research type → flavor selection
3. Strategic config → parameter overrides
4. Pipeline execution → python run_pipeline_modular.py --flavor {selected_flavor} --config {form_overrides}
5. Results → GitHub repo with 10 issues matching form criteria
```

This reference ensures our modular pipeline system perfectly aligns with the frontend form structure and user expectations! 🎯