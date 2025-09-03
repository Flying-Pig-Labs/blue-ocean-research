#!/usr/bin/env python3
"""
Device Specification Synthesizer - Medical Device Specification Generation

Transforms opportunity zones and SPEC-TRACE framework results into comprehensive
medical device specifications with complete regulatory, engineering, and validation details.
"""

import json
import logging
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class DeviceSpecification:
    """Complete medical device specification with all required fields."""
    # Identification
    spec_id: str
    title: str
    device_category: str
    
    # Clinical context
    intended_use: str
    clinical_need: str
    target_setting: str
    user_profiles: List[str]
    
    # Technical requirements
    performance_requirements: List[Dict[str, str]]
    environmental_constraints: List[str]
    form_factor_constraints: str
    
    # Regulatory pathway
    regulatory_pathway: str
    applicable_standards: List[str]
    risk_register: List[Dict[str, str]]
    
    # Materials and biocompatibility
    materials_and_biocompatibility: str
    sterilization_reprocessing: Optional[str] = None
    
    # Technology stack
    power_connectivity: Optional[str] = None
    manufacturing_processes: List[str] = None
    top_level_BOM: List[str] = None
    
    # Business considerations  
    unit_cost_target: float = 0.0
    supply_chain_notes: str = ""
    
    # Human factors
    human_factors: str = ""
    
    # Validation and verification
    verification_plan: str = ""
    validation_plan: str = ""
    
    # Additional considerations
    ip_landscape: Optional[str] = None
    postmarket_surveillance: Optional[str] = None
    
    # Framework analysis
    spec_trace_scores: Dict[str, float] = None
    citations: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert specification to dictionary for JSON serialization."""
        return {
            'spec_id': self.spec_id,
            'title': self.title,
            'device_category': self.device_category,
            'intended_use': self.intended_use,
            'clinical_need': self.clinical_need,
            'target_setting': self.target_setting,
            'user_profiles': self.user_profiles,
            'performance_requirements': self.performance_requirements,
            'regulatory_pathway': self.regulatory_pathway,
            'applicable_standards': self.applicable_standards,
            'materials_and_biocompatibility': self.materials_and_biocompatibility,
            'sterilization_reprocessing': self.sterilization_reprocessing,
            'power_connectivity': self.power_connectivity,
            'human_factors': self.human_factors,
            'environmental_constraints': self.environmental_constraints,
            'form_factor_constraints': self.form_factor_constraints,
            'manufacturing_processes': self.manufacturing_processes,
            'top_level_BOM': self.top_level_BOM,
            'unit_cost_target': self.unit_cost_target,
            'supply_chain_notes': self.supply_chain_notes,
            'verification_plan': self.verification_plan,
            'validation_plan': self.validation_plan,
            'risk_register': self.risk_register,
            'ip_landscape': self.ip_landscape,
            'postmarket_surveillance': self.postmarket_surveillance,
            'spec_trace_scores': self.spec_trace_scores,
            'citations': self.citations
        }

class DeviceSpecSynthesizer:
    """Synthesizes medical device specifications from opportunity zones and framework results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def synthesize_device_specs(self, 
                               opportunity_zones: List[Dict[str, Any]],
                               framework_results: List[Dict[str, Any]], 
                               total_count: int = 10,
                               context: Dict[str, Any] = None) -> List[DeviceSpecification]:
        """
        Generate device specifications from opportunity zones and SPEC-TRACE analysis.
        
        Args:
            opportunity_zones: List of opportunity zone data
            framework_results: List of SPEC-TRACE framework analysis results
            total_count: Total number of specifications to generate (default: 10)
            context: Additional context for specification generation
            
        Returns:
            List of DeviceSpecification objects
        """
        self.logger.info(f"Synthesizing {total_count} device specifications from {len(opportunity_zones)} zones")
        
        # Combine zones with framework results
        zone_analyses = self._combine_zones_with_frameworks(opportunity_zones, framework_results)
        
        # Weight zones by SPEC-TRACE composite scores for distribution
        weighted_zones = self._calculate_zone_weights(zone_analyses)
        
        # Generate specifications across zones
        device_specs = []
        
        for zone_data in weighted_zones:
            zone = zone_data['zone']
            framework_result = zone_data['framework']
            target_count = zone_data['target_specs']
            
            if target_count == 0:
                continue
                
            self.logger.info(f"Generating {target_count} specs for zone: {zone.get('name', 'Unknown')}")
            
            # Generate specifications for this zone
            zone_specs = self._generate_specs_for_zone(
                zone, framework_result, target_count, context
            )
            
            device_specs.extend(zone_specs)
        
        # Ensure exactly total_count specifications
        device_specs = self._ensure_exact_count(device_specs, total_count)
        
        # Sort by composite SPEC-TRACE score (descending)
        device_specs.sort(key=lambda spec: spec.spec_trace_scores.get('composite', 0), reverse=True)
        
        self.logger.info(f"Successfully generated {len(device_specs)} device specifications")
        
        return device_specs
    
    def _combine_zones_with_frameworks(self, zones: List[Dict], frameworks: List[Dict]) -> List[Dict]:
        """Combine opportunity zones with their corresponding framework results."""
        zone_analyses = []
        
        # Create mapping of zone_id to framework result
        framework_map = {}
        for fw in frameworks:
            zone_id = fw.get('zone_id')
            if zone_id:
                framework_map[zone_id] = fw
        
        # Combine each zone with its framework result
        for zone in zones:
            zone_id = zone.get('zone_id') or zone.get('id')
            framework_result = framework_map.get(zone_id)
            
            if framework_result:
                zone_analyses.append({
                    'zone': zone,
                    'framework': framework_result
                })
            else:
                self.logger.warning(f"No framework result found for zone {zone_id}")
        
        return zone_analyses
    
    def _calculate_zone_weights(self, zone_analyses: List[Dict]) -> List[Dict]:
        """Calculate how many specs each zone should contribute based on SPEC-TRACE scores."""
        if not zone_analyses:
            return []
        
        # Extract composite scores
        for analysis in zone_analyses:
            framework = analysis['framework']
            composite_score = framework.get('overall_score', 0) or framework.get('composite_score', 0)
            analysis['composite_score'] = composite_score
        
        # Calculate total weight
        total_weight = sum(analysis['composite_score'] for analysis in zone_analyses)
        
        if total_weight == 0:
            # Equal distribution if no scores available
            specs_per_zone = 10 // len(zone_analyses)
            remainder = 10 % len(zone_analyses)
            
            for i, analysis in enumerate(zone_analyses):
                analysis['target_specs'] = specs_per_zone + (1 if i < remainder else 0)
        else:
            # Weighted distribution based on composite scores
            for analysis in zone_analyses:
                weight_percentage = analysis['composite_score'] / total_weight
                analysis['target_specs'] = max(1, round(weight_percentage * 10))
        
        return zone_analyses
    
    def _generate_specs_for_zone(self, 
                                zone: Dict[str, Any], 
                                framework_result: Dict[str, Any],
                                target_count: int,
                                context: Dict[str, Any]) -> List[DeviceSpecification]:
        """Generate device specifications for a specific opportunity zone."""
        zone_name = zone.get('name', 'Unknown Zone')
        device_category = self._detect_device_category(zone, framework_result)
        
        specs = []
        
        for i in range(target_count):
            try:
                spec = self._create_device_spec(
                    zone, framework_result, device_category, i, context
                )
                specs.append(spec)
                
            except Exception as e:
                self.logger.error(f"Failed to create spec {i+1} for zone {zone_name}: {e}")
                continue
        
        return specs
    
    def _create_device_spec(self, 
                           zone: Dict[str, Any],
                           framework_result: Dict[str, Any], 
                           device_category: str,
                           spec_index: int,
                           context: Dict[str, Any]) -> DeviceSpecification:
        """Create a single device specification."""
        
        zone_name = zone.get('name', 'Unknown Zone')
        zone_id = zone.get('zone_id') or zone.get('id', 'unknown')
        
        # Generate unique spec ID
        spec_id = self._generate_spec_id(zone_id, spec_index)
        
        # Extract key information from zone and framework
        pain_dims = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbd_descriptions', [])
        framework_scores = framework_result.get('scores', {})
        
        # Generate spec title
        title = self._generate_device_title(device_category, solutions, jtbds, spec_index)
        
        # Generate clinical context
        intended_use = self._generate_intended_use(device_category, solutions, jtbds)
        clinical_need = self._generate_clinical_need(pain_dims, solutions, jtbds)
        target_setting = self._determine_target_setting(device_category, jtbds)
        user_profiles = self._identify_user_profiles(device_category, jtbds, solutions)
        
        # Generate technical requirements
        performance_reqs = self._generate_performance_requirements(device_category, solutions, framework_scores)
        environmental_constraints = self._generate_environmental_constraints(device_category, framework_scores)
        form_factor = self._generate_form_factor_constraints(device_category, solutions)
        
        # Generate regulatory pathway
        regulatory_pathway = self._generate_regulatory_pathway(device_category, framework_scores)
        applicable_standards = self._generate_applicable_standards(device_category, framework_scores)
        risk_register = self._generate_risk_register(device_category, framework_scores)
        
        # Generate materials and biocompatibility
        materials = self._generate_materials_biocompatibility(device_category)
        sterilization = self._generate_sterilization_reprocessing(device_category)
        
        # Generate technology details
        power_connectivity = self._generate_power_connectivity(device_category, framework_scores)
        manufacturing = self._generate_manufacturing_processes(device_category)
        bom = self._generate_top_level_bom(device_category, solutions)
        
        # Generate business considerations
        cost_target = self._estimate_unit_cost_target(device_category, framework_scores)
        supply_chain = self._generate_supply_chain_notes(device_category, manufacturing)
        
        # Generate human factors
        human_factors = self._generate_human_factors_plan(device_category, user_profiles, framework_scores)
        
        # Generate validation plans
        verification_plan = self._generate_verification_plan(device_category, performance_reqs)
        validation_plan = self._generate_validation_plan(device_category, framework_scores)
        
        # Optional fields
        ip_landscape = self._generate_ip_landscape(device_category)
        postmarket = self._generate_postmarket_surveillance(device_category)
        
        # Extract citations
        citations = framework_result.get('citations', []) + context.get('reddit_discussions', [])[:2]
        
        # Create specification
        spec = DeviceSpecification(
            spec_id=spec_id,
            title=title,
            device_category=device_category,
            intended_use=intended_use,
            clinical_need=clinical_need,
            target_setting=target_setting,
            user_profiles=user_profiles,
            performance_requirements=performance_reqs,
            regulatory_pathway=regulatory_pathway,
            applicable_standards=applicable_standards,
            materials_and_biocompatibility=materials,
            sterilization_reprocessing=sterilization,
            power_connectivity=power_connectivity,
            human_factors=human_factors,
            environmental_constraints=environmental_constraints,
            form_factor_constraints=form_factor,
            manufacturing_processes=manufacturing,
            top_level_BOM=bom,
            unit_cost_target=cost_target,
            supply_chain_notes=supply_chain,
            verification_plan=verification_plan,
            validation_plan=validation_plan,
            risk_register=risk_register,
            ip_landscape=ip_landscape,
            postmarket_surveillance=postmarket,
            spec_trace_scores=framework_scores,
            citations=citations
        )
        
        return spec
    
    def _generate_spec_id(self, zone_id: str, spec_index: int) -> str:
        """Generate unique specification ID."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d')
        hash_input = f"{zone_id}:{spec_index}:{timestamp}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:6]
        return f"DEV-{timestamp}-{hash_suffix.upper()}"
    
    def _detect_device_category(self, zone: Dict, framework_result: Dict) -> str:
        """Detect device category from zone and framework analysis."""
        solutions = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbd_descriptions', [])
        text_analysis = ' '.join(solutions + jtbds).lower()
        
        # Category detection logic
        if any(word in text_analysis for word in ['monitor', 'sensor', 'measurement', 'vital']):
            return 'monitoring'
        elif any(word in text_analysis for word in ['surgical', 'instrument', 'procedure', 'operation']):
            return 'surgical_accessory'
        elif any(word in text_analysis for word in ['implant', 'permanent', 'internal']):
            return 'implantable'
        elif any(word in text_analysis for word in ['diagnostic', 'test', 'assay', 'screening']):
            return 'diagnostic'
        elif any(word in text_analysis for word in ['wound', 'dressing', 'healing', 'skin']):
            return 'wound_care'
        else:
            return 'monitoring'  # Default fallback
    
    def _generate_device_title(self, category: str, solutions: List, jtbds: List, index: int) -> str:
        """Generate market-facing device title."""
        category_prefixes = {
            'monitoring': ['Smart', 'Continuous', 'Real-time', 'Wireless'],
            'diagnostic': ['Rapid', 'Point-of-Care', 'Portable', 'Advanced'],
            'surgical_accessory': ['Precision', 'Enhanced', 'Smart', 'Adaptive'],
            'implantable': ['Bio-integrated', 'Smart', 'Adaptive', 'Advanced'],
            'wound_care': ['Advanced', 'Smart', 'Therapeutic', 'Bioactive']
        }
        
        category_suffixes = {
            'monitoring': ['Monitor', 'Sensor System', 'Detector', 'Tracking Device'],
            'diagnostic': ['Analyzer', 'Test System', 'Diagnostic Tool', 'Scanner'],
            'surgical_accessory': ['Instrument', 'Surgical Tool', 'Assistant', 'Guide'],
            'implantable': ['Implant', 'Device', 'System', 'Prosthetic'],
            'wound_care': ['Dressing', 'Treatment System', 'Therapy Device', 'Healing Platform']
        }
        
        prefix = category_prefixes.get(category, ['Smart'])[index % len(category_prefixes.get(category, ['Smart']))]
        suffix = category_suffixes.get(category, ['Device'])[index % len(category_suffixes.get(category, ['Device']))]
        
        # Try to extract domain from solutions/JTBDs
        domain_hints = []
        text = ' '.join(solutions + jtbds).lower()
        if 'cardiac' in text or 'heart' in text:
            domain_hints.append('Cardiac')
        elif 'respiratory' in text or 'lung' in text:
            domain_hints.append('Respiratory')
        elif 'blood' in text or 'glucose' in text:
            domain_hints.append('Blood')
        elif 'pressure' in text:
            domain_hints.append('Pressure')
        
        if domain_hints:
            return f"{prefix} {domain_hints[0]} {suffix}"
        else:
            return f"{prefix} Clinical {suffix}"
    
    def _generate_intended_use(self, category: str, solutions: List, jtbds: List) -> str:
        """Generate intended use statement."""
        use_templates = {
            'monitoring': "Continuous monitoring of {parameter} in {setting} for {indication}",
            'diagnostic': "Point-of-care testing for {condition} in {setting} environments",
            'surgical_accessory': "Surgical assistance for {procedure} to improve {outcome}",
            'implantable': "Long-term implantable device for {therapy} in {patient_population}",
            'wound_care': "Advanced wound management for {wound_type} in {care_setting}"
        }
        
        template = use_templates.get(category, "Clinical device for {application} in {setting}")
        
        # Default parameters
        return template.format(
            parameter='physiological parameters',
            setting='clinical environments',
            indication='patient care',
            condition='clinical conditions',
            procedure='minimally invasive procedures',
            outcome='patient outcomes',
            therapy='therapeutic intervention',
            patient_population='target patient population',
            wound_type='chronic wounds',
            care_setting='clinical care settings',
            application='clinical applications'
        )
    
    def _generate_clinical_need(self, pain_dims: Dict, solutions: List, jtbds: List) -> str:
        """Generate clinical need statement with measurable outcomes."""
        # Extract primary pain points
        top_pains = sorted(pain_dims.items(), key=lambda x: x[1], reverse=True)[:2]
        
        need_components = []
        if top_pains:
            pain_name, pain_score = top_pains[0]
            need_components.append(f"Addresses critical {pain_name.replace('_', ' ')} challenges")
        
        need_components.append("Improves patient outcomes through enhanced clinical workflow")
        need_components.append("Reduces healthcare costs by preventing complications")
        need_components.append("Measurable impact: 20-30% reduction in adverse events")
        
        return '. '.join(need_components) + '.'
    
    def _determine_target_setting(self, category: str, jtbds: List) -> str:
        """Determine target clinical setting."""
        text = ' '.join(jtbds).lower()
        
        if 'icu' in text or 'intensive' in text:
            return 'ICU'
        elif 'emergency' in text or 'ed' in text:
            return 'ED'
        elif 'surgery' in text or 'operating' in text:
            return 'OR'
        elif 'clinic' in text or 'outpatient' in text:
            return 'clinic'
        elif 'home' in text or 'patient' in text:
            return 'home'
        else:
            # Category-based defaults
            defaults = {
                'monitoring': 'ICU',
                'diagnostic': 'clinic',
                'surgical_accessory': 'OR',
                'implantable': 'OR',
                'wound_care': 'clinic'
            }
            return defaults.get(category, 'clinic')
    
    def _identify_user_profiles(self, category: str, jtbds: List, solutions: List) -> List[str]:
        """Identify primary user profiles."""
        text = ' '.join(jtbds + solutions).lower()
        
        users = []
        if 'nurse' in text or 'nursing' in text:
            users.append('RN')
        if 'physician' in text or 'doctor' in text:
            users.append('Physician')
        if 'surgeon' in text or 'surgical' in text:
            users.append('Surgeon')
        if 'tech' in text or 'technician' in text:
            users.append('Medical Technician')
        if 'patient' in text:
            users.append('Patient')
        if 'respiratory' in text:
            users.append('Respiratory Therapist')
        
        # Category defaults if no users detected
        if not users:
            defaults = {
                'monitoring': ['RN', 'Medical Technician'],
                'diagnostic': ['Physician', 'Medical Technician'],
                'surgical_accessory': ['Surgeon', 'OR Nurse'],
                'implantable': ['Surgeon', 'Patient'],
                'wound_care': ['RN', 'Wound Care Specialist']
            }
            users = defaults.get(category, ['Healthcare Professional'])
        
        return users
    
    def _generate_performance_requirements(self, category: str, solutions: List, framework_scores: Dict) -> List[Dict[str, str]]:
        """Generate testable performance requirements."""
        requirements = []
        
        # Category-specific base requirements
        if category == 'monitoring':
            requirements.extend([
                {'metric': 'Accuracy', 'target': '≥95% vs gold standard', 'test_method': 'Bench validation'},
                {'metric': 'Response time', 'target': '≤2 seconds', 'test_method': 'Real-time testing'},
                {'metric': 'Battery life', 'target': '≥24 hours continuous', 'test_method': 'Endurance testing'}
            ])
        elif category == 'diagnostic':
            requirements.extend([
                {'metric': 'Sensitivity', 'target': '≥90%', 'test_method': 'Clinical validation'},
                {'metric': 'Specificity', 'target': '≥85%', 'test_method': 'Clinical validation'},
                {'metric': 'Time to result', 'target': '≤15 minutes', 'test_method': 'Performance testing'}
            ])
        elif category == 'surgical_accessory':
            requirements.extend([
                {'metric': 'Precision', 'target': '±0.1mm accuracy', 'test_method': 'Mechanical testing'},
                {'metric': 'Force feedback', 'target': '1-10N range', 'test_method': 'Force testing'},
                {'metric': 'Sterilization cycles', 'target': '≥50 cycles', 'test_method': 'Sterilization validation'}
            ])
        
        # Add reliability requirements
        requirements.append({
            'metric': 'MTBF', 
            'target': '≥2000 hours', 
            'test_method': 'Reliability testing per IEC 60601-1'
        })
        
        return requirements
    
    def _generate_environmental_constraints(self, category: str, framework_scores: Dict) -> List[str]:
        """Generate environmental operating constraints."""
        base_constraints = [
            '10°C to 40°C operating temperature',
            '15% to 85% relative humidity',
            'IP42 minimum ingress protection'
        ]
        
        if category in ['monitoring', 'diagnostic']:
            base_constraints.extend([
                'EMC per IEC 60601-1-2',
                'Vibration resistance per IEC 60601-1-8'
            ])
        
        if framework_scores.get('DC', 0) > 0.5:  # High data/cyber requirements
            base_constraints.append('Cybersecurity per FDA guidelines')
        
        return base_constraints
    
    def _generate_form_factor_constraints(self, category: str, solutions: List) -> str:
        """Generate form factor and ergonomic constraints."""
        constraints = {
            'monitoring': 'Wearable patch ≤15g; base unit mountable on IV pole',
            'diagnostic': 'Handheld form factor ≤500g; one-handed operation',
            'surgical_accessory': 'Sterilizable handle; tactile feedback; <200g',
            'implantable': 'Biocompatible titanium housing; ≤5mm thickness',
            'wound_care': 'Flexible conformable design; sterile packaging'
        }
        
        return constraints.get(category, 'Ergonomic design optimized for clinical workflow')
    
    def _generate_regulatory_pathway(self, category: str, framework_scores: Dict) -> str:
        """Generate regulatory pathway assessment."""
        rc_score = framework_scores.get('RC', 0.5)
        
        # Invert RC score (higher complexity = lower score in SPEC-TRACE)
        complexity = 1.0 - rc_score
        
        if complexity > 0.7:
            pathway = "US Class III; likely PMA pathway with clinical data requirements"
        elif complexity > 0.5:
            pathway = "US Class II; De Novo or 510(k) with substantial predicate gaps"  
        else:
            pathway = "US Class II; likely 510(k) with well-established predicates"
        
        # Add EU considerations
        pathway += "; EU Class IIa/IIb under MDR with conformity assessment"
        
        return pathway
    
    def _generate_applicable_standards(self, category: str, framework_scores: Dict) -> List[str]:
        """Generate applicable regulatory standards."""
        standards = ['ISO 13485', 'ISO 14971']  # Universal
        
        if category in ['monitoring', 'diagnostic']:
            standards.extend(['IEC 60601-1', 'IEC 60601-1-2'])
        
        if framework_scores.get('HF', 0) > 0.6:
            standards.extend(['IEC 62366-1', 'IEC 62366-2'])
        
        if framework_scores.get('DC', 0) > 0.5:
            standards.append('IEC 62304')
        
        if category in ['implantable', 'wound_care']:
            standards.append('ISO 10993 series')
        
        return standards
    
    def _generate_risk_register(self, category: str, framework_scores: Dict) -> List[Dict[str, str]]:
        """Generate top 5 risk register entries per ISO 14971."""
        risks = []
        
        # Category-specific risks
        if category == 'monitoring':
            risks.extend([
                {
                    'hazard': 'Sensor malfunction',
                    'sequence_of_events': 'Sensor drift → incorrect readings → delayed intervention',
                    'harm': 'Patient deterioration',
                    'mitigations': 'Redundant sensors, alarm limits, calibration protocols'
                },
                {
                    'hazard': 'Adhesive reaction',
                    'sequence_of_events': 'Prolonged skin contact → irritation → skin breakdown',
                    'harm': 'Skin injury',
                    'mitigations': 'Biocompatible materials, wear time limits, proper labeling'
                }
            ])
        elif category == 'surgical_accessory':
            risks.extend([
                {
                    'hazard': 'Instrument fracture',
                    'sequence_of_events': 'Material failure → fragment retention → inflammation',
                    'harm': 'Tissue damage',
                    'mitigations': 'Material testing, design margin, inspection protocols'
                },
                {
                    'hazard': 'Sterilization failure',
                    'sequence_of_events': 'Inadequate sterilization → infection transmission',
                    'harm': 'Healthcare-associated infection',
                    'mitigations': 'Validated sterilization process, sterility testing, packaging'
                }
            ])
        
        # Add universal risks
        risks.append({
            'hazard': 'Use error',
            'sequence_of_events': 'Complex interface → user confusion → incorrect use',
            'harm': 'Treatment delay',
            'mitigations': 'Human factors validation, training, clear labeling'
        })
        
        return risks[:5]  # Limit to top 5
    
    def _generate_materials_biocompatibility(self, category: str) -> str:
        """Generate materials and biocompatibility assessment."""
        materials = {
            'monitoring': 'Skin-contact silicone elastomer; ISO 10993 endpoints: cytotoxicity, sensitization, irritation',
            'diagnostic': 'Blood-contact polycarbonate; ISO 10993 cytotoxicity and hemocompatibility testing',
            'surgical_accessory': 'Stainless steel 316L; tissue contact ≤24 hours; cytotoxicity testing',
            'implantable': 'Titanium alloy housing; permanent implant; full ISO 10993 biological evaluation',
            'wound_care': 'Hydrocolloid with antimicrobial silver; skin contact; cytotoxicity and sensitization'
        }
        
        return materials.get(category, 'Medical-grade materials per ISO 10993 requirements')
    
    def _generate_sterilization_reprocessing(self, category: str) -> Optional[str]:
        """Generate sterilization and reprocessing requirements."""
        if category in ['surgical_accessory']:
            return 'Steam sterilization 134°C, 3 minutes; validated for 100+ cycles; reprocessing per IFU'
        elif category == 'implantable':
            return 'Gamma irradiation 25-40 kGy; single-use sterile packaging'
        elif category in ['monitoring', 'wound_care']:
            return 'Single-use disposable; EtO sterilization if required'
        else:
            return None
    
    def _generate_power_connectivity(self, category: str, framework_scores: Dict) -> Optional[str]:
        """Generate power and connectivity specifications."""
        if framework_scores.get('DC', 0) > 0.4:  # Moderate+ data/cyber requirements
            return 'Rechargeable Li-ion battery; BLE 5.0; encrypted data transmission; OTA updates via secure channel'
        elif category in ['monitoring', 'diagnostic']:
            return 'Battery-powered; optional USB-C charging; basic data logging'
        else:
            return None
    
    def _generate_manufacturing_processes(self, category: str) -> List[str]:
        """Generate primary manufacturing processes."""
        processes = {
            'monitoring': ['Injection molding', 'SMT assembly', 'Adhesive application', 'Sterile packaging'],
            'diagnostic': ['Injection molding', 'Microfluidics fabrication', 'Electronic assembly', 'Final testing'],
            'surgical_accessory': ['CNC machining', 'Electropolishing', 'Laser marking', 'Sterilization'],
            'implantable': ['Precision machining', 'Surface treatment', 'Hermetic sealing', 'Final inspection'],
            'wound_care': ['Film lamination', 'Die cutting', 'Adhesive coating', 'Sterile packaging']
        }
        
        return processes.get(category, ['Manufacturing process TBD'])
    
    def _generate_top_level_bom(self, category: str, solutions: List) -> List[str]:
        """Generate top-level bill of materials."""
        boms = {
            'monitoring': ['Sensor module', 'MCU board', 'Battery pack', 'Adhesive patch', 'Wireless module'],
            'diagnostic': ['Microfluidic cartridge', 'Optical sensor', 'Control electronics', 'Display unit', 'Reagents'],
            'surgical_accessory': ['Handle assembly', 'Instrument tip', 'Actuation mechanism', 'Electrical contacts'],
            'implantable': ['Titanium housing', 'Electronics module', 'Battery', 'Antenna', 'Hermetic feedthrough'],
            'wound_care': ['Base dressing', 'Active layer', 'Adhesive border', 'Release liner', 'Packaging']
        }
        
        return boms.get(category, ['Component list TBD'])
    
    def _estimate_unit_cost_target(self, category: str, framework_scores: Dict) -> float:
        """Estimate target unit cost at scale."""
        base_costs = {
            'monitoring': 45.0,
            'diagnostic': 85.0,
            'surgical_accessory': 125.0,
            'implantable': 2500.0,
            'wound_care': 15.0
        }
        
        base_cost = base_costs.get(category, 50.0)
        
        # Adjust based on complexity (DC score indicates electronic complexity)
        dc_score = framework_scores.get('DC', 0.3)
        if dc_score > 0.7:
            base_cost *= 1.5  # High connectivity/data requirements
        elif dc_score > 0.5:
            base_cost *= 1.2
        
        return base_cost
    
    def _generate_supply_chain_notes(self, category: str, manufacturing: List[str]) -> str:
        """Generate supply chain risk assessment."""
        notes = [
            "Key component lead times: 12-20 weeks for custom semiconductors",
            "Dual-source strategy for critical components",
            "Regulatory change control for supplier qualifications"
        ]
        
        if category == 'implantable':
            notes.append("Titanium supply chain monitoring for material certificates")
        
        if 'SMT' in ' '.join(manufacturing):
            notes.append("Electronic component obsolescence monitoring program")
        
        return '. '.join(notes) + '.'
    
    def _generate_human_factors_plan(self, category: str, users: List[str], framework_scores: Dict) -> str:
        """Generate human factors validation plan per IEC 62366."""
        hf_score = framework_scores.get('HF', 0.5)
        
        plan_components = [
            f"Primary users: {', '.join(users)}",
            "Critical tasks identification and use-related risk analysis",
            "Formative evaluation with clinical workflow integration"
        ]
        
        if hf_score > 0.7:
            plan_components.append("Summative HF validation study with representative users")
            plan_components.append("Use error mitigation through design and labeling")
        
        plan_components.append("IEC 62366-1 compliance with usability engineering file")
        
        return '. '.join(plan_components) + '.'
    
    def _generate_verification_plan(self, category: str, performance_reqs: List[Dict]) -> str:
        """Generate verification plan for performance requirements."""
        plan = [
            "Bench testing of all performance requirements per test methods",
            "Environmental testing per IEC 60601-1-8",
            "EMC testing per IEC 60601-1-2"
        ]
        
        if category in ['monitoring', 'diagnostic']:
            plan.append("Accuracy validation against gold standard references")
        
        if category == 'surgical_accessory':
            plan.append("Mechanical testing including fatigue and durability")
        
        plan.append("Software verification per IEC 62304 if applicable")
        
        return '. '.join(plan) + '.'
    
    def _generate_validation_plan(self, category: str, framework_scores: Dict) -> str:
        """Generate validation plan including clinical validation."""
        plan = ["Human factors summative validation per IEC 62366"]
        
        ep_score = framework_scores.get('EP', 0.6)
        
        if ep_score < 0.5:  # Low EP score means high evidence burden
            plan.append("Clinical validation study with patient outcome endpoints")
            plan.append("Multi-center trial for regulatory submission")
        else:
            plan.append("Clinical performance validation with surrogate endpoints")
        
        plan.append("Post-market clinical follow-up per regulatory requirements")
        
        return '. '.join(plan) + '.'
    
    def _generate_ip_landscape(self, category: str) -> Optional[str]:
        """Generate intellectual property landscape assessment."""
        return f"Freedom-to-operate analysis for {category} devices; patent landscape review for key technologies; defensive IP strategy development"
    
    def _generate_postmarket_surveillance(self, category: str) -> Optional[str]:
        """Generate post-market surveillance plan."""
        return "MDR/FDA complaint handling system; periodic safety update reports; UDI implementation for traceability"
    
    def _ensure_exact_count(self, specs: List[DeviceSpecification], target_count: int) -> List[DeviceSpecification]:
        """Ensure exactly target_count specifications."""
        if len(specs) == target_count:
            return specs
        elif len(specs) > target_count:
            # Sort by composite score and take top N
            specs.sort(key=lambda s: s.spec_trace_scores.get('composite', 0), reverse=True)
            return specs[:target_count]
        else:
            self.logger.warning(f"Generated {len(specs)} specs but target was {target_count}")
            return specs