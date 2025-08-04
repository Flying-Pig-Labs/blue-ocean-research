"""
Smart Filtering System with Excellence Preservation
=================================================

Implements adaptive filtering that preserves excellent ideas while optimizing
portfolio selection across opportunity zones.
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import math
from .idea_score import IdeaScore
from .breakthrough_detector import BreakthroughDetector, BreakthroughAnalysis


@dataclass
class FilteringResults:
    """Results of smart filtering process"""

    selected_ideas: List[Dict[str, Any]]
    dropped_ideas: List[Dict[str, Any]]
    excellence_preserved: List[Dict[str, Any]]
    quota_adjustments: Dict[str, Any]
    filtering_stats: Dict[str, Any]
    warnings: List[str]


class SmartFilterer:
    """
    Advanced filtering system that preserves excellence while optimizing
    portfolio selection across opportunity zones
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize smart filterer with configuration"""
        if config is None:
            config = IdeaScore.load_config()

        self.config = config
        self.breakthrough_detector = BreakthroughDetector(config)

        # Filtering thresholds
        self.excellence_threshold = config.get("excellence_threshold", 8.5)
        self.moonshot_preservation_threshold = config.get(
            "moonshot_preservation_threshold", 8.0
        )
        self.minimum_viable_score = config.get("minimum_viable_score", 4.0)

        # Adaptive filtering parameters
        self.base_quota_flexibility = config.get(
            "base_quota_flexibility", 0.2
        )  # 20% flexibility
        self.excellence_quota_boost = config.get(
            "excellence_quota_boost", 0.3
        )  # 30% boost for excellence
        self.min_ideas_per_zone = config.get("min_ideas_per_zone", 1)
        self.max_ideas_per_zone = config.get("max_ideas_per_zone", 8)

    def filter_ideas(self, zone_results: List[Dict[str, Any]]) -> FilteringResults:
        """
        Apply smart filtering across all opportunity zones

        Args:
            zone_results: List of zone processing results

        Returns:
            FilteringResults with selected ideas and analysis
        """
        # Step 1: Score all ideas and detect breakthroughs
        scored_zones = self._score_all_ideas(zone_results)

        # Step 2: Identify excellence ideas that must be preserved
        excellence_ideas = self._identify_excellence_ideas(scored_zones)

        # Step 3: Calculate flexible quotas based on zone importance and idea quality
        flexible_quotas = self._calculate_flexible_quotas(
            scored_zones, excellence_ideas
        )

        # Step 4: Apply smart selection strategy
        selected_ideas, dropped_ideas, warnings = self._smart_select(
            scored_zones, flexible_quotas, excellence_ideas
        )

        # Step 5: Generate filtering statistics
        filtering_stats = self._generate_filtering_stats(
            scored_zones, selected_ideas, dropped_ideas, excellence_ideas
        )

        return FilteringResults(
            selected_ideas=selected_ideas,
            dropped_ideas=dropped_ideas,
            excellence_preserved=excellence_ideas,
            quota_adjustments=flexible_quotas,
            filtering_stats=filtering_stats,
            warnings=warnings,
        )

    def _score_all_ideas(
        self, zone_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score all ideas with comprehensive scoring system"""
        scored_zones = []

        for zone_result in zone_results:
            zone_data = zone_result.copy()
            scored_ideas = []

            all_ideas = zone_result.get("all_ideas", [])
            zone_name = zone_result.get("zone", {}).get("name", "Unknown")

            for idea in all_ideas:
                # Add zone context to idea
                idea["zone_name"] = zone_name

                # Calculate comprehensive scores
                idea_score = IdeaScore.from_idea_data(idea, self.config)
                breakthrough_analysis = self.breakthrough_detector.analyze_idea(
                    idea, idea_score
                )

                # Add scoring data to idea
                idea["scoring"] = {
                    "idea_score": idea_score,
                    "breakthrough_analysis": breakthrough_analysis,
                    "composite_score": idea_score.composite_score,
                    "is_excellence": idea_score.composite_score
                    >= self.excellence_threshold,
                    "is_moonshot": breakthrough_analysis.is_moonshot,
                    "is_breakthrough": breakthrough_analysis.is_breakthrough,
                    "risk_level": idea_score.get_risk_level(),
                }

                scored_ideas.append(idea)

            zone_data["scored_ideas"] = scored_ideas
            scored_zones.append(zone_data)

        return scored_zones

    def _identify_excellence_ideas(
        self, scored_zones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify ideas that must be preserved due to excellence"""
        excellence_ideas = []

        for zone_data in scored_zones:
            for idea in zone_data.get("scored_ideas", []):
                scoring = idea.get("scoring", {})

                # Excellence criteria
                is_excellent = (
                    scoring.get("composite_score", 0) >= self.excellence_threshold
                    or scoring.get("is_moonshot", False)
                    or (
                        scoring.get("is_breakthrough", False)
                        and scoring.get("idea_score").viability_score >= 6.0
                    )
                )

                if is_excellent:
                    idea["preservation_reason"] = self._get_preservation_reason(scoring)
                    excellence_ideas.append(idea)

        return excellence_ideas

    def _get_preservation_reason(self, scoring: Dict[str, Any]) -> str:
        """Get reason why idea should be preserved"""
        reasons = []

        if scoring.get("composite_score", 0) >= self.excellence_threshold:
            reasons.append(
                f"High composite score ({scoring.get('composite_score', 0):.1f})"
            )

        if scoring.get("is_moonshot", False):
            reasons.append("Moonshot potential")

        if scoring.get("is_breakthrough", False):
            reasons.append("Breakthrough innovation")

        idea_score = scoring.get("idea_score")
        if idea_score and idea_score.innovation_score >= 9.0:
            reasons.append(
                f"Exceptional innovation ({idea_score.innovation_score:.1f})"
            )

        return "; ".join(reasons) if reasons else "Excellence criteria met"

    def _calculate_flexible_quotas(
        self, scored_zones: List[Dict[str, Any]], excellence_ideas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate adaptive quotas based on zone quality and importance"""
        zone_quotas = {}
        total_original_quota = 0
        total_flexible_quota = 0

        # Calculate excellence distribution by zone
        excellence_by_zone = {}
        for idea in excellence_ideas:
            zone_name = idea.get("zone_name", "Unknown")
            excellence_by_zone[zone_name] = excellence_by_zone.get(zone_name, 0) + 1

        for zone_data in scored_zones:
            zone = zone_data.get("zone", {})
            zone_name = zone.get("name", "Unknown")
            importance_percentage = zone.get("importance_percentage", 50)
            scored_ideas = zone_data.get("scored_ideas", [])

            # Original quota calculation
            original_quota = max(
                1, round(len(scored_ideas) * (importance_percentage / 100))
            )
            total_original_quota += original_quota

            # Calculate zone quality metrics
            avg_composite_score = self._calculate_average_score(
                scored_ideas, "composite_score"
            )
            breakthrough_count = sum(
                1
                for idea in scored_ideas
                if idea.get("scoring", {}).get("is_breakthrough", False)
            )
            excellence_count = excellence_by_zone.get(zone_name, 0)

            # Quality-based adjustments
            quality_multiplier = 1.0

            # Boost for high-quality zones
            if avg_composite_score >= 7.5:
                quality_multiplier += 0.3
            elif avg_composite_score >= 6.5:
                quality_multiplier += 0.15

            # Boost for breakthrough-rich zones
            if breakthrough_count >= 3:
                quality_multiplier += 0.2
            elif breakthrough_count >= 2:
                quality_multiplier += 0.1

            # Boost for excellence-rich zones
            if excellence_count >= 2:
                quality_multiplier += self.excellence_quota_boost
            elif excellence_count >= 1:
                quality_multiplier += self.excellence_quota_boost / 2

            # Apply flexibility
            flexible_quota = original_quota * quality_multiplier
            flexible_quota = max(
                self.min_ideas_per_zone,
                min(self.max_ideas_per_zone, round(flexible_quota)),
            )

            total_flexible_quota += flexible_quota

            zone_quotas[zone_name] = {
                "original_quota": original_quota,
                "flexible_quota": flexible_quota,
                "quality_multiplier": quality_multiplier,
                "avg_composite_score": avg_composite_score,
                "breakthrough_count": breakthrough_count,
                "excellence_count": excellence_count,
                "adjustment_reason": self._get_adjustment_reason(
                    quality_multiplier,
                    avg_composite_score,
                    breakthrough_count,
                    excellence_count,
                ),
            }

        # Add summary statistics
        zone_quotas["_summary"] = {
            "total_original_quota": total_original_quota,
            "total_flexible_quota": total_flexible_quota,
            "total_adjustment": total_flexible_quota - total_original_quota,
            "adjustment_percentage": (
                (total_flexible_quota - total_original_quota)
                / total_original_quota
                * 100
            )
            if total_original_quota > 0
            else 0,
        }

        return zone_quotas

    def _get_adjustment_reason(
        self,
        quality_multiplier: float,
        avg_score: float,
        breakthrough_count: int,
        excellence_count: int,
    ) -> str:
        """Generate explanation for quota adjustments"""
        if quality_multiplier <= 1.05:
            return "No significant adjustment"

        reasons = []

        if avg_score >= 7.5:
            reasons.append("High average quality")
        elif avg_score >= 6.5:
            reasons.append("Above average quality")

        if breakthrough_count >= 3:
            reasons.append("High breakthrough density")
        elif breakthrough_count >= 2:
            reasons.append("Multiple breakthroughs")

        if excellence_count >= 2:
            reasons.append("Multiple excellence ideas")
        elif excellence_count >= 1:
            reasons.append("Excellence idea present")

        return "; ".join(reasons) if reasons else "Quality-based adjustment"

    def _smart_select(
        self,
        scored_zones: List[Dict[str, Any]],
        flexible_quotas: Dict[str, Any],
        excellence_ideas: List[Dict[str, Any]],
    ) -> Tuple[List[Dict], List[Dict], List[str]]:
        """Apply intelligent selection strategy"""
        selected_ideas = []
        dropped_ideas = []
        warnings = []

        # Track excellence ideas to ensure they're selected
        excellence_ids = {id(idea) for idea in excellence_ideas}

        for zone_data in scored_zones:
            zone_name = zone_data.get("zone", {}).get("name", "Unknown")
            scored_ideas = zone_data.get("scored_ideas", [])
            quota_info = flexible_quotas.get(zone_name, {})
            target_quota = quota_info.get("flexible_quota", 1)

            # Sort ideas by selection priority
            prioritized_ideas = self._prioritize_ideas_for_selection(scored_ideas)

            # Select ideas using multi-criteria approach
            zone_selected, zone_dropped, zone_warnings = self._select_from_zone(
                prioritized_ideas, target_quota, excellence_ids, zone_name
            )

            selected_ideas.extend(zone_selected)
            dropped_ideas.extend(zone_dropped)
            warnings.extend(zone_warnings)

        # Final safety check for excellence preservation
        excellence_warnings = self._verify_excellence_preservation(
            selected_ideas, excellence_ideas
        )
        warnings.extend(excellence_warnings)

        return selected_ideas, dropped_ideas, warnings

    def _prioritize_ideas_for_selection(
        self, ideas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize ideas for selection using multi-criteria ranking"""

        def priority_score(idea):
            scoring = idea.get("scoring", {})
            idea_score = scoring.get("idea_score")

            if not idea_score:
                return 0.0

            # Base score
            priority = idea_score.composite_score

            # Excellence boost
            if scoring.get("is_excellence", False):
                priority += 3.0

            # Moonshot boost
            if scoring.get("is_moonshot", False):
                priority += 2.5

            # Breakthrough boost
            if scoring.get("is_breakthrough", False):
                priority += 2.0

            # High innovation boost
            if idea_score.innovation_score >= 8.5:
                priority += 1.5

            # Balanced viability boost (not too high, not too low)
            if 6.0 <= idea_score.viability_score <= 8.5:
                priority += 1.0

            # High confidence boost
            if idea_score.confidence_score >= 8.0:
                priority += 0.5

            return priority

        return sorted(ideas, key=priority_score, reverse=True)

    def _select_from_zone(
        self,
        prioritized_ideas: List[Dict[str, Any]],
        target_quota: int,
        excellence_ids: set,
        zone_name: str,
    ) -> Tuple[List[Dict], List[Dict], List[str]]:
        """Select ideas from a single zone"""
        selected = []
        dropped = []
        warnings = []

        # First pass: Select excellence ideas (guaranteed)
        excellence_selected = 0
        for idea in prioritized_ideas:
            if id(idea) in excellence_ids and len(selected) < target_quota:
                selected.append(idea)
                excellence_selected += 1
            elif id(idea) in excellence_ids:
                # Excellence idea but quota full - this is a serious warning
                warnings.append(
                    f"Excellence idea '{idea.get('name', 'Unknown')}' in zone '{zone_name}' "
                    f"dropped due to quota constraints. Consider increasing zone quota."
                )
                dropped.append(idea)

        # Second pass: Fill remaining quota with best non-excellence ideas
        remaining_quota = target_quota - len(selected)
        non_excellence_ideas = [
            idea for idea in prioritized_ideas if id(idea) not in excellence_ids
        ]

        for idea in non_excellence_ideas:
            if len(selected) < target_quota:
                scoring = idea.get("scoring", {})

                # Quality gate: Don't select ideas below minimum viable score
                if scoring.get("composite_score", 0) >= self.minimum_viable_score:
                    selected.append(idea)
                else:
                    dropped.append(idea)
                    if scoring.get("is_breakthrough", False):
                        warnings.append(
                            f"Breakthrough idea '{idea.get('name', 'Unknown')}' in zone '{zone_name}' "
                            f"dropped due to low viability score ({scoring.get('composite_score', 0):.1f})"
                        )
            else:
                dropped.append(idea)

                # Warn about high-quality ideas being dropped
                scoring = idea.get("scoring", {})
                if scoring.get("composite_score", 0) >= 7.0:
                    warnings.append(
                        f"High-quality idea '{idea.get('name', 'Unknown')}' in zone '{zone_name}' "
                        f"dropped due to quota limits (score: {scoring.get('composite_score', 0):.1f})"
                    )

        return selected, dropped, warnings

    def _verify_excellence_preservation(
        self,
        selected_ideas: List[Dict[str, Any]],
        excellence_ideas: List[Dict[str, Any]],
    ) -> List[str]:
        """Verify that all excellence ideas were preserved"""
        warnings = []
        selected_ids = {id(idea) for idea in selected_ideas}

        for excellence_idea in excellence_ideas:
            if id(excellence_idea) not in selected_ids:
                warnings.append(
                    f"CRITICAL: Excellence idea '{excellence_idea.get('name', 'Unknown')}' "
                    f"was not preserved in final selection. Review quota allocation."
                )

        return warnings

    def _calculate_average_score(
        self, ideas: List[Dict[str, Any]], score_key: str
    ) -> float:
        """Calculate average score for a list of ideas"""
        scores = []
        for idea in ideas:
            scoring = idea.get("scoring", {})
            if score_key in scoring:
                scores.append(scoring[score_key])
            elif score_key == "composite_score":
                idea_score = scoring.get("idea_score")
                if idea_score:
                    scores.append(idea_score.composite_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_filtering_stats(
        self,
        scored_zones: List[Dict[str, Any]],
        selected_ideas: List[Dict[str, Any]],
        dropped_ideas: List[Dict[str, Any]],
        excellence_ideas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive filtering statistics"""
        total_ideas = sum(len(zone.get("scored_ideas", [])) for zone in scored_zones)

        # Score distributions
        all_ideas = []
        for zone in scored_zones:
            all_ideas.extend(zone.get("scored_ideas", []))

        selected_scores = [
            idea.get("scoring", {}).get("composite_score", 0) for idea in selected_ideas
        ]
        dropped_scores = [
            idea.get("scoring", {}).get("composite_score", 0) for idea in dropped_ideas
        ]

        # Breakthrough preservation
        total_breakthroughs = sum(
            1
            for idea in all_ideas
            if idea.get("scoring", {}).get("is_breakthrough", False)
        )
        selected_breakthroughs = sum(
            1
            for idea in selected_ideas
            if idea.get("scoring", {}).get("is_breakthrough", False)
        )

        # Moonshot preservation
        total_moonshots = sum(
            1 for idea in all_ideas if idea.get("scoring", {}).get("is_moonshot", False)
        )
        selected_moonshots = sum(
            1
            for idea in selected_ideas
            if idea.get("scoring", {}).get("is_moonshot", False)
        )

        return {
            "total_ideas": total_ideas,
            "selected_count": len(selected_ideas),
            "dropped_count": len(dropped_ideas),
            "selection_rate": len(selected_ideas) / total_ideas
            if total_ideas > 0
            else 0,
            "excellence_preservation": {
                "total_excellence": len(excellence_ideas),
                "preserved_excellence": sum(
                    1
                    for idea in selected_ideas
                    if id(idea) in {id(e) for e in excellence_ideas}
                ),
                "preservation_rate": sum(
                    1
                    for idea in selected_ideas
                    if id(idea) in {id(e) for e in excellence_ideas}
                )
                / len(excellence_ideas)
                if excellence_ideas
                else 1.0,
            },
            "breakthrough_preservation": {
                "total_breakthroughs": total_breakthroughs,
                "selected_breakthroughs": selected_breakthroughs,
                "preservation_rate": selected_breakthroughs / total_breakthroughs
                if total_breakthroughs > 0
                else 1.0,
            },
            "moonshot_preservation": {
                "total_moonshots": total_moonshots,
                "selected_moonshots": selected_moonshots,
                "preservation_rate": selected_moonshots / total_moonshots
                if total_moonshots > 0
                else 1.0,
            },
            "score_distributions": {
                "selected_avg_score": sum(selected_scores) / len(selected_scores)
                if selected_scores
                else 0,
                "dropped_avg_score": sum(dropped_scores) / len(dropped_scores)
                if dropped_scores
                else 0,
                "selected_min_score": min(selected_scores) if selected_scores else 0,
                "selected_max_score": max(selected_scores) if selected_scores else 0,
            },
            "zone_analysis": self._generate_zone_analysis(scored_zones, selected_ideas),
        }

    def _generate_zone_analysis(
        self, scored_zones: List[Dict[str, Any]], selected_ideas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate per-zone analysis"""
        zone_analysis = {}

        # Group selected ideas by zone
        selected_by_zone = {}
        for idea in selected_ideas:
            zone_name = idea.get("zone_name", "Unknown")
            if zone_name not in selected_by_zone:
                selected_by_zone[zone_name] = []
            selected_by_zone[zone_name].append(idea)

        for zone_data in scored_zones:
            zone_name = zone_data.get("zone", {}).get("name", "Unknown")
            total_ideas = len(zone_data.get("scored_ideas", []))
            selected_ideas_count = len(selected_by_zone.get(zone_name, []))

            zone_analysis[zone_name] = {
                "total_ideas": total_ideas,
                "selected_ideas": selected_ideas_count,
                "selection_rate": selected_ideas_count / total_ideas
                if total_ideas > 0
                else 0,
                "importance_percentage": zone_data.get("zone", {}).get(
                    "importance_percentage", 0
                ),
            }

        return zone_analysis
