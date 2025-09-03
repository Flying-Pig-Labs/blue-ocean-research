#!/usr/bin/env python3
"""
QA Guardrails Module - Validation, Determinism, and Quality Assurance

Provides comprehensive validation and quality assurance for the modular pipeline.
Ensures schema compliance, deterministic results, and proper output validation.
"""

import json
import hashlib
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of validation checks."""
    passed: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]

@dataclass
class RunManifest:
    """Complete run manifest with metadata and validation hashes."""
    run_id: str
    flavor_name: str
    pipeline_version: str
    execution_timestamp: str
    
    # Input data hashes (for determinism verification)
    input_hashes: Dict[str, str]
    
    # Output validation
    total_opportunities: int
    schema_validation_passed: bool
    determinism_hash: str
    
    # GitHub artifact info
    repository_url: Optional[str]
    issue_count: int
    issue_numbers: List[int]
    
    # Quality metrics
    confidence_scores: Dict[str, float]  # min, max, avg confidence
    framework_coverage: Dict[str, float]  # framework dimension coverage
    citation_quality: Dict[str, Any]  # citation analysis
    
    # Validation details
    validation_errors: List[str]
    validation_warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

class SchemaValidator:
    """Validates opportunities against their defined schemas."""
    
    def __init__(self, schema_type: str, required_fields: List[str], optional_fields: List[str] = None):
        """Initialize validator with schema definition."""
        self.schema_type = schema_type
        self.required_fields = set(required_fields)
        self.optional_fields = set(optional_fields or [])
        self.all_fields = self.required_fields | self.optional_fields
        
        # Define field type requirements
        self.field_types = {
            'id': str,
            'title': str,
            'description': str,
            'rationale': str,
            'citations': list,
            'confidence_score': (int, float),
            'zone_id': str,
            'zone_name': str,
            'framework_scores': dict,
            'created_timestamp': str,
            # Business idea specific
            'target_market': str,
            'value_proposition': str,
            'revenue_model': str,
            'risk_factors': list,
            # Site candidate specific
            'location_type': str,
            'site_requirements': list,
            'accessibility_score': (int, float),
            'zoning_requirements': list,
            # Device spec specific
            'device_category': str,
            'target_population': str,
            'functional_requirements': list,
            'safety_specifications': list
        }
    
    def validate_opportunity(self, opportunity: Dict[str, Any]) -> ValidationResult:
        """Validate a single opportunity against schema."""
        errors = []
        warnings = []
        details = {}
        
        # Check required fields
        missing_required = self.required_fields - set(opportunity.keys())
        if missing_required:
            errors.append(f"Missing required fields: {list(missing_required)}")
        
        # Check for unexpected fields
        unexpected_fields = set(opportunity.keys()) - self.all_fields
        if unexpected_fields:
            warnings.append(f"Unexpected fields (will be ignored): {list(unexpected_fields)}")
        
        # Validate field types and constraints
        for field, value in opportunity.items():
            if field in self.field_types:
                expected_type = self.field_types[field]
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        errors.append(f"Field '{field}' must be of type {expected_type}, got {type(value)}")
                else:
                    if not isinstance(value, expected_type):
                        errors.append(f"Field '{field}' must be of type {expected_type.__name__}, got {type(value).__name__}")
        
        # Validate specific field constraints
        if 'confidence_score' in opportunity:
            score = opportunity['confidence_score']
            if isinstance(score, (int, float)):
                if not 0.0 <= score <= 1.0:
                    errors.append("confidence_score must be between 0.0 and 1.0")
            
        if 'framework_scores' in opportunity:
            scores = opportunity['framework_scores']
            if isinstance(scores, dict):
                for dim, score in scores.items():
                    if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                        errors.append(f"framework_scores['{dim}'] must be between 0.0 and 1.0")
        
        if 'citations' in opportunity:
            citations = opportunity['citations']
            if isinstance(citations, list):
                if len(citations) == 0:
                    warnings.append("citations list is empty - opportunities should have supporting evidence")
                elif len(citations) > 10:
                    warnings.append("citations list is very long (>10) - consider summarizing key evidence")
        
        # Schema-specific validations
        if self.schema_type == 'business_idea':
            if 'risk_factors' in opportunity:
                risks = opportunity['risk_factors']
                if isinstance(risks, list) and len(risks) == 0:
                    warnings.append("risk_factors is empty - business ideas should identify potential risks")
        
        elif self.schema_type == 'device_spec':
            if 'safety_specifications' in opportunity:
                safety_specs = opportunity['safety_specifications']
                if isinstance(safety_specs, list) and len(safety_specs) == 0:
                    errors.append("safety_specifications cannot be empty for medical devices")
        
        # Calculate validation details
        details['field_count'] = len(opportunity)
        details['required_field_coverage'] = len(self.required_fields & set(opportunity.keys())) / len(self.required_fields)
        details['optional_field_usage'] = len(self.optional_fields & set(opportunity.keys())) / len(self.optional_fields) if self.optional_fields else 0
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def validate_opportunities(self, opportunities: List[Dict[str, Any]]) -> ValidationResult:
        """Validate all opportunities in a batch."""
        all_errors = []
        all_warnings = []
        all_details = {}
        
        if not opportunities:
            return ValidationResult(
                passed=False,
                errors=["No opportunities provided for validation"],
                warnings=[],
                details={}
            )
        
        # Validate each opportunity
        individual_results = []
        for i, opportunity in enumerate(opportunities):
            result = self.validate_opportunity(opportunity)
            individual_results.append(result)
            
            # Collect errors/warnings with opportunity context
            for error in result.errors:
                all_errors.append(f"Opportunity {i+1} ({opportunity.get('id', 'unknown')}): {error}")
            
            for warning in result.warnings:
                all_warnings.append(f"Opportunity {i+1} ({opportunity.get('id', 'unknown')}): {warning}")
        
        # Overall validation statistics
        passed_count = sum(1 for r in individual_results if r.passed)
        all_details['total_opportunities'] = len(opportunities)
        all_details['passed_validation'] = passed_count
        all_details['failed_validation'] = len(opportunities) - passed_count
        all_details['validation_rate'] = passed_count / len(opportunities)
        
        # Aggregate field coverage stats
        coverage_scores = [r.details.get('required_field_coverage', 0) for r in individual_results]
        all_details['avg_field_coverage'] = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        
        return ValidationResult(
            passed=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            details=all_details
        )

class DeterminismChecker:
    """Checks for deterministic behavior and reproducibility."""
    
    @staticmethod
    def calculate_content_hash(content: Any) -> str:
        """Calculate deterministic hash of content."""
        if isinstance(content, dict):
            # Sort dict keys for consistent hashing
            sorted_content = json.dumps(content, sort_keys=True, default=str)
        elif isinstance(content, list):
            # Convert to JSON with sorted dicts
            sorted_content = json.dumps(content, sort_keys=True, default=str)
        else:
            sorted_content = str(content)
        
        return hashlib.sha256(sorted_content.encode()).hexdigest()
    
    @staticmethod
    def check_opportunity_determinism(opportunities: List[Dict[str, Any]]) -> ValidationResult:
        """Check if opportunities are deterministically generated."""
        errors = []
        warnings = []
        details = {}
        
        if not opportunities:
            return ValidationResult(
                passed=False,
                errors=["No opportunities to check for determinism"],
                warnings=[],
                details={}
            )
        
        # Check for duplicate IDs
        ids = [opp.get('id') for opp in opportunities]
        duplicate_ids = [id for id in set(ids) if ids.count(id) > 1]
        if duplicate_ids:
            errors.append(f"Duplicate opportunity IDs found: {duplicate_ids}")
        
        # Check for deterministic ID format
        id_pattern_consistent = True
        for opp in opportunities:
            opp_id = opp.get('id', '')
            if not opp_id.startswith('opp_') or len(opp_id) != 12:  # opp_ + 8 hex chars
                id_pattern_consistent = False
                break
        
        if not id_pattern_consistent:
            warnings.append("Opportunity IDs don't follow expected deterministic pattern (opp_xxxxxxxx)")
        
        # Check timestamp consistency (all should be from same run)
        timestamps = [opp.get('created_timestamp') for opp in opportunities if 'created_timestamp' in opp]
        if timestamps:
            timestamp_range = max(timestamps) - min(timestamps) if len(set(timestamps)) > 1 else 0
            # Allow up to 5 minutes of variance for processing time
            if len(set([t[:16] for t in timestamps])) > 1:  # More than 1 minute variance
                warnings.append("Large timestamp variance suggests non-deterministic generation timing")
        
        # Calculate overall determinism hash
        determinism_data = {
            'opportunity_ids': sorted([opp.get('id') for opp in opportunities]),
            'titles': sorted([opp.get('title') for opp in opportunities]),
            'zone_mappings': sorted([(opp.get('id'), opp.get('zone_id')) for opp in opportunities])
        }
        determinism_hash = DeterminismChecker.calculate_content_hash(determinism_data)
        
        details['total_opportunities'] = len(opportunities)
        details['unique_ids'] = len(set(ids))
        details['id_format_consistent'] = id_pattern_consistent
        details['determinism_hash'] = determinism_hash
        details['timestamp_variance'] = len(set([t[:16] for t in timestamps])) if timestamps else 0
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )

class QualityAnalyzer:
    """Analyzes opportunity quality metrics."""
    
    @staticmethod
    def analyze_confidence_distribution(opportunities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze confidence score distribution."""
        confidence_scores = [opp.get('confidence_score', 0) for opp in opportunities]
        
        if not confidence_scores:
            return {'min': 0, 'max': 0, 'avg': 0, 'std': 0}
        
        return {
            'min': min(confidence_scores),
            'max': max(confidence_scores),
            'avg': sum(confidence_scores) / len(confidence_scores),
            'std': (sum((x - sum(confidence_scores)/len(confidence_scores))**2 for x in confidence_scores) / len(confidence_scores))**0.5
        }
    
    @staticmethod
    def analyze_framework_coverage(opportunities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze framework dimension coverage across opportunities."""
        all_dimensions = set()
        dimension_scores = {}
        
        # Collect all framework dimensions
        for opp in opportunities:
            framework_scores = opp.get('framework_scores', {})
            for dim, score in framework_scores.items():
                all_dimensions.add(dim)
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(score)
        
        # Calculate coverage statistics
        coverage_stats = {}
        for dim in all_dimensions:
            scores = dimension_scores[dim]
            coverage_stats[dim] = {
                'avg_score': sum(scores) / len(scores),
                'coverage_rate': len(scores) / len(opportunities),  # How many opps have this dimension
                'above_threshold': sum(1 for s in scores if s > 0.5) / len(scores)  # % above 0.5
            }
        
        return coverage_stats
    
    @staticmethod
    def analyze_citation_quality(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quality of citations and evidence."""
        total_citations = 0
        opportunities_with_citations = 0
        citation_lengths = []
        
        for opp in opportunities:
            citations = opp.get('citations', [])
            if citations:
                opportunities_with_citations += 1
                total_citations += len(citations)
                citation_lengths.extend([len(str(citation)) for citation in citations])
        
        avg_citation_length = sum(citation_lengths) / len(citation_lengths) if citation_lengths else 0
        
        return {
            'total_citations': total_citations,
            'avg_citations_per_opportunity': total_citations / len(opportunities) if opportunities else 0,
            'opportunities_with_citations': opportunities_with_citations,
            'citation_coverage': opportunities_with_citations / len(opportunities) if opportunities else 0,
            'avg_citation_length': avg_citation_length
        }

class QAGuardrails:
    """Main QA and validation orchestrator."""
    
    def __init__(self, flavor_config: Any):
        """Initialize QA system with flavor configuration."""
        self.flavor_config = flavor_config
        self.schema_validator = SchemaValidator(
            flavor_config.output.schema_type.value,
            flavor_config.output.required_fields,
            getattr(flavor_config.output, 'optional_fields', [])
        )
    
    def validate_pipeline_output(
        self,
        opportunities: List[Dict[str, Any]],
        framework_results: List[Any],
        github_results: Dict[str, Any] = None,
        expected_count: int = 10
    ) -> Tuple[ValidationResult, RunManifest]:
        """
        Complete validation of pipeline output.
        
        Args:
            opportunities: Generated opportunities
            framework_results: Framework analysis results  
            github_results: GitHub artifact creation results
            expected_count: Expected number of opportunities
            
        Returns:
            Tuple of (ValidationResult, RunManifest)
        """
        all_errors = []
        all_warnings = []
        
        # 1. Schema Validation
        logger.info("Performing schema validation...")
        schema_result = self.schema_validator.validate_opportunities(opportunities)
        all_errors.extend(schema_result.errors)
        all_warnings.extend(schema_result.warnings)
        
        # 2. Count Validation
        logger.info(f"Validating opportunity count (expected: {expected_count})...")
        if len(opportunities) != expected_count:
            all_errors.append(f"Expected exactly {expected_count} opportunities, got {len(opportunities)}")
        
        # 3. Determinism Check
        logger.info("Checking deterministic behavior...")
        determinism_result = DeterminismChecker.check_opportunity_determinism(opportunities)
        all_errors.extend(determinism_result.errors)
        all_warnings.extend(determinism_result.warnings)
        
        # 4. GitHub Issue Validation (if applicable)
        if github_results:
            logger.info("Validating GitHub integration...")
            issues_created = github_results.get('summary', {}).get('issues_created_or_updated', 0)
            if issues_created != expected_count:
                all_errors.append(f"Expected {expected_count} GitHub issues, created/updated {issues_created}")
        
        # 5. Quality Analysis
        logger.info("Performing quality analysis...")
        confidence_stats = QualityAnalyzer.analyze_confidence_distribution(opportunities)
        framework_coverage = QualityAnalyzer.analyze_framework_coverage(opportunities)
        citation_quality = QualityAnalyzer.analyze_citation_quality(opportunities)
        
        # Quality warnings
        if confidence_stats['avg'] < 0.5:
            all_warnings.append(f"Low average confidence score: {confidence_stats['avg']:.2f}")
        
        if citation_quality['citation_coverage'] < 0.8:
            all_warnings.append(f"Low citation coverage: {citation_quality['citation_coverage']:.1%} of opportunities have citations")
        
        # Generate Run Manifest
        run_manifest = self._generate_run_manifest(
            opportunities=opportunities,
            framework_results=framework_results,
            github_results=github_results,
            confidence_stats=confidence_stats,
            framework_coverage=framework_coverage,
            citation_quality=citation_quality,
            determinism_hash=determinism_result.details.get('determinism_hash', ''),
            validation_errors=all_errors,
            validation_warnings=all_warnings
        )
        
        # Overall validation result
        overall_result = ValidationResult(
            passed=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            details={
                'schema_validation': schema_result.details,
                'determinism_check': determinism_result.details,
                'confidence_stats': confidence_stats,
                'framework_coverage': framework_coverage,
                'citation_quality': citation_quality
            }
        )
        
        return overall_result, run_manifest
    
    def _generate_run_manifest(
        self,
        opportunities: List[Dict[str, Any]],
        framework_results: List[Any],
        github_results: Dict[str, Any] = None,
        confidence_stats: Dict[str, float] = None,
        framework_coverage: Dict[str, Any] = None,
        citation_quality: Dict[str, Any] = None,
        determinism_hash: str = '',
        validation_errors: List[str] = None,
        validation_warnings: List[str] = None
    ) -> RunManifest:
        """Generate comprehensive run manifest."""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.flavor_config.name}"
        
        # Calculate input hashes for reproducibility
        input_hashes = {
            'flavor_config': DeterminismChecker.calculate_content_hash(self.flavor_config.name),
            'framework_results': DeterminismChecker.calculate_content_hash([r.to_dict() if hasattr(r, 'to_dict') else str(r) for r in framework_results])
        }
        
        # Extract GitHub info
        repo_url = github_results.get('repository', {}).get('html_url') if github_results else None
        issue_numbers = [issue.get('issue_number') for issue in github_results.get('issues', []) if 'issue_number' in issue] if github_results else []
        
        return RunManifest(
            run_id=run_id,
            flavor_name=self.flavor_config.name,
            pipeline_version="2.0.0",
            execution_timestamp=datetime.now().isoformat(),
            
            input_hashes=input_hashes,
            
            total_opportunities=len(opportunities),
            schema_validation_passed=len(validation_errors or []) == 0,
            determinism_hash=determinism_hash,
            
            repository_url=repo_url,
            issue_count=len(issue_numbers),
            issue_numbers=issue_numbers,
            
            confidence_scores=confidence_stats or {},
            framework_coverage=framework_coverage or {},
            citation_quality=citation_quality or {},
            
            validation_errors=validation_errors or [],
            validation_warnings=validation_warnings or []
        )
    
    def save_manifest(self, manifest: RunManifest, output_path: str = None) -> str:
        """Save run manifest to JSON file."""
        if not output_path:
            output_path = f"manifest_{manifest.flavor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Run manifest saved to: {output_path}")
        return output_path

def validate_pipeline_output(
    opportunities: List[Dict[str, Any]],
    flavor_config: Any,
    framework_results: List[Any],
    github_results: Dict[str, Any] = None,
    expected_count: int = 10,
    save_manifest: bool = True
) -> Tuple[bool, str]:
    """
    Main validation function for pipeline outputs.
    
    Args:
        opportunities: Generated opportunities  
        flavor_config: Flavor configuration
        framework_results: Framework analysis results
        github_results: GitHub creation results (optional)
        expected_count: Expected number of opportunities
        save_manifest: Whether to save validation manifest
        
    Returns:
        Tuple of (validation_passed, manifest_path)
    """
    qa = QAGuardrails(flavor_config)
    
    try:
        validation_result, manifest = qa.validate_pipeline_output(
            opportunities=opportunities,
            framework_results=framework_results,
            github_results=github_results,
            expected_count=expected_count
        )
        
        # Log validation results
        if validation_result.passed:
            logger.info("✅ All validation checks passed!")
        else:
            logger.error(f"❌ Validation failed with {len(validation_result.errors)} errors")
            for error in validation_result.errors:
                logger.error(f"  - {error}")
        
        if validation_result.warnings:
            logger.warning(f"⚠️ {len(validation_result.warnings)} warnings:")
            for warning in validation_result.warnings:
                logger.warning(f"  - {warning}")
        
        # Save manifest
        manifest_path = None
        if save_manifest:
            manifest_path = qa.save_manifest(manifest)
        
        return validation_result.passed, manifest_path
        
    except Exception as e:
        logger.error(f"QA validation failed: {e}")
        return False, None