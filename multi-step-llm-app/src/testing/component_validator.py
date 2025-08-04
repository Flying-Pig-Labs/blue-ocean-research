"""
Component Validator

Validates component outputs against expected formats and content requirements.
Provides detailed validation reports and error analysis.
"""

import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import traceback

from ..utils.pipeline_logger import get_logger
from ..models.logging_models import ComponentType


@dataclass
class ValidationError:
    """Represents a validation error"""

    field: str
    error_type: str
    message: str
    severity: str = "error"  # error, warning, info

    def to_dict(self) -> Dict[str, str]:
        return {
            "field": self.field,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report"""

    is_valid: bool
    component_name: str
    validation_timestamp: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    errors: List[ValidationError]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "component_name": self.component_name,
            "validation_timestamp": self.validation_timestamp,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "errors": [error.to_dict() for error in self.errors],
            "details": self.details,
        }


class ComponentValidator:
    """Validates component outputs and behavior"""

    def __init__(self, logger=None):
        """Initialize the validator"""
        self.logger = logger or get_logger()
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load validation rules for each component"""
        return {
            "research_analyzer": {
                "required_fields": [
                    "pain_points",
                    "personas",
                    "solutions",
                    "verticals",
                ],
                "field_types": {
                    "pain_points": (list, dict),
                    "personas": (list, dict),
                    "solutions": (list, dict),
                    "verticals": (list, dict),
                },
                "min_items": {"pain_points": 3, "personas": 2, "solutions": 3},
                "content_requirements": {
                    "pain_points": {
                        "min_length": 50,
                        "must_contain": ["pain", "problem", "challenge"],
                    },
                    "personas": {
                        "min_length": 100,
                        "must_contain": ["person", "user", "customer"],
                    },
                    "solutions": {
                        "min_length": 50,
                        "must_contain": ["solution", "solve", "address"],
                    },
                },
            },
            "jobs_researcher": {
                "required_fields": ["jtbd_table", "research_summary"],
                "field_types": {"jtbd_table": (list, dict), "research_summary": str},
                "min_items": {"jtbd_table": 5},
                "content_requirements": {
                    "jtbd_table": {
                        "min_length": 100,
                        "must_contain": ["job", "done", "when"],
                    },
                    "research_summary": {
                        "min_length": 200,
                        "must_contain": ["research", "found", "data"],
                    },
                },
            },
            "cluster_jtbd": {
                "required_fields": ["clustered_zones", "cluster_summary"],
                "field_types": {
                    "clustered_zones": (list, dict),
                    "cluster_summary": str,
                },
                "min_items": {"clustered_zones": 3},
                "content_requirements": {
                    "clustered_zones": {
                        "min_length": 100,
                        "must_contain": ["zone", "cluster", "group"],
                    },
                    "cluster_summary": {
                        "min_length": 150,
                        "must_contain": ["cluster", "analysis", "pattern"],
                    },
                },
            },
            "value_curve_mapper": {
                "required_fields": ["value_curves", "competitive_analysis"],
                "field_types": {
                    "value_curves": (list, dict),
                    "competitive_analysis": (str, dict),
                },
                "min_items": {"value_curves": 4},
                "content_requirements": {
                    "value_curves": {
                        "min_length": 100,
                        "must_contain": ["value", "curve", "factor"],
                    },
                    "competitive_analysis": {
                        "min_length": 200,
                        "must_contain": ["competitive", "market", "analysis"],
                    },
                },
            },
            "product_idea_generator": {
                "required_fields": ["product_ideas", "viability_analysis"],
                "field_types": {
                    "product_ideas": (list, dict),
                    "viability_analysis": (str, dict),
                },
                "min_items": {"product_ideas": 3},
                "content_requirements": {
                    "product_ideas": {
                        "min_length": 150,
                        "must_contain": ["product", "idea", "solution"],
                    },
                    "viability_analysis": {
                        "min_length": 200,
                        "must_contain": ["viable", "feasible", "market"],
                    },
                },
            },
            "idea_consolidator": {
                "required_fields": ["consolidated_ideas", "final_recommendations"],
                "field_types": {
                    "consolidated_ideas": (list, dict),
                    "final_recommendations": (str, dict),
                },
                "min_items": {"consolidated_ideas": 2},
                "content_requirements": {
                    "consolidated_ideas": {
                        "min_length": 200,
                        "must_contain": ["consolidated", "refined", "idea"],
                    },
                    "final_recommendations": {
                        "min_length": 300,
                        "must_contain": ["recommend", "next", "step"],
                    },
                },
            },
            "main_pipeline": {
                "required_fields": ["workflow_steps", "execution_summary"],
                "field_types": {
                    "workflow_steps": (int, list),
                    "execution_summary": str,
                },
                "content_requirements": {
                    "execution_summary": {
                        "min_length": 100,
                        "must_contain": ["workflow", "completed", "step"],
                    }
                },
            },
        }

    def validate_component_output(
        self, component_name: str, output: Any, expected_outputs: List[str] = None
    ) -> ValidationReport:
        """Validate component output against rules and expectations"""
        from datetime import datetime

        errors = []
        details = {}
        total_checks = 0
        passed_checks = 0
        warnings = 0

        try:
            self.logger.info(
                f"Starting validation for component: {component_name}",
                ComponentType.MAIN_PIPELINE,
            )

            # Get validation rules for this component
            rules = self.validation_rules.get(component_name, {})
            if not rules:
                # Generic validation for unknown components
                return self._validate_generic_output(
                    component_name, output, expected_outputs
                )

            # Convert output to standardized format
            if isinstance(output, str):
                try:
                    output_data = json.loads(output)
                except json.JSONDecodeError:
                    output_data = {"raw_output": output}
            elif isinstance(output, dict):
                output_data = output
            else:
                output_data = {"output": output}

            details["output_type"] = type(output).__name__
            details["output_size"] = len(str(output))

            # 1. Check required fields
            required_fields = rules.get("required_fields", [])
            for field in required_fields:
                total_checks += 1
                if field in output_data:
                    passed_checks += 1
                    details[f"has_{field}"] = True
                else:
                    errors.append(
                        ValidationError(
                            field=field,
                            error_type="missing_field",
                            message=f"Required field '{field}' is missing from output",
                            severity="error",
                        )
                    )
                    details[f"has_{field}"] = False

            # 2. Check field types
            field_types = rules.get("field_types", {})
            for field, expected_types in field_types.items():
                total_checks += 1
                if field in output_data:
                    field_value = output_data[field]
                    if isinstance(field_value, expected_types):
                        passed_checks += 1
                        details[f"{field}_type_valid"] = True
                    else:
                        errors.append(
                            ValidationError(
                                field=field,
                                error_type="invalid_type",
                                message=f"Field '{field}' has type {type(field_value).__name__}, expected {[t.__name__ for t in (expected_types if isinstance(expected_types, tuple) else (expected_types,))]}",
                                severity="error",
                            )
                        )
                        details[f"{field}_type_valid"] = False
                else:
                    # Field missing - already reported above
                    details[f"{field}_type_valid"] = False

            # 3. Check minimum item counts
            min_items = rules.get("min_items", {})
            for field, min_count in min_items.items():
                total_checks += 1
                if field in output_data:
                    field_value = output_data[field]
                    if isinstance(field_value, (list, dict)):
                        actual_count = len(field_value)
                        if actual_count >= min_count:
                            passed_checks += 1
                            details[f"{field}_count"] = actual_count
                        else:
                            errors.append(
                                ValidationError(
                                    field=field,
                                    error_type="insufficient_items",
                                    message=f"Field '{field}' has {actual_count} items, minimum required: {min_count}",
                                    severity="warning",
                                )
                            )
                            warnings += 1
                            details[f"{field}_count"] = actual_count
                    else:
                        errors.append(
                            ValidationError(
                                field=field,
                                error_type="not_countable",
                                message=f"Field '{field}' is not a list or dict, cannot check item count",
                                severity="warning",
                            )
                        )
                        warnings += 1

            # 4. Check content requirements
            content_reqs = rules.get("content_requirements", {})
            for field, requirements in content_reqs.items():
                if field in output_data:
                    field_value = output_data[field]
                    content_str = self._extract_content_string(field_value)

                    # Check minimum length
                    total_checks += 1
                    min_length = requirements.get("min_length", 0)
                    if len(content_str) >= min_length:
                        passed_checks += 1
                        details[f"{field}_length_valid"] = True
                    else:
                        errors.append(
                            ValidationError(
                                field=field,
                                error_type="insufficient_content",
                                message=f"Field '{field}' content is {len(content_str)} chars, minimum required: {min_length}",
                                severity="warning",
                            )
                        )
                        warnings += 1
                        details[f"{field}_length_valid"] = False

                    # Check required content
                    must_contain = requirements.get("must_contain", [])
                    for keyword in must_contain:
                        total_checks += 1
                        if keyword.lower() in content_str.lower():
                            passed_checks += 1
                            details[f"{field}_contains_{keyword}"] = True
                        else:
                            errors.append(
                                ValidationError(
                                    field=field,
                                    error_type="missing_keyword",
                                    message=f"Field '{field}' does not contain required keyword: '{keyword}'",
                                    severity="info",
                                )
                            )
                            details[f"{field}_contains_{keyword}"] = False

            # 5. Check against expected outputs if provided
            if expected_outputs:
                for expected_field in expected_outputs:
                    total_checks += 1
                    if expected_field in output_data:
                        passed_checks += 1
                        details[f"expected_{expected_field}"] = True
                    else:
                        errors.append(
                            ValidationError(
                                field=expected_field,
                                error_type="missing_expected_output",
                                message=f"Expected output '{expected_field}' not found",
                                severity="warning",
                            )
                        )
                        warnings += 1
                        details[f"expected_{expected_field}"] = False

            # Determine overall validity
            failed_checks = total_checks - passed_checks
            error_count = len([e for e in errors if e.severity == "error"])
            is_valid = error_count == 0 and failed_checks <= warnings

            self.logger.info(
                f"Validation completed for {component_name}",
                ComponentType.MAIN_PIPELINE,
                metadata={
                    "is_valid": is_valid,
                    "total_checks": total_checks,
                    "passed_checks": passed_checks,
                    "errors": error_count,
                },
            )

            return ValidationReport(
                is_valid=is_valid,
                component_name=component_name,
                validation_timestamp=datetime.now().isoformat(),
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                warnings=warnings,
                errors=errors,
                details=details,
            )

        except Exception as e:
            self.logger.error(
                f"Error during validation of {component_name}: {e}",
                ComponentType.MAIN_PIPELINE,
                stack_trace=traceback.format_exc(),
            )

            return ValidationReport(
                is_valid=False,
                component_name=component_name,
                validation_timestamp=datetime.now().isoformat(),
                total_checks=1,
                passed_checks=0,
                failed_checks=1,
                warnings=0,
                errors=[
                    ValidationError(
                        field="validation",
                        error_type="validation_error",
                        message=f"Validation failed with error: {e}",
                        severity="error",
                    )
                ],
                details={"validation_error": str(e)},
            )

    def _validate_generic_output(
        self, component_name: str, output: Any, expected_outputs: List[str] = None
    ) -> ValidationReport:
        """Generic validation for unknown components"""
        from datetime import datetime

        errors = []
        details = {}
        total_checks = 1
        passed_checks = 1 if output is not None else 0

        details["output_type"] = type(output).__name__
        details["has_output"] = output is not None

        if output is None:
            errors.append(
                ValidationError(
                    field="output",
                    error_type="no_output",
                    message="Component produced no output",
                    severity="error",
                )
            )

        # Check if output has expected structure
        if expected_outputs and isinstance(output, dict):
            for expected_field in expected_outputs:
                total_checks += 1
                if expected_field in output:
                    passed_checks += 1
                    details[f"has_{expected_field}"] = True
                else:
                    errors.append(
                        ValidationError(
                            field=expected_field,
                            error_type="missing_expected_field",
                            message=f"Expected field '{expected_field}' not found in output",
                            severity="warning",
                        )
                    )
                    details[f"has_{expected_field}"] = False

        failed_checks = total_checks - passed_checks
        error_count = len([e for e in errors if e.severity == "error"])
        is_valid = error_count == 0

        return ValidationReport(
            is_valid=is_valid,
            component_name=component_name,
            validation_timestamp=datetime.now().isoformat(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=len([e for e in errors if e.severity in ["warning", "info"]]),
            errors=errors,
            details=details,
        )

    def _extract_content_string(self, value: Any) -> str:
        """Extract string content from various data types"""
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # Extract all string values and concatenate
            content_parts = []
            for v in value.values():
                if isinstance(v, str):
                    content_parts.append(v)
                elif isinstance(v, (list, dict)):
                    content_parts.append(self._extract_content_string(v))
            return " ".join(content_parts)
        elif isinstance(value, list):
            # Extract content from list items
            content_parts = []
            for item in value:
                content_parts.append(self._extract_content_string(item))
            return " ".join(content_parts)
        else:
            return str(value)

    def validate_api_response_format(
        self, response: Any, expected_format: str = "json"
    ) -> Tuple[bool, str]:
        """Validate API response format"""
        try:
            if expected_format == "json":
                if isinstance(response, dict):
                    return True, "Valid JSON object"
                elif isinstance(response, str):
                    json.loads(response)
                    return True, "Valid JSON string"
                else:
                    return False, f"Expected JSON, got {type(response).__name__}"

            elif expected_format == "text":
                if isinstance(response, str):
                    return True, "Valid text response"
                else:
                    return False, f"Expected text, got {type(response).__name__}"

            else:
                return True, f"Unknown format '{expected_format}', skipping validation"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"

    def validate_response_completeness(
        self, response: Any, min_length: int = 100
    ) -> Tuple[bool, str]:
        """Validate that response is complete and substantial"""
        response_str = str(response)

        if len(response_str) < min_length:
            return (
                False,
                f"Response too short: {len(response_str)} chars (minimum: {min_length})",
            )

        # Check for common truncation indicators
        truncation_indicators = [
            "...",
            "[truncated]",
            "[cut off]",
            "continued...",
            "etc.",
        ]
        for indicator in truncation_indicators:
            if indicator.lower() in response_str.lower():
                return False, f"Response appears truncated (found: {indicator})"

        return True, "Response appears complete"

    def create_validation_summary(
        self, reports: List[ValidationReport]
    ) -> Dict[str, Any]:
        """Create a summary of multiple validation reports"""
        if not reports:
            return {"error": "No validation reports provided"}

        total_components = len(reports)
        valid_components = sum(1 for r in reports if r.is_valid)
        invalid_components = total_components - valid_components

        total_checks = sum(r.total_checks for r in reports)
        total_passed = sum(r.passed_checks for r in reports)
        total_failed = sum(r.failed_checks for r in reports)
        total_warnings = sum(r.warnings for r in reports)

        all_errors = []
        for report in reports:
            for error in report.errors:
                all_errors.append(
                    {"component": report.component_name, **error.to_dict()}
                )

        return {
            "summary": {
                "total_components": total_components,
                "valid_components": valid_components,
                "invalid_components": invalid_components,
                "overall_success_rate": (valid_components / total_components) * 100
                if total_components > 0
                else 0,
            },
            "checks": {
                "total_checks": total_checks,
                "passed_checks": total_passed,
                "failed_checks": total_failed,
                "warnings": total_warnings,
                "pass_rate": (total_passed / total_checks) * 100
                if total_checks > 0
                else 0,
            },
            "errors": all_errors,
            "component_results": [
                {
                    "component": report.component_name,
                    "is_valid": report.is_valid,
                    "passed_checks": report.passed_checks,
                    "total_checks": report.total_checks,
                    "error_count": len(
                        [e for e in report.errors if e.severity == "error"]
                    ),
                }
                for report in reports
            ],
        }
