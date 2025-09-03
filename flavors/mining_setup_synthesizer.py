#!/usr/bin/env python3
"""
Mining Setup Synthesizer - Generate Top 10 Viable Mining Configurations

Synthesizes comprehensive mining setups with execution packets based on mining viability
framework analysis. Each setup includes complete hardware, power, financial, and 
execution specifications for immediate implementation.
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class HardwareBill:
    """Complete hardware bill of materials for mining setup."""
    asic_model: str
    asic_quantity: int
    unit_hashrate_th: float
    unit_power_w: int
    unit_cost_usd: int
    total_hashrate_th: float
    total_power_kw: float
    total_cost_usd: int
    efficiency_wth: float
    vendor_options: List[str]
    lead_time_weeks: int
    cooling_method: str
    additional_equipment: Dict[str, Any]

@dataclass
class PowerPlan:
    """Power arrangement and contracting details."""
    power_source: str  # grid, ppa, flare
    contracted_rate_kwh: float
    minimum_mw: float
    maximum_mw: float
    contract_tenor_years: int
    curtailment_risk: str  # low/medium/high
    uptime_guarantee_pct: float
    lead_time_energize_weeks: int
    utility_company: str
    interconnection_cost_usd: int
    backup_power: bool

@dataclass
class FinancialBreakdown:
    """Complete financial analysis and projections."""
    capex_breakdown: Dict[str, int]
    opex_breakdown: Dict[str, int]
    total_capex_usd: int
    monthly_opex_usd: int
    payback_months_base: int
    payback_months_bear: int
    payback_months_bull: int
    irr_pct_base: float
    irr_pct_bear: float
    irr_pct_bull: float
    break_even_btc_price: float
    cashflow_curve_months: List[Dict[str, float]]
    sensitivity_analysis: Dict[str, Dict[str, float]]

@dataclass
class ExecutionTimeline:
    """Project execution timeline with critical path."""
    total_timeline_weeks: int
    critical_path: List[str]
    milestones: List[Dict[str, Any]]
    dependencies: List[Dict[str, str]]
    risk_buffer_weeks: int
    earliest_production: str  # ISO date
    full_capacity: str  # ISO date

@dataclass
class MiningSetup:
    """Complete mining setup specification with execution packet."""
    setup_id: str
    region_power_hardware_config: str
    viability_score: float
    
    # Hardware and infrastructure
    bill_of_hardware: HardwareBill
    power_plan: PowerPlan
    setup_friction_score: float
    
    # Financial analysis
    capex_breakdown: Dict[str, int]
    opex_breakdown: Dict[str, int] 
    financial_projections: FinancialBreakdown
    cashflow_curve: List[Dict[str, float]]
    sensitivity_analysis: Dict[str, Dict[str, float]]
    
    # Execution details
    execution_timeline: ExecutionTimeline
    critical_dependencies: List[str]
    customs_shipping_plan: Dict[str, Any]
    draft_contracts_rfqs: List[Dict[str, str]]
    
    # Risk assessment
    disqualifiers: List[str]
    mitigation_options: List[str]
    
    # Supporting data
    citations: List[str]
    vendor_shortlists: List[Dict[str, Any]]
    curtailment_risk_details: str
    failure_scenarios: List[Dict[str, str]]
    expansion_roadmap: List[Dict[str, Any]]

class MiningSetupSynthesizer:
    """Synthesizes complete mining setups from viability analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize synthesizer with configuration."""
        self.config = config
        self.user_inputs = config.get('user_inputs', {})
        self.data_connectors = config.get('data_connectors', {})
        self.output_config = config.get('output', {})
        
        # Mining viability parameters
        self.budget_usd = self.user_inputs.get('budget_usd', 5000000)
        self.timeline_days = self.user_inputs.get('timeline_days', 120)
        self.preferred_regions = self.user_inputs.get('preferred_regions', ['US-TX', 'PY', 'CA-QC'])
        self.power_pref = self.user_inputs.get('power_pref', ['grid', 'ppa', 'flare'])
        self.mining_asset = self.user_inputs.get('mining_asset', 'BTC')
        self.risk_tolerance = self.user_inputs.get('risk_tolerance', 'medium')
        self.max_kwh = self.user_inputs.get('max_kwh', 0.05)
        self.min_scale_mw = self.user_inputs.get('min_scale_mw', 1.0)
        
    def synthesize_mining_setups(self, analyzed_zones: List[Dict[str, Any]], target_count: int = 10) -> List[MiningSetup]:
        """
        Synthesize top viable mining setups from analyzed opportunity zones.
        
        Args:
            analyzed_zones: Zones analyzed with mining viability framework
            target_count: Number of setups to generate (default 10)
            
        Returns:
            List of MiningSetup objects with complete execution packets
        """
        logger.info(f"Synthesizing {target_count} mining setups from {len(analyzed_zones)} analyzed zones")
        
        # Sort zones by viability score
        sorted_zones = sorted(analyzed_zones, 
                            key=lambda z: z.get('framework_analysis', {}).get('overall_score', 0), 
                            reverse=True)
        
        # Take top zones for setup generation
        top_zones = sorted_zones[:target_count]
        
        mining_setups = []
        
        for i, zone in enumerate(top_zones, 1):
            try:
                setup = self._synthesize_single_setup(zone, i)
                mining_setups.append(setup)
                logger.info(f"Generated mining setup {i}: {setup.setup_id} (viability: {setup.viability_score:.3f})")
            except Exception as e:
                logger.error(f"Error generating mining setup {i}: {e}")
                continue
                
        logger.info(f"Successfully generated {len(mining_setups)} mining setups")
        return mining_setups
    
    def _synthesize_single_setup(self, zone: Dict[str, Any], rank: int) -> MiningSetup:
        """Synthesize a single comprehensive mining setup."""
        framework_analysis = zone.get('framework_analysis', {})
        enriched_data = zone.get('enriched_data', {})
        
        # Generate unique setup ID
        setup_id = f"MINING_{rank:02d}_{datetime.now().strftime('%Y%m%d')}"
        
        # Determine optimal region and configuration
        region_config = self._determine_optimal_region(zone, enriched_data)
        
        # Generate hardware bill of materials
        hardware_bill = self._generate_hardware_bill(zone, enriched_data, region_config)
        
        # Generate power plan
        power_plan = self._generate_power_plan(zone, enriched_data, region_config, hardware_bill)
        
        # Generate financial projections
        financial_breakdown = self._generate_financial_projections(hardware_bill, power_plan, zone)
        
        # Generate execution timeline
        execution_timeline = self._generate_execution_timeline(hardware_bill, power_plan, region_config)
        
        # Generate shipping and customs plan
        shipping_plan = self._generate_shipping_customs_plan(region_config, hardware_bill)
        
        # Generate draft contracts and RFQs
        contracts_rfqs = self._generate_draft_contracts_rfqs(power_plan, hardware_bill, region_config)
        
        # Assess setup friction and risks
        setup_friction = self._assess_setup_friction(zone, region_config, execution_timeline)
        disqualifiers = self._identify_disqualifiers(zone, framework_analysis)
        mitigation_options = self._generate_mitigation_options(zone, framework_analysis, disqualifiers)
        
        # Generate supporting details
        vendor_shortlists = self._generate_vendor_shortlists(hardware_bill, region_config)
        failure_scenarios = self._generate_failure_scenarios(zone, framework_analysis, hardware_bill, power_plan, financial_breakdown)
        expansion_roadmap = self._generate_expansion_roadmap(hardware_bill, power_plan, region_config)
        
        return MiningSetup(
            setup_id=setup_id,
            region_power_hardware_config=f"{region_config['region']} | {power_plan.power_source.upper()} @ {power_plan.contracted_rate_kwh:.3f}$/kWh | {hardware_bill.asic_model}",
            viability_score=framework_analysis.get('overall_score', 0),
            
            # Hardware and infrastructure
            bill_of_hardware=hardware_bill,
            power_plan=power_plan,
            setup_friction_score=setup_friction,
            
            # Financial analysis
            capex_breakdown=financial_breakdown.capex_breakdown,
            opex_breakdown=financial_breakdown.opex_breakdown,
            financial_projections=financial_breakdown,
            cashflow_curve=financial_breakdown.cashflow_curve_months,
            sensitivity_analysis=financial_breakdown.sensitivity_analysis,
            
            # Execution details
            execution_timeline=execution_timeline,
            critical_dependencies=self._extract_critical_dependencies(execution_timeline, power_plan, hardware_bill),
            customs_shipping_plan=shipping_plan,
            draft_contracts_rfqs=contracts_rfqs,
            
            # Risk assessment
            disqualifiers=disqualifiers,
            mitigation_options=mitigation_options,
            
            # Supporting data
            citations=zone.get('citations', []),
            vendor_shortlists=vendor_shortlists,
            curtailment_risk_details=self._generate_curtailment_risk_details(power_plan, zone),
            failure_scenarios=failure_scenarios,
            expansion_roadmap=expansion_roadmap
        )
    
    def _determine_optimal_region(self, zone: Dict, enriched_data: Dict) -> Dict[str, str]:
        """Determine optimal region configuration from zone analysis."""
        # Extract region from zone data or enriched data
        region = enriched_data.get('region', 'Unknown')
        
        # If not specified, select based on preferred regions and viability
        if region == 'Unknown' and self.preferred_regions:
            # Select first preferred region as default
            region = self.preferred_regions[0]
            
        return {
            'region': region,
            'country_code': region.split('-')[0] if '-' in region else region[:2],
            'state_province': region.split('-')[1] if '-' in region else '',
            'zone_designation': f"Mining Zone {zone.get('zone_id', 'Unknown')}"
        }
    
    def _generate_hardware_bill(self, zone: Dict, enriched_data: Dict, region_config: Dict) -> HardwareBill:
        """Generate complete hardware bill of materials."""
        # Get hardware data from enrichment or use defaults
        hardware_data = enriched_data.get('hardware_data', {})
        
        # Select optimal ASIC model based on efficiency and availability
        asic_models = {
            'Antminer S19 XP': {'hashrate_th': 140, 'power_w': 3010, 'efficiency_wth': 21.5, 'cost_usd': 2800},
            'Whatsminer M50S': {'hashrate_th': 126, 'power_w': 3276, 'efficiency_wth': 26.0, 'cost_usd': 2600},
            'Antminer S19j Pro': {'hashrate_th': 100, 'power_w': 3050, 'efficiency_wth': 30.5, 'cost_usd': 2200},
        }
        
        # Select model based on efficiency preference and budget
        selected_model = 'Antminer S19 XP'  # Default high-efficiency model
        if self.risk_tolerance == 'conservative':
            selected_model = 'Antminer S19j Pro'  # Lower cost, proven model
        elif self.risk_tolerance == 'aggressive':
            selected_model = 'Antminer S19 XP'  # Highest efficiency
            
        model_specs = asic_models[selected_model]
        
        # Calculate optimal quantity based on budget and minimum scale
        target_power_kw = max(self.min_scale_mw * 1000, 1000)  # At least 1MW
        unit_power_kw = model_specs['power_w'] / 1000
        min_quantity = int(target_power_kw / unit_power_kw)
        
        # Budget constraint
        max_quantity_budget = int(self.budget_usd * 0.6 / model_specs['cost_usd'])  # 60% of budget for hardware
        
        # Select final quantity
        asic_quantity = min(min_quantity, max_quantity_budget, 2000)  # Cap at 2000 units
        
        # Calculate totals
        total_hashrate = asic_quantity * model_specs['hashrate_th']
        total_power_kw = asic_quantity * model_specs['power_w'] / 1000
        total_cost = asic_quantity * model_specs['cost_usd']
        
        # Cooling method based on climate and preference
        cooling_method = 'air'  # Default
        if 'immersion' in self.user_inputs.get('cooling_pref', []):
            cooling_method = 'immersion'
        
        # Additional equipment (PDUs, networking, etc.)
        additional_equipment = {
            'PDU_count': int(asic_quantity / 12) + 1,
            'network_switches': int(asic_quantity / 48) + 1,
            'monitoring_systems': 1,
            'spare_parts_budget_usd': int(total_cost * 0.05),  # 5% spares
            'installation_cost_usd': int(total_cost * 0.08),  # 8% installation
            'shipping_cost_usd': int(total_cost * 0.03)  # 3% shipping
        }
        
        return HardwareBill(
            asic_model=selected_model,
            asic_quantity=asic_quantity,
            unit_hashrate_th=model_specs['hashrate_th'],
            unit_power_w=model_specs['power_w'],
            unit_cost_usd=model_specs['cost_usd'],
            total_hashrate_th=total_hashrate,
            total_power_kw=total_power_kw,
            total_cost_usd=total_cost,
            efficiency_wth=model_specs['efficiency_wth'],
            vendor_options=['Bitmain', 'Compass Mining', 'Crypto Miners'],
            lead_time_weeks=8,  # Default lead time
            cooling_method=cooling_method,
            additional_equipment=additional_equipment
        )
    
    def _generate_power_plan(self, zone: Dict, enriched_data: Dict, region_config: Dict, hardware_bill: HardwareBill) -> PowerPlan:
        """Generate comprehensive power arrangement plan."""
        # Get power data from enrichment
        power_data = enriched_data.get('power_data', {})
        
        # Select optimal power source from preferences
        available_sources = power_data.get('available_sources', self.power_pref)
        selected_source = available_sources[0] if available_sources else 'grid'
        
        # Power rate from data or regional estimates
        power_rates = {
            'grid': power_data.get('grid_rate_kwh', 0.06),
            'ppa': power_data.get('ppa_rate_kwh', 0.045),
            'flare': power_data.get('flare_rate_kwh', 0.025)
        }
        
        contracted_rate = min(power_rates.get(selected_source, 0.06), self.max_kwh)
        
        # Power requirements with buffer
        required_mw = hardware_bill.total_power_kw / 1000 * 1.1  # 10% buffer
        
        # Contract terms based on source
        contract_terms = {
            'grid': {'tenor': 3, 'uptime': 99.5, 'curtailment': 'low'},
            'ppa': {'tenor': 10, 'uptime': 97.0, 'curtailment': 'medium'}, 
            'flare': {'tenor': 5, 'uptime': 95.0, 'curtailment': 'high'}
        }
        
        terms = contract_terms.get(selected_source, contract_terms['grid'])
        
        # Regional utility mapping
        utilities = {
            'US-TX': 'ERCOT Texas',
            'CA-QC': 'Hydro-Quebec', 
            'PY': 'ANDE Paraguay',
            'NO': 'Statkraft Norway'
        }
        
        utility_company = utilities.get(region_config['region'], 'Regional Utility')
        
        # Interconnection costs vary by source and region
        interconnection_cost = {
            'grid': int(required_mw * 150000),  # $150k/MW
            'ppa': int(required_mw * 200000),   # $200k/MW  
            'flare': int(required_mw * 50000)   # $50k/MW
        }.get(selected_source, 150000)
        
        return PowerPlan(
            power_source=selected_source,
            contracted_rate_kwh=contracted_rate,
            minimum_mw=required_mw * 0.8,  # 80% minimum
            maximum_mw=required_mw * 1.2,  # 120% maximum
            contract_tenor_years=terms['tenor'],
            curtailment_risk=terms['curtailment'],
            uptime_guarantee_pct=terms['uptime'],
            lead_time_energize_weeks=12 if selected_source == 'grid' else 24,
            utility_company=utility_company,
            interconnection_cost_usd=interconnection_cost,
            backup_power=selected_source == 'flare'  # Backup for flare gas
        )
    
    def _generate_financial_projections(self, hardware_bill: HardwareBill, power_plan: PowerPlan, zone: Dict) -> FinancialBreakdown:
        """Generate comprehensive financial analysis and projections."""
        # CAPEX breakdown
        capex_breakdown = {
            'asic_miners': hardware_bill.total_cost_usd,
            'additional_equipment': sum(hardware_bill.additional_equipment.values()),
            'site_preparation': int(hardware_bill.total_cost_usd * 0.15),  # 15%
            'interconnection': power_plan.interconnection_cost_usd,
            'working_capital': int(hardware_bill.total_cost_usd * 0.1),  # 10%
            'contingency': int(hardware_bill.total_cost_usd * 0.08)  # 8%
        }
        total_capex = sum(capex_breakdown.values())
        
        # OPEX breakdown (monthly)
        monthly_power_cost = hardware_bill.total_power_kw * 24 * 30 * power_plan.contracted_rate_kwh
        opex_breakdown = {
            'power_cost': int(monthly_power_cost),
            'site_maintenance': int(hardware_bill.total_cost_usd * 0.002),  # 0.2% monthly
            'insurance': int(total_capex * 0.001),  # 0.1% monthly
            'management_fee': int(hardware_bill.total_cost_usd * 0.003),  # 0.3% monthly
            'repairs_replacement': int(hardware_bill.total_cost_usd * 0.001),  # 0.1% monthly
            'regulatory_compliance': 5000  # Fixed monthly
        }
        monthly_opex = sum(opex_breakdown.values())
        
        # Revenue projections (BTC mining)
        btc_price_scenarios = {'bear': 25000, 'base': 35000, 'bull': 50000}
        network_difficulty_growth = 0.03  # 3% monthly growth
        
        # Calculate payback periods and IRR for each scenario
        payback_months = {}
        irr_pct = {}
        
        for scenario, btc_price in btc_price_scenarios.items():
            # Simplified mining revenue calculation
            monthly_btc_mined = hardware_bill.total_hashrate_th / 1000000 * 6.25 * 144 * 30 / 350000  # Rough approximation
            monthly_revenue = monthly_btc_mined * btc_price
            monthly_profit = monthly_revenue - monthly_opex
            
            if monthly_profit > 0:
                payback_months[scenario] = int(total_capex / monthly_profit)
                # Simplified IRR calculation
                annual_return = monthly_profit * 12
                irr_pct[scenario] = (annual_return / total_capex) * 100
            else:
                payback_months[scenario] = 999  # Never pays back
                irr_pct[scenario] = -100
        
        # Break-even BTC price
        break_even_price = (monthly_opex / (hardware_bill.total_hashrate_th / 1000000 * 6.25 * 144 * 30 / 350000))
        
        # Generate 24-month cashflow curve (base case)
        cashflow_curve = []
        base_btc_price = btc_price_scenarios['base']
        for month in range(1, 25):
            # Account for difficulty growth
            difficulty_factor = (1 + network_difficulty_growth) ** month
            monthly_btc_mined = (hardware_bill.total_hashrate_th / 1000000 * 6.25 * 144 * 30 / 350000) / difficulty_factor
            monthly_revenue = monthly_btc_mined * base_btc_price
            monthly_profit = monthly_revenue - monthly_opex
            cumulative_profit = sum([cashflow_curve[i-1]['cumulative_profit'] for i in range(month-1)]) + monthly_profit if month > 1 else monthly_profit
            
            cashflow_curve.append({
                'month': month,
                'revenue': monthly_revenue,
                'opex': monthly_opex,
                'profit': monthly_profit,
                'cumulative_profit': cumulative_profit,
                'btc_mined': monthly_btc_mined
            })
        
        # Sensitivity analysis
        sensitivity_analysis = {
            'btc_price': {
                '20k': irr_pct.get('bear', -100),
                '35k': irr_pct.get('base', 0),
                '50k': irr_pct.get('bull', 0)
            },
            'power_rate': {
                '0.03': irr_pct['base'] + 15,  # 15% IRR boost with cheap power
                '0.05': irr_pct['base'],
                '0.08': max(irr_pct['base'] - 20, -100)  # 20% IRR reduction
            },
            'difficulty_growth': {
                '0%': irr_pct['base'] + 10,
                '3%': irr_pct['base'],
                '6%': max(irr_pct['base'] - 15, -100)
            }
        }
        
        return FinancialBreakdown(
            capex_breakdown=capex_breakdown,
            opex_breakdown=opex_breakdown,
            total_capex_usd=total_capex,
            monthly_opex_usd=monthly_opex,
            payback_months_base=payback_months.get('base', 999),
            payback_months_bear=payback_months.get('bear', 999),
            payback_months_bull=payback_months.get('bull', 999),
            irr_pct_base=irr_pct.get('base', 0),
            irr_pct_bear=irr_pct.get('bear', -100),
            irr_pct_bull=irr_pct.get('bull', 0),
            break_even_btc_price=break_even_price,
            cashflow_curve_months=cashflow_curve,
            sensitivity_analysis=sensitivity_analysis
        )
    
    def _generate_execution_timeline(self, hardware_bill: HardwareBill, power_plan: PowerPlan, region_config: Dict) -> ExecutionTimeline:
        """Generate comprehensive execution timeline with critical path."""
        # Base timeline components
        timeline_components = {
            'site_selection_due_diligence': 4,  # weeks
            'power_contract_negotiation': 8,
            'permitting_zoning': 12,
            'site_preparation': 8,
            'power_interconnection': power_plan.lead_time_energize_weeks,
            'equipment_procurement': hardware_bill.lead_time_weeks,
            'shipping_customs': 3,
            'installation_commissioning': 6,
            'testing_optimization': 2
        }
        
        # Adjust for region-specific factors
        if region_config['region'] in ['PY', 'KZ']:  # International complexity
            timeline_components['permitting_zoning'] += 4
            timeline_components['shipping_customs'] += 2
        
        # Critical path analysis (sequential activities)
        critical_path = [
            'site_selection_due_diligence',
            'power_contract_negotiation', 
            'permitting_zoning',
            'equipment_procurement',  # Can overlap with permitting
            'site_preparation',
            'power_interconnection',  # Can overlap with site prep
            'shipping_customs',
            'installation_commissioning',
            'testing_optimization'
        ]
        
        # Calculate total timeline with critical path optimization
        critical_path_weeks = max(
            timeline_components['site_selection_due_diligence'] + 
            timeline_components['power_contract_negotiation'] + 
            timeline_components['permitting_zoning'] + 
            timeline_components['site_preparation'] + 
            timeline_components['installation_commissioning'] + 
            timeline_components['testing_optimization'],
            
            timeline_components['equipment_procurement'] + 
            timeline_components['shipping_customs'] + 
            timeline_components['installation_commissioning'],
            
            timeline_components['power_interconnection'] + 
            timeline_components['installation_commissioning']
        )
        
        # Add risk buffer
        risk_buffer = int(critical_path_weeks * 0.15)  # 15% buffer
        total_weeks = critical_path_weeks + risk_buffer
        
        # Generate milestone timeline
        start_date = datetime.now()
        milestones = []
        current_week = 0
        
        for activity, weeks in timeline_components.items():
            milestone_date = start_date + timedelta(weeks=current_week + weeks)
            milestones.append({
                'activity': activity,
                'start_week': current_week,
                'duration_weeks': weeks,
                'completion_date': milestone_date.isoformat(),
                'critical_path': activity in critical_path
            })
            if activity in critical_path:
                current_week += weeks
        
        # Dependencies mapping
        dependencies = [
            {'prerequisite': 'site_selection_due_diligence', 'dependent': 'power_contract_negotiation'},
            {'prerequisite': 'power_contract_negotiation', 'dependent': 'permitting_zoning'},
            {'prerequisite': 'permitting_zoning', 'dependent': 'site_preparation'},
            {'prerequisite': 'site_preparation', 'dependent': 'installation_commissioning'},
            {'prerequisite': 'equipment_procurement', 'dependent': 'shipping_customs'},
            {'prerequisite': 'shipping_customs', 'dependent': 'installation_commissioning'},
            {'prerequisite': 'power_interconnection', 'dependent': 'testing_optimization'}
        ]
        
        # Calculate production dates
        earliest_production = start_date + timedelta(weeks=total_weeks - 2)
        full_capacity = start_date + timedelta(weeks=total_weeks)
        
        return ExecutionTimeline(
            total_timeline_weeks=total_weeks,
            critical_path=critical_path,
            milestones=milestones,
            dependencies=dependencies,
            risk_buffer_weeks=risk_buffer,
            earliest_production=earliest_production.isoformat(),
            full_capacity=full_capacity.isoformat()
        )
    
    def _generate_shipping_customs_plan(self, region_config: Dict, hardware_bill: HardwareBill) -> Dict[str, Any]:
        """Generate shipping and customs clearance plan."""
        # Shipping routes and methods
        shipping_routes = {
            'US-TX': {'origin': 'Shenzhen', 'port': 'Houston', 'method': 'sea_freight'},
            'CA-QC': {'origin': 'Shenzhen', 'port': 'Montreal', 'method': 'sea_freight'},
            'PY': {'origin': 'Shenzhen', 'port': 'Santos_to_Asuncion', 'method': 'sea_air'},
            'NO': {'origin': 'Shenzhen', 'port': 'Oslo', 'method': 'sea_freight'}
        }
        
        route = shipping_routes.get(region_config['region'], shipping_routes['US-TX'])
        
        # Duty and tax rates by region
        duty_rates = {
            'US-TX': {'duty_pct': 7.5, 'vat_pct': 0},
            'CA-QC': {'duty_pct': 6.1, 'vat_pct': 13},
            'PY': {'duty_pct': 0, 'vat_pct': 10},
            'NO': {'duty_pct': 3.7, 'vat_pct': 25}
        }
        
        duties = duty_rates.get(region_config['region'], duty_rates['US-TX'])
        
        # Calculate costs
        equipment_value = hardware_bill.total_cost_usd
        duty_cost = int(equipment_value * duties['duty_pct'] / 100)
        vat_cost = int(equipment_value * duties['vat_pct'] / 100)
        shipping_cost = hardware_bill.additional_equipment['shipping_cost_usd']
        
        # Documentation requirements
        required_docs = [
            'Commercial Invoice',
            'Packing List', 
            'Bill of Lading',
            'Certificate of Origin',
            'Import License (if required)',
            'FCC/IC Certification',
            'Insurance Certificate'
        ]
        
        return {
            'shipping_route': route,
            'estimated_transit_days': 21 if route['method'] == 'sea_freight' else 14,
            'duty_rates': duties,
            'estimated_costs': {
                'duty_usd': duty_cost,
                'vat_usd': vat_cost,
                'shipping_usd': shipping_cost,
                'customs_brokerage_usd': 2500,
                'total_landed_cost_usd': equipment_value + duty_cost + vat_cost + shipping_cost + 2500
            },
            'required_documentation': required_docs,
            'customs_broker': f"Regional Customs Broker - {region_config['region']}",
            'incoterms': 'DDP',  # Delivered Duty Paid
            'insurance_coverage': equipment_value * 1.1,  # 110% coverage
            'special_handling': ['Fragile Electronics', 'Temperature Controlled'] if hardware_bill.cooling_method == 'immersion' else ['Fragile Electronics']
        }
    
    def _generate_draft_contracts_rfqs(self, power_plan: PowerPlan, hardware_bill: HardwareBill, region_config: Dict) -> List[Dict[str, str]]:
        """Generate draft contracts and RFQ templates."""
        contracts_rfqs = []
        
        # Power Purchase Agreement template
        contracts_rfqs.append({
            'type': 'Power Purchase Agreement',
            'counterparty': power_plan.utility_company,
            'key_terms': f"{power_plan.contracted_rate_kwh:.3f}$/kWh, {power_plan.minimum_mw:.1f}-{power_plan.maximum_mw:.1f}MW, {power_plan.contract_tenor_years}yr term",
            'template': f"PPA template for {power_plan.power_source} in {region_config['region']}",
            'negotiation_points': f"Rate escalation, curtailment terms, {power_plan.uptime_guarantee_pct}% uptime guarantee"
        })
        
        # Equipment Purchase Agreement
        contracts_rfqs.append({
            'type': 'Equipment Purchase Agreement',
            'counterparty': f"Mining Equipment Supplier - {hardware_bill.vendor_options[0]}",
            'key_terms': f"{hardware_bill.asic_quantity} x {hardware_bill.asic_model} @ ${hardware_bill.unit_cost_usd:,}/unit",
            'template': 'Standard OEM purchase agreement with warranties',
            'negotiation_points': f"Payment terms, {hardware_bill.lead_time_weeks}wk delivery, warranty coverage, spare parts"
        })
        
        # Site Development Contract
        contracts_rfqs.append({
            'type': 'Site Development Contract', 
            'counterparty': 'Regional Construction Contractor',
            'key_terms': f"Site prep, electrical, cooling infrastructure for {hardware_bill.total_power_kw:.0f}kW facility",
            'template': 'EPC contract template with performance guarantees',
            'negotiation_points': 'Timeline penalties, change order procedures, commissioning support'
        })
        
        # Interconnection Agreement
        contracts_rfqs.append({
            'type': 'Interconnection Agreement',
            'counterparty': power_plan.utility_company,
            'key_terms': f"{power_plan.maximum_mw:.1f}MW interconnection at {region_config['zone_designation']}",
            'template': 'Standard utility interconnection agreement',
            'negotiation_points': f"${power_plan.interconnection_cost_usd:,} cost, timeline, upgrade requirements"
        })
        
        # Operations & Maintenance Agreement
        contracts_rfqs.append({
            'type': 'Operations & Maintenance Agreement',
            'counterparty': 'Mining Operations Specialist',
            'key_terms': f"24/7 monitoring, maintenance, optimization for {hardware_bill.asic_quantity} miners",
            'template': 'Comprehensive O&M service agreement',
            'negotiation_points': 'SLA targets, remote monitoring, on-site response times, profit sharing'
        })
        
        return contracts_rfqs
    
    def _assess_setup_friction(self, zone: Dict, region_config: Dict, timeline: ExecutionTimeline) -> float:
        """Assess overall setup friction score (0-1, lower is better)."""
        base_friction = 0.3  # Base friction
        
        # Timeline friction
        if timeline.total_timeline_weeks > 32:  # Over 8 months
            base_friction += 0.2
        elif timeline.total_timeline_weeks < 16:  # Under 4 months
            base_friction -= 0.1
            
        # Regional friction
        regional_friction = {
            'US-TX': 0.1,  # Low friction
            'CA-QC': 0.2,  # Moderate
            'PY': 0.4,     # Higher friction
            'NO': 0.15     # Low-moderate
        }
        base_friction += regional_friction.get(region_config['region'], 0.3)
        
        # Regulatory friction from zone analysis
        framework_scores = zone.get('framework_analysis', {}).get('scores', {})
        policy_score = framework_scores.get('M7_compliance_policy', 0.5)
        infrastructure_score = framework_scores.get('M3_infrastructure_feasibility', 0.5)
        
        # Higher policy/infrastructure scores = lower friction
        base_friction -= (policy_score - 0.5) * 0.2
        base_friction -= (infrastructure_score - 0.5) * 0.2
        
        return min(max(base_friction, 0.0), 1.0)
    
    def _identify_disqualifiers(self, zone: Dict, framework_analysis: Dict) -> List[str]:
        """Identify potential deal disqualifiers."""
        disqualifiers = []
        scores = framework_analysis.get('scores', {})
        
        # Critical score thresholds
        if scores.get('M7_compliance_policy', 1.0) < 0.3:
            disqualifiers.append("Regulatory hostility - crypto mining may be banned or severely restricted")
            
        if scores.get('M2_power_hunt_normalizer', 1.0) < 0.2:
            disqualifiers.append("Power unavailability - no viable power sources at acceptable rates")
            
        if scores.get('M6_financial_synthesizer', 1.0) < 0.3:
            disqualifiers.append("Financial unviability - payback period exceeds acceptable thresholds")
            
        if scores.get('M5_logistics_customs', 1.0) < 0.2:
            disqualifiers.append("Logistics impossibility - equipment cannot be imported or delivered reliably")
            
        # Community warning signals
        if scores.get('M8_community_signal_overlay', 1.0) < 0.2:
            disqualifiers.append("Negative community signals - widespread operator complaints and failures")
        
        return disqualifiers
    
    def _generate_mitigation_options(self, zone: Dict, framework_analysis: Dict, disqualifiers: List[str]) -> List[str]:
        """Generate mitigation options for identified risks."""
        mitigations = []
        scores = framework_analysis.get('scores', {})
        
        # Regulatory mitigations
        if scores.get('M7_compliance_policy', 1.0) < 0.5:
            mitigations.append("Engage local legal counsel specializing in crypto regulations")
            mitigations.append("Structure as data center or high-performance computing facility")
            mitigations.append("Establish relationships with regulatory authorities early")
            
        # Power mitigations
        if scores.get('M2_power_hunt_normalizer', 1.0) < 0.5:
            mitigations.append("Negotiate flexible curtailment agreements with power providers")
            mitigations.append("Consider behind-the-meter renewable energy development")
            mitigations.append("Explore stranded gas or renewable energy opportunities")
            
        # Infrastructure mitigations
        if scores.get('M3_infrastructure_feasibility', 1.0) < 0.5:
            mitigations.append("Budget additional time and cost for permitting and approvals")
            mitigations.append("Consider modular/containerized deployment to reduce site prep")
            mitigations.append("Partner with local developers familiar with regulatory processes")
            
        # Financial mitigations
        if scores.get('M6_financial_synthesizer', 1.0) < 0.5:
            mitigations.append("Secure fixed-rate power contracts to reduce energy price risk")
            mitigations.append("Consider hosting arrangements to reduce capital requirements")
            mitigations.append("Implement dynamic optimization to maximize operational efficiency")
            
        return mitigations
    
    def _extract_critical_dependencies(self, timeline: ExecutionTimeline, power_plan: PowerPlan, hardware_bill: HardwareBill) -> List[str]:
        """Extract critical dependencies that could delay project."""
        dependencies = []
        
        # Timeline-based dependencies
        if timeline.total_timeline_weeks > 24:
            dependencies.append("Extended permitting timeline - regulatory approval delays possible")
            
        # Power dependencies
        if power_plan.lead_time_energize_weeks > 20:
            dependencies.append(f"Power interconnection - {power_plan.lead_time_energize_weeks}wk utility timeline")
            
        if power_plan.curtailment_risk == 'high':
            dependencies.append("Curtailment risk - power availability not guaranteed")
            
        # Hardware dependencies
        if hardware_bill.lead_time_weeks > 12:
            dependencies.append(f"Equipment procurement - {hardware_bill.lead_time_weeks}wk supplier lead time")
            
        dependencies.append("Regulatory approval - mining operations permit required")
        dependencies.append("Site access - land acquisition/lease finalization")
        dependencies.append("Skilled technicians - local workforce availability for installation")
        
        return dependencies
    
    def _generate_vendor_shortlists(self, hardware_bill: HardwareBill, region_config: Dict) -> List[Dict[str, Any]]:
        """Generate vendor shortlists for key categories."""
        vendor_shortlists = []
        
        # Hardware vendors
        vendor_shortlists.append({
            'category': 'Mining Hardware',
            'primary': hardware_bill.vendor_options[0],
            'alternatives': hardware_bill.vendor_options[1:],
            'evaluation_criteria': ['Price', 'Lead time', 'Warranty terms', 'Local support'],
            'preferred_terms': 'NET 30, 2yr warranty, local service'
        })
        
        # Power/Electrical contractors
        vendor_shortlists.append({
            'category': 'Electrical Contractors',
            'primary': f"Regional Electrical - {region_config['region']}",
            'alternatives': ['National EPC Firm', 'Local Industrial Electrician'],
            'evaluation_criteria': ['MW experience', 'Timeline', 'Bonding capacity', 'Local permits'],
            'preferred_terms': 'Fixed price, performance guarantees, local expertise'
        })
        
        # Site development
        vendor_shortlists.append({
            'category': 'Site Development',
            'primary': f"Construction Partner - {region_config['region']}",
            'alternatives': ['Industrial Site Developer', 'Data Center Specialist'],
            'evaluation_criteria': ['Industrial experience', 'Cost', 'Schedule reliability'],
            'preferred_terms': 'EPC contract with penalties, design-build approach'
        })
        
        return vendor_shortlists
    
    def _generate_curtailment_risk_details(self, power_plan: PowerPlan, zone: Dict) -> str:
        """Generate detailed curtailment risk assessment."""
        risk_level = power_plan.curtailment_risk
        
        risk_details = {
            'low': f"Minimal curtailment risk with {power_plan.power_source} power source. Grid interconnection provides stable baseload power with <5% annual curtailment expected. Utility {power_plan.utility_company} has strong grid reliability record.",
            
            'medium': f"Moderate curtailment risk with {power_plan.power_source} arrangement. Renewable-heavy grid may require 10-25% curtailment during peak renewable generation periods. Recommend demand response programs and flexible operations.",
            
            'high': f"Significant curtailment risk with {power_plan.power_source} power source. Expect 25-40% curtailment during favorable conditions (low gas prices, high renewables). Critical to negotiate curtailment compensation and maintain operational flexibility."
        }
        
        base_details = risk_details.get(risk_level, risk_details['medium'])
        
        # Add uptime guarantee context
        base_details += f" Power uptime guaranteed at {power_plan.uptime_guarantee_pct}% with financial penalties for underperformance."
        
        return base_details
    
    def _generate_failure_scenarios(self, zone: Dict, framework_analysis: Dict, hardware_bill: HardwareBill, power_plan: PowerPlan, financial_breakdown: FinancialBreakdown) -> List[Dict[str, str]]:
        """Generate potential failure scenarios and impacts."""
        scenarios = []
        scores = framework_analysis.get('scores', {})
        
        # Regulatory failure
        if scores.get('M7_compliance_policy', 1.0) < 0.6:
            scenarios.append({
                'scenario': 'Regulatory Crackdown',
                'description': 'Local government bans or severely restricts crypto mining operations',
                'probability': 'Medium' if scores.get('M7_compliance_policy', 1.0) < 0.4 else 'Low',
                'impact': 'Complete shutdown required, asset stranding, potential legal liability',
                'mitigation': 'Legal structure as data center, regulatory engagement, exit planning'
            })
        
        # Power failure
        scenarios.append({
            'scenario': 'Power Contract Termination',
            'description': 'Utility terminates power agreement due to grid constraints or policy changes',
            'probability': 'Medium' if power_plan.curtailment_risk == 'high' else 'Low',
            'impact': f"{int(hardware_bill.total_power_kw * 24 * 30 * 0.1):,}$/month revenue loss, forced shutdown",
            'mitigation': 'Multiple power sources, portable infrastructure, demand response participation'
        })
        
        # Market failure
        scenarios.append({
            'scenario': 'Bitcoin Price Collapse',
            'description': 'Sustained BTC price below break-even, making operations unprofitable',
            'probability': 'Medium',
            'impact': f"Operations unprofitable below ${financial_breakdown.break_even_btc_price:,.0f}/BTC",
            'mitigation': 'Flexible cost structure, alternative revenue streams, hedging strategies'
        })
        
        # Hardware failure
        scenarios.append({
            'scenario': 'Equipment Obsolescence',
            'description': 'Rapid advancement in mining hardware makes current equipment uncompetitive',
            'probability': 'High over 3+ years',
            'impact': 'Declining profitability, forced hardware replacement, stranded investment',
            'mitigation': 'Aggressive depreciation, upgrade planning, residual value contracts'
        })
        
        return scenarios
    
    def _generate_expansion_roadmap(self, hardware_bill: HardwareBill, power_plan: PowerPlan, region_config: Dict) -> List[Dict[str, Any]]:
        """Generate expansion roadmap for scaling operations."""
        roadmap = []
        
        # Phase 1: Initial deployment (completed in synthesis)
        roadmap.append({
            'phase': 'Phase 1 - Initial Deployment',
            'timeline': '0-6 months',
            'capacity_mw': power_plan.maximum_mw,
            'capex_usd': hardware_bill.total_cost_usd + sum(hardware_bill.additional_equipment.values()),
            'key_activities': ['Site development', 'Initial equipment deployment', 'Grid interconnection'],
            'success_metrics': [f'{hardware_bill.total_hashrate_th:.0f} TH/s operational', f'{power_plan.uptime_guarantee_pct}% uptime achieved']
        })
        
        # Phase 2: Optimization and efficiency
        roadmap.append({
            'phase': 'Phase 2 - Optimization',
            'timeline': '6-12 months',
            'capacity_mw': power_plan.maximum_mw * 1.1,  # 10% optimization
            'capex_usd': int(hardware_bill.total_cost_usd * 0.1),  # 10% optimization capex
            'key_activities': ['Operational optimization', 'Efficiency improvements', 'Performance tuning'],
            'success_metrics': ['10% efficiency gain', 'Reduce OpEx by 5%', 'Achieve target uptime']
        })
        
        # Phase 3: Scale expansion
        if power_plan.maximum_mw < 5.0:  # Room for expansion
            roadmap.append({
                'phase': 'Phase 3 - Scale Expansion',
                'timeline': '12-24 months', 
                'capacity_mw': min(power_plan.maximum_mw * 2, 10.0),  # Double capacity or cap at 10MW
                'capex_usd': hardware_bill.total_cost_usd,  # Similar to initial investment
                'key_activities': ['Additional interconnection', 'Hardware refresh', 'Site expansion'],
                'success_metrics': ['Double operational capacity', 'Maintain unit economics', 'Diversify hardware portfolio']
            })
        
        # Phase 4: Geographic diversification
        roadmap.append({
            'phase': 'Phase 4 - Geographic Diversification',
            'timeline': '18-36 months',
            'capacity_mw': 5.0,  # New site capacity
            'capex_usd': int(hardware_bill.total_cost_usd * 1.2),  # New site premium
            'key_activities': ['Second site development', 'Geographic risk diversification', 'Portfolio optimization'],
            'success_metrics': ['Multi-site operations', 'Reduced concentration risk', 'Portfolio-level optimization']
        })
        
        return roadmap

def generate_mining_setup_issues(mining_setups: List[MiningSetup], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate GitHub issues for mining setups with complete specifications.
    
    Args:
        mining_setups: List of synthesized mining setups
        config: Configuration for issue generation
        
    Returns:
        List of GitHub issue specifications
    """
    issues = []
    
    for i, setup in enumerate(mining_setups, 1):
        # Create GitHub issue content
        issue_title = f"[Mining Setup {i:02d}] {setup.region_power_hardware_config}"
        
        # Generate comprehensive issue body
        issue_body = f"""# Mining Viability Setup Specification

## 🎯 Setup Overview
- **Setup ID**: `{setup.setup_id}`
- **Viability Score**: {setup.viability_score:.3f}
- **Configuration**: {setup.region_power_hardware_config}

## ⚡ Power Arrangement
- **Source**: {setup.power_plan.power_source.upper()}
- **Rate**: ${setup.power_plan.contracted_rate_kwh:.4f}/kWh
- **Capacity**: {setup.power_plan.minimum_mw:.1f} - {setup.power_plan.maximum_mw:.1f} MW
- **Utility**: {setup.power_plan.utility_company}
- **Curtailment Risk**: {setup.power_plan.curtailment_risk.title()}

## 🔧 Hardware Configuration
- **ASIC Model**: {setup.bill_of_hardware.asic_model}
- **Quantity**: {setup.bill_of_hardware.asic_quantity:,} units
- **Total Hashrate**: {setup.bill_of_hardware.total_hashrate_th:,.0f} TH/s
- **Total Power**: {setup.bill_of_hardware.total_power_kw:,.0f} kW
- **Hardware Cost**: ${setup.bill_of_hardware.total_cost_usd:,}

## 💰 Financial Projections
- **Total CapEx**: ${setup.financial_projections.total_capex_usd:,}
- **Monthly OpEx**: ${setup.financial_projections.monthly_opex_usd:,}
- **Payback (Base/Bear/Bull)**: {setup.financial_projections.payback_months_base}/{setup.financial_projections.payback_months_bear}/{setup.financial_projections.payback_months_bull} months
- **IRR (Base)**: {setup.financial_projections.irr_pct_base:.1f}%
- **Break-even BTC**: ${setup.financial_projections.break_even_btc_price:,.0f}

## 📅 Execution Timeline
- **Total Timeline**: {setup.execution_timeline.total_timeline_weeks} weeks
- **Production Start**: {setup.execution_timeline.earliest_production[:10]}
- **Full Capacity**: {setup.execution_timeline.full_capacity[:10]}
- **Setup Friction**: {setup.setup_friction_score:.2f}

## 🚨 Critical Dependencies
{chr(10).join([f"- {dep}" for dep in setup.critical_dependencies])}

## ⚠️ Risk Assessment
### Disqualifiers
{chr(10).join([f"- {qual}" for qual in setup.disqualifiers]) if setup.disqualifiers else "- None identified"}

### Mitigation Options
{chr(10).join([f"- {mit}" for mit in setup.mitigation_options])}

## 📋 Next Steps
1. **Power Contract**: Negotiate PPA with {setup.power_plan.utility_company}
2. **Equipment Orders**: Place orders with {setup.bill_of_hardware.vendor_options[0]}
3. **Site Development**: Begin permitting and site preparation
4. **Regulatory**: Engage legal counsel for compliance strategy
5. **Operations**: Establish O&M partnership

## 📊 Detailed Analysis
- **Curtailment Risk**: {setup.curtailment_risk_details}
- **Vendor Shortlists**: {len(setup.vendor_shortlists)} categories evaluated
- **Expansion Roadmap**: {len(setup.expansion_roadmap)} phases planned

---
*Generated by Mining Viability Engine on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        # Create issue specification
        issue_labels = ['opportunity', 'crypto-mining', 'viability-analysis', 'mining-setup', 'power-infrastructure']
        
        # Extract labels from config if available
        try:
            if isinstance(config, dict):
                if 'output' in config and isinstance(config['output'], dict) and 'issue_labels' in config['output']:
                    issue_labels = config['output']['issue_labels']
            elif hasattr(config, 'output') and hasattr(config.output, 'issue_labels'):
                issue_labels = config.output.issue_labels
        except (AttributeError, TypeError, KeyError):
            pass  # Use default labels
        
        issue = {
            'title': issue_title,
            'body': issue_body,
            'labels': issue_labels,
            'assignees': [],
            'milestone': None,
            'frontmatter': {
                'setup_id': setup.setup_id,
                'viability_score': setup.viability_score,
                'region': setup.region_power_hardware_config.split(' | ')[0],
                'power_source': setup.power_plan.power_source,
                'total_capex_usd': setup.financial_projections.total_capex_usd,
                'payback_months_base': setup.financial_projections.payback_months_base,
                'timeline_weeks': setup.execution_timeline.total_timeline_weeks,
                'hashrate_th': setup.bill_of_hardware.total_hashrate_th,
                'power_kw': setup.bill_of_hardware.total_power_kw
            }
        }
        
        issues.append(issue)
    
    logger.info(f"Generated {len(issues)} mining setup GitHub issues")
    return issues