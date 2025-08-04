"""
Confidence Scoring and Risk Adjustment System
===========================================

Calculates confidence in assessments and applies risk adjustments based on
uncertainty levels and data quality.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import math
from .idea_score import IdeaScore


@dataclass
class ConfidenceAnalysis:
    """Comprehensive confidence analysis results"""

    overall_confidence: float
    data_quality_score: float
    assessment_consistency: float
    uncertainty_factors: List[str]
    confidence_breakdown: Dict[str, float]
    risk_adjustment_factor: float
    adjusted_scores: Dict[str, float]


class ConfidenceScorer:
    """
    Advanced confidence scoring system that evaluates the reliability
    of assessments and applies appropriate risk adjustments
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize confidence scorer"""
        if config is None:
            config = IdeaScore.load_config()

        self.config = config

        # Confidence thresholds
        self.high_confidence_threshold = config.get("high_confidence_threshold", 8.0)
        self.medium_confidence_threshold = config.get(
            "medium_confidence_threshold", 6.0
        )
        self.low_confidence_threshold = config.get("low_confidence_threshold", 4.0)

        # Risk adjustment parameters
        self.max_risk_adjustment = config.get(
            "max_risk_adjustment", 0.3
        )  # 30% max adjustment
        self.confidence_weight = config.get(
            "confidence_weight", 0.7
        )  # Weight for confidence in adjustment

        # Data quality factors and weights
        self.data_quality_factors = {
            "completeness": 0.25,
            "detail_level": 0.20,
            "consistency": 0.20,
            "specificity": 0.15,
            "validation_data": 0.20,
        }

    def calculate_confidence(
        self, idea: Dict[str, Any], idea_score: Optional[IdeaScore] = None
    ) -> ConfidenceAnalysis:
        """
        Calculate comprehensive confidence analysis for an idea

        Args:
            idea: Product idea dictionary
            idea_score: Optional pre-calculated IdeaScore

        Returns:
            ConfidenceAnalysis with detailed confidence assessment
        """
        if idea_score is None:
            idea_score = IdeaScore.from_idea_data(idea, self.config)

        # Calculate individual confidence factors
        data_quality_score = self._assess_data_quality(idea)
        assessment_consistency = self._assess_consistency(idea, idea_score)
        uncertainty_factors = self._identify_uncertainty_factors(idea, idea_score)

        # Calculate confidence breakdown
        confidence_breakdown = self._calculate_confidence_breakdown(
            idea, idea_score, data_quality_score, assessment_consistency
        )

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(confidence_breakdown)

        # Calculate risk adjustment factor
        risk_adjustment_factor = self._calculate_risk_adjustment_factor(
            overall_confidence, uncertainty_factors
        )

        # Apply risk adjustments to scores
        adjusted_scores = self._apply_risk_adjustments(
            idea_score, risk_adjustment_factor, overall_confidence
        )

        return ConfidenceAnalysis(
            overall_confidence=round(overall_confidence, 2),
            data_quality_score=round(data_quality_score, 2),
            assessment_consistency=round(assessment_consistency, 2),
            uncertainty_factors=uncertainty_factors,
            confidence_breakdown=confidence_breakdown,
            risk_adjustment_factor=round(risk_adjustment_factor, 3),
            adjusted_scores=adjusted_scores,
        )

    def _assess_data_quality(self, idea: Dict[str, Any]) -> float:
        """Assess the quality of available data for the idea"""
        quality_scores = {}

        # 1. Completeness assessment
        required_fields = [
            "name",
            "value_proposition",
            "target_segment",
            "viability_score",
            "innovation_score",
        ]
        optional_fields = ["features", "differentiation", "viability_details"]

        completeness = 0.0
        # Required fields (60% weight)
        for field in required_fields:
            if idea.get(field) and str(idea[field]).strip():
                completeness += 0.6 / len(required_fields)

        # Optional fields (40% weight)
        for field in optional_fields:
            if idea.get(field) and str(idea[field]).strip():
                completeness += 0.4 / len(optional_fields)

        quality_scores["completeness"] = min(10.0, completeness * 10)

        # 2. Detail level assessment
        text_fields = ["value_proposition", "features", "differentiation"]
        total_length = sum(len(str(idea.get(field, ""))) for field in text_fields)
        avg_length = total_length / len(text_fields)

        # Score based on average text length (more detail = higher confidence)
        detail_score = min(10.0, avg_length / 50)  # 500 chars = max score
        quality_scores["detail_level"] = detail_score

        # 3. Consistency assessment
        consistency_score = self._assess_field_consistency(idea)
        quality_scores["consistency"] = consistency_score

        # 4. Specificity assessment
        specificity_score = self._assess_specificity(idea)
        quality_scores["specificity"] = specificity_score

        # 5. Validation data assessment
        validation_score = self._assess_validation_data(idea)
        quality_scores["validation_data"] = validation_score

        # Calculate weighted average
        total_score = sum(
            score * self.data_quality_factors[factor]
            for factor, score in quality_scores.items()
        )

        return total_score

    def _assess_field_consistency(self, idea: Dict[str, Any]) -> float:
        """Assess consistency between different fields"""
        consistency_score = 8.0  # Start with high consistency assumption

        # Check for obvious inconsistencies
        viability = idea.get("viability_score", 5.0)
        innovation = idea.get("innovation_score", 5.0)

        # High innovation with very low viability might indicate inconsistency
        if innovation >= 8.0 and viability <= 3.0:
            consistency_score -= 2.0

        # Very high viability with very low innovation might also be suspicious
        if viability >= 9.0 and innovation <= 2.0:
            consistency_score -= 1.5

        # Check text consistency
        value_prop = idea.get("value_proposition", "").lower()
        features = str(idea.get("features", [])).lower()
        target = idea.get("target_segment", "").lower()

        # Check if target segment mentioned in value proposition
        if target and len(target) > 5:
            target_words = target.split()
            if not any(word in value_prop for word in target_words if len(word) > 3):
                consistency_score -= 0.5

        return max(0.0, consistency_score)

    def _assess_specificity(self, idea: Dict[str, Any]) -> float:
        """Assess how specific and concrete the descriptions are"""
        specificity_score = 0.0

        # Check value proposition specificity
        value_prop = idea.get("value_proposition", "").lower()

        # Specific metrics or numbers
        if any(char.isdigit() for char in value_prop):
            specificity_score += 2.0

        # Specific industry terms
        industry_terms = [
            "healthcare",
            "finance",
            "education",
            "retail",
            "manufacturing",
            "logistics",
            "saas",
            "b2b",
            "b2c",
            "api",
            "platform",
        ]
        for term in industry_terms:
            if term in value_prop:
                specificity_score += 0.5
                break

        # Specific technology mentions
        tech_terms = [
            "ai",
            "machine learning",
            "blockchain",
            "cloud",
            "mobile",
            "web",
            "analytics",
            "automation",
            "iot",
            "ar",
            "vr",
        ]
        for term in tech_terms:
            if term in value_prop:
                specificity_score += 0.5
                break

        # Specific problem statements
        problem_indicators = [
            "solve",
            "address",
            "eliminate",
            "reduce",
            "improve",
            "optimize",
            "streamline",
            "automate",
        ]
        for indicator in problem_indicators:
            if indicator in value_prop:
                specificity_score += 1.0
                break

        # Target segment specificity
        target = idea.get("target_segment", "").lower()
        if len(target) > 20:  # Detailed target description
            specificity_score += 1.5
        elif len(target) > 10:
            specificity_score += 1.0

        return min(10.0, specificity_score)

    def _assess_validation_data(self, idea: Dict[str, Any]) -> float:
        """Assess availability of validation or supporting data"""
        validation_score = 5.0  # Default middle score

        # Check for detailed viability breakdown
        viability_details = idea.get("viability_details", {})
        if isinstance(viability_details, dict) and len(viability_details) >= 4:
            validation_score += 2.0
        elif viability_details:
            validation_score += 1.0

        # Check for market or competitive data
        if any(
            field in idea
            for field in ["market_analysis", "competitive_analysis", "user_research"]
        ):
            validation_score += 2.0

        # Check for specific metrics or KPIs
        text_content = " ".join(
            [
                str(idea.get(field, ""))
                for field in ["value_proposition", "features", "differentiation"]
            ]
        ).lower()

        metric_indicators = [
            "%",
            "percent",
            "revenue",
            "cost",
            "time",
            "efficiency",
            "users",
            "customers",
            "market size",
            "roi",
            "growth",
        ]
        for indicator in metric_indicators:
            if indicator in text_content:
                validation_score += 0.5
                break

        return min(10.0, validation_score)

    def _assess_consistency(self, idea: Dict[str, Any], idea_score: IdeaScore) -> float:
        """Assess consistency of scoring with idea characteristics"""
        consistency_score = 8.0  # Start optimistic

        # Check viability vs innovation consistency
        if idea_score.innovation_score >= 9.0 and idea_score.viability_score <= 4.0:
            consistency_score -= 2.0  # Very innovative but not viable is suspicious

        # Check breakthrough vs viability consistency
        if idea_score.breakthrough_score >= 8.5 and idea_score.viability_score <= 3.0:
            consistency_score -= 1.5  # Breakthrough ideas should have some viability

        # Check confidence vs other scores consistency
        if idea_score.confidence_score >= 8.0:
            # High confidence should align with reasonable other scores
            if idea_score.viability_score <= 3.0 or idea_score.innovation_score <= 2.0:
                consistency_score -= 1.0

        # Check composite vs component consistency
        expected_composite = (
            idea_score.viability_score * 0.35
            + idea_score.innovation_score * 0.25
            + idea_score.breakthrough_score * 0.25
            + idea_score.confidence_score * 0.15
        )

        composite_diff = abs(idea_score.composite_score - expected_composite)
        if composite_diff > 1.0:
            consistency_score -= composite_diff

        return max(0.0, consistency_score)

    def _identify_uncertainty_factors(
        self, idea: Dict[str, Any], idea_score: IdeaScore
    ) -> List[str]:
        """Identify factors that increase uncertainty in the assessment"""
        uncertainty_factors = []

        # Low data quality factors
        if len(idea.get("value_proposition", "")) < 20:
            uncertainty_factors.append("Insufficient value proposition detail")

        if not idea.get("target_segment"):
            uncertainty_factors.append("Missing target segment definition")

        if not idea.get("features"):
            uncertainty_factors.append("No specific features described")

        # Score-based uncertainty factors
        if idea_score.confidence_score < self.medium_confidence_threshold:
            uncertainty_factors.append(
                f"Low base confidence score ({idea_score.confidence_score:.1f})"
            )

        # Viability detail uncertainty
        viability_details = idea.get("viability_details", {})
        if not isinstance(viability_details, dict) or len(viability_details) < 3:
            uncertainty_factors.append("Limited viability assessment detail")

        # Consistency uncertainty
        if abs(idea_score.innovation_score - idea_score.viability_score) > 4.0:
            uncertainty_factors.append(
                "Large gap between innovation and viability scores"
            )

        # Market validation uncertainty
        if "market" not in idea.get("value_proposition", "").lower():
            uncertainty_factors.append("Limited market context provided")

        # Technology uncertainty
        if idea_score.innovation_score >= 8.0:
            features = idea.get("features", [])
            if isinstance(features, list):
                features_text = " ".join(str(f) for f in features)
            else:
                features_text = str(features)

            text_content = (
                features_text + " " + str(idea.get("value_proposition", ""))
            ).lower()
            if not any(
                tech in text_content
                for tech in ["technology", "technical", "algorithm", "system"]
            ):
                uncertainty_factors.append(
                    "High innovation score but limited technical detail"
                )

        return uncertainty_factors

    def _calculate_confidence_breakdown(
        self,
        idea: Dict[str, Any],
        idea_score: IdeaScore,
        data_quality: float,
        consistency: float,
    ) -> Dict[str, float]:
        """Calculate detailed confidence breakdown"""
        breakdown = {}

        # Base confidence from IdeaScore
        breakdown["base_confidence"] = idea_score.confidence_score

        # Data quality contribution
        breakdown["data_quality"] = data_quality

        # Assessment consistency
        breakdown["assessment_consistency"] = consistency

        # Score reliability (how well-supported the scores are)
        score_reliability = self._assess_score_reliability(idea, idea_score)
        breakdown["score_reliability"] = score_reliability

        # External validation (if any supporting data exists)
        external_validation = self._assess_external_validation(idea)
        breakdown["external_validation"] = external_validation

        return breakdown

    def _assess_score_reliability(
        self, idea: Dict[str, Any], idea_score: IdeaScore
    ) -> float:
        """Assess how reliable the assigned scores appear"""
        reliability = 7.0  # Start with good reliability assumption

        # Check for extreme scores without justification
        if idea_score.innovation_score >= 9.0:
            # High innovation should be justified by description
            innovation_keywords = [
                "revolutionary",
                "breakthrough",
                "novel",
                "unprecedented",
                "innovative",
                "disruptive",
                "advanced",
            ]
            text = (
                idea.get("value_proposition", "") + str(idea.get("features", ""))
            ).lower()
            if not any(keyword in text for keyword in innovation_keywords):
                reliability -= 2.0

        if idea_score.viability_score >= 9.0:
            # High viability should be justified
            viability_keywords = [
                "proven",
                "tested",
                "validated",
                "feasible",
                "ready",
                "mature",
            ]
            text = idea.get("value_proposition", "").lower()
            if not any(keyword in text for keyword in viability_keywords):
                reliability -= 1.5

        # Check for balanced scoring
        score_variance = self._calculate_score_variance(idea_score)
        if score_variance > 8.0:  # Very high variance might indicate unreliable scoring
            reliability -= 1.0

        return max(0.0, reliability)

    def _calculate_score_variance(self, idea_score: IdeaScore) -> float:
        """Calculate variance in the scores"""
        scores = [
            idea_score.viability_score,
            idea_score.innovation_score,
            idea_score.breakthrough_score,
            idea_score.confidence_score,
        ]

        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)

        return variance

    def _assess_external_validation(self, idea: Dict[str, Any]) -> float:
        """Assess external validation indicators"""
        validation_score = 5.0  # Default neutral score

        # Look for validation indicators in text
        validation_indicators = [
            "research",
            "study",
            "survey",
            "market analysis",
            "user feedback",
            "prototype",
            "pilot",
            "beta",
        ]

        text_content = " ".join(
            [
                str(idea.get(field, ""))
                for field in ["value_proposition", "features", "differentiation"]
            ]
        ).lower()

        for indicator in validation_indicators:
            if indicator in text_content:
                validation_score += 1.0

        return min(10.0, validation_score)

    def _calculate_overall_confidence(self, breakdown: Dict[str, float]) -> float:
        """Calculate overall confidence from breakdown components"""
        # Weighted combination of confidence factors
        weights = {
            "base_confidence": 0.3,
            "data_quality": 0.25,
            "assessment_consistency": 0.2,
            "score_reliability": 0.15,
            "external_validation": 0.1,
        }

        overall = sum(
            breakdown.get(factor, 5.0) * weight for factor, weight in weights.items()
        )

        return min(10.0, max(0.0, overall))

    def _calculate_risk_adjustment_factor(
        self, confidence: float, uncertainty_factors: List[str]
    ) -> float:
        """Calculate risk adjustment factor based on confidence"""
        # Base adjustment based on confidence level
        if confidence >= self.high_confidence_threshold:
            base_adjustment = 0.0  # No adjustment for high confidence
        elif confidence >= self.medium_confidence_threshold:
            base_adjustment = 0.1  # Small adjustment for medium confidence
        elif confidence >= self.low_confidence_threshold:
            base_adjustment = 0.2  # Moderate adjustment for low confidence
        else:
            base_adjustment = (
                self.max_risk_adjustment
            )  # Maximum adjustment for very low confidence

        # Additional adjustment for uncertainty factors
        uncertainty_adjustment = min(0.1, len(uncertainty_factors) * 0.02)

        total_adjustment = min(
            self.max_risk_adjustment, base_adjustment + uncertainty_adjustment
        )

        return total_adjustment

    def _apply_risk_adjustments(
        self, idea_score: IdeaScore, risk_adjustment: float, confidence: float
    ) -> Dict[str, float]:
        """Apply risk adjustments to scores based on confidence"""
        adjusted_scores = {}

        # Adjust scores downward for uncertainty
        adjustment_factor = 1.0 - risk_adjustment

        # Apply adjustment with different sensitivities
        adjusted_scores["viability_score"] = (
            idea_score.viability_score * adjustment_factor
        )
        adjusted_scores["innovation_score"] = idea_score.innovation_score * (
            1.0 - risk_adjustment * 0.5
        )  # Less sensitive
        adjusted_scores["breakthrough_score"] = (
            idea_score.breakthrough_score * adjustment_factor
        )
        adjusted_scores["confidence_score"] = confidence  # Use calculated confidence

        # Recalculate composite score with adjusted components
        config = self.config
        weights = config.get("weights", {})
        w_viability = weights.get("viability", 0.35)
        w_innovation = weights.get("innovation", 0.25)
        w_breakthrough = weights.get("breakthrough", 0.25)
        w_confidence = weights.get("confidence", 0.15)

        adjusted_scores["composite_score"] = (
            adjusted_scores["viability_score"] * w_viability
            + adjusted_scores["innovation_score"] * w_innovation
            + adjusted_scores["breakthrough_score"] * w_breakthrough
            + adjusted_scores["confidence_score"] * w_confidence
        )

        # Round all scores
        for key in adjusted_scores:
            adjusted_scores[key] = round(adjusted_scores[key], 2)

        return adjusted_scores

    def get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence level"""
        if confidence >= self.high_confidence_threshold:
            return "High Confidence"
        elif confidence >= self.medium_confidence_threshold:
            return "Medium Confidence"
        elif confidence >= self.low_confidence_threshold:
            return "Low Confidence"
        else:
            return "Very Low Confidence"

    def get_adjustment_explanation(self, analysis: ConfidenceAnalysis) -> str:
        """Provide explanation for risk adjustments"""
        if analysis.risk_adjustment_factor <= 0.05:
            return (
                "Minimal risk adjustment applied due to high confidence in assessment"
            )
        elif analysis.risk_adjustment_factor <= 0.15:
            return f"Moderate risk adjustment ({analysis.risk_adjustment_factor:.1%}) applied due to assessment uncertainties"
        else:
            return f"Significant risk adjustment ({analysis.risk_adjustment_factor:.1%}) applied due to low confidence and multiple uncertainty factors"
