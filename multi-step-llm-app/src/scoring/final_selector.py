"""
Final Selection System with Ensemble Approach
===========================================

Implements multiple selection strategies with safety checks to prevent
dropping excellent ideas and generate warnings for high-value ideas.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import random
from .idea_score import IdeaScore
from .breakthrough_detector import BreakthroughDetector
from .confidence_scorer import ConfidenceScorer
from .smart_filterer import SmartFilterer


@dataclass
class SelectionStrategy:
    """Represents a selection strategy with its results"""

    name: str
    description: str
    selected_ideas: List[Dict[str, Any]]
    selection_rationale: str
    strategy_score: float
    risks: List[str]


@dataclass
class FinalSelectionResults:
    """Results of the final selection process"""

    final_selection: List[Dict[str, Any]]
    ensemble_strategies: List[SelectionStrategy]
    consensus_analysis: Dict[str, Any]
    safety_checks: Dict[str, Any]
    warnings: List[str]
    selection_confidence: float
    dropped_high_value_ideas: List[Dict[str, Any]]


class FinalSelector:
    """
    Advanced final selection system using ensemble approach with multiple
    strategies and comprehensive safety checks
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize final selector"""
        if config is None:
            config = IdeaScore.load_config()

        self.config = config
        self.breakthrough_detector = BreakthroughDetector(config)
        self.confidence_scorer = ConfidenceScorer(config)
        self.smart_filterer = SmartFilterer(config)

        # Selection parameters
        self.min_consensus_threshold = config.get("min_consensus_threshold", 0.6)
        self.safety_preservation_threshold = config.get(
            "safety_preservation_threshold", 8.5
        )
        self.high_value_warning_threshold = config.get(
            "high_value_warning_threshold", 7.5
        )

        # Strategy weights for ensemble
        self.strategy_weights = config.get(
            "strategy_weights",
            {
                "composite_ranking": 0.3,
                "breakthrough_prioritized": 0.25,
                "balanced_portfolio": 0.2,
                "risk_optimized": 0.15,
                "innovation_focused": 0.1,
            },
        )

    def select_final_ideas(
        self, filtered_results, target_count: Optional[int] = None
    ) -> FinalSelectionResults:
        """
        Apply ensemble selection with multiple strategies and safety checks

        Args:
            filtered_results: Results from smart filtering
            target_count: Optional target number of ideas to select

        Returns:
            FinalSelectionResults with comprehensive selection analysis
        """
        selected_ideas = filtered_results.selected_ideas

        if target_count is None:
            target_count = len(selected_ideas)  # Use current selection size

        # Apply multiple selection strategies
        strategies = self._apply_selection_strategies(selected_ideas, target_count)

        # Perform consensus analysis
        consensus_analysis = self._analyze_consensus(strategies)

        # Apply safety checks
        safety_checks = self._apply_safety_checks(selected_ideas, consensus_analysis)

        # Generate final selection using ensemble approach
        final_selection = self._generate_ensemble_selection(
            strategies, consensus_analysis, safety_checks, target_count
        )

        # Identify dropped high-value ideas
        dropped_high_value = self._identify_dropped_high_value_ideas(
            selected_ideas, final_selection
        )

        # Generate warnings
        warnings = self._generate_selection_warnings(
            final_selection, dropped_high_value, safety_checks
        )

        # Calculate selection confidence
        selection_confidence = self._calculate_selection_confidence(
            strategies, consensus_analysis, safety_checks
        )

        return FinalSelectionResults(
            final_selection=final_selection,
            ensemble_strategies=strategies,
            consensus_analysis=consensus_analysis,
            safety_checks=safety_checks,
            warnings=warnings,
            selection_confidence=selection_confidence,
            dropped_high_value_ideas=dropped_high_value,
        )

    def _apply_selection_strategies(
        self, ideas: List[Dict[str, Any]], target_count: int
    ) -> List[SelectionStrategy]:
        """Apply multiple selection strategies"""
        strategies = []

        # Strategy 1: Composite Score Ranking
        composite_strategy = self._composite_ranking_strategy(ideas, target_count)
        strategies.append(composite_strategy)

        # Strategy 2: Breakthrough Prioritized
        breakthrough_strategy = self._breakthrough_prioritized_strategy(
            ideas, target_count
        )
        strategies.append(breakthrough_strategy)

        # Strategy 3: Balanced Portfolio
        balanced_strategy = self._balanced_portfolio_strategy(ideas, target_count)
        strategies.append(balanced_strategy)

        # Strategy 4: Risk Optimized
        risk_strategy = self._risk_optimized_strategy(ideas, target_count)
        strategies.append(risk_strategy)

        # Strategy 5: Innovation Focused
        innovation_strategy = self._innovation_focused_strategy(ideas, target_count)
        strategies.append(innovation_strategy)

        return strategies

    def _composite_ranking_strategy(
        self, ideas: List[Dict[str, Any]], target_count: int
    ) -> SelectionStrategy:
        """Strategy based on composite score ranking"""
        # Sort by composite score
        sorted_ideas = sorted(
            ideas,
            key=lambda x: x.get("scoring", {}).get("composite_score", 0),
            reverse=True,
        )

        selected = sorted_ideas[:target_count]

        avg_score = sum(
            idea.get("scoring", {}).get("composite_score", 0) for idea in selected
        ) / len(selected)

        return SelectionStrategy(
            name="Composite Ranking",
            description="Selection based on highest composite scores",
            selected_ideas=selected,
            selection_rationale=f"Selected top {target_count} ideas by composite score (avg: {avg_score:.2f})",
            strategy_score=avg_score,
            risks=[
                "May miss synergistic opportunities",
                "Could be biased toward conservative ideas",
            ],
        )

    def _breakthrough_prioritized_strategy(
        self, ideas: List[Dict[str, Any]], target_count: int
    ) -> SelectionStrategy:
        """Strategy prioritizing breakthrough potential"""

        # Priority scoring: breakthrough > moonshot > high innovation > composite
        def breakthrough_priority(idea):
            scoring = idea.get("scoring", {})
            breakthrough_analysis = scoring.get("breakthrough_analysis")
            idea_score = scoring.get("idea_score", IdeaScore())

            priority = 0.0

            if breakthrough_analysis and breakthrough_analysis.is_moonshot:
                priority += 1000  # Highest priority
            elif breakthrough_analysis and breakthrough_analysis.is_breakthrough:
                priority += 500
            elif idea_score.innovation_score >= 8.5:
                priority += 200

            # Add composite score as tie-breaker
            priority += scoring.get("composite_score", 0)

            return priority

        sorted_ideas = sorted(ideas, key=breakthrough_priority, reverse=True)
        selected = sorted_ideas[:target_count]

        breakthrough_count = sum(
            1
            for idea in selected
            if idea.get("scoring", {}).get("breakthrough_analysis", {}).is_breakthrough
        )

        return SelectionStrategy(
            name="Breakthrough Prioritized",
            description="Selection prioritizing breakthrough and moonshot ideas",
            selected_ideas=selected,
            selection_rationale=f"Selected {breakthrough_count} breakthrough ideas out of {target_count}",
            strategy_score=breakthrough_count / target_count * 10,
            risks=["May select high-risk ideas", "Could sacrifice near-term viability"],
        )

    def _balanced_portfolio_strategy(
        self, ideas: List[Dict[str, Any]], target_count: int
    ) -> SelectionStrategy:
        """Strategy for balanced portfolio across multiple dimensions"""
        # Categorize ideas
        categories = {
            "high_viability": [],
            "high_innovation": [],
            "breakthrough": [],
            "balanced": [],
        }

        for idea in ideas:
            scoring = idea.get("scoring", {})
            idea_score = scoring.get("idea_score", IdeaScore())
            breakthrough_analysis = scoring.get("breakthrough_analysis")

            if breakthrough_analysis and breakthrough_analysis.is_breakthrough:
                categories["breakthrough"].append(idea)
            elif idea_score.viability_score >= 8.0:
                categories["high_viability"].append(idea)
            elif idea_score.innovation_score >= 8.0:
                categories["high_innovation"].append(idea)
            else:
                categories["balanced"].append(idea)

        # Allocate selections across categories
        selected = []

        # Ensure at least one from each non-empty category
        for category, cat_ideas in categories.items():
            if cat_ideas and len(selected) < target_count:
                best_in_category = max(
                    cat_ideas,
                    key=lambda x: x.get("scoring", {}).get("composite_score", 0),
                )
                selected.append(best_in_category)
                cat_ideas.remove(best_in_category)

        # Fill remaining slots proportionally
        remaining_slots = target_count - len(selected)
        all_remaining = []
        for cat_ideas in categories.values():
            all_remaining.extend(cat_ideas)

        # Sort remaining by composite score
        all_remaining.sort(
            key=lambda x: x.get("scoring", {}).get("composite_score", 0), reverse=True
        )

        selected.extend(all_remaining[:remaining_slots])

        balance_score = (
            len(set(categories.keys())) * 2
        )  # Score based on category diversity

        return SelectionStrategy(
            name="Balanced Portfolio",
            description="Balanced selection across viability, innovation, and breakthrough",
            selected_ideas=selected,
            selection_rationale=f"Balanced selection across {len(categories)} idea categories",
            strategy_score=balance_score,
            risks=[
                "May dilute focus",
                "Could miss opportunity for concentrated excellence",
            ],
        )

    def _risk_optimized_strategy(
        self, ideas: List[Dict[str, Any]], target_count: int
    ) -> SelectionStrategy:
        """Strategy optimized for risk-adjusted returns"""
        # Calculate risk-adjusted scores
        risk_adjusted_ideas = []

        for idea in ideas:
            scoring = idea.get("scoring", {})
            idea_score = scoring.get("idea_score", IdeaScore())

            # Risk adjustment based on confidence and viability
            risk_factor = (
                idea_score.confidence_score + idea_score.viability_score
            ) / 20
            composite_score = scoring.get("composite_score", 0)

            risk_adjusted_score = composite_score * risk_factor

            idea_copy = idea.copy()
            idea_copy["risk_adjusted_score"] = risk_adjusted_score
            risk_adjusted_ideas.append(idea_copy)

        # Sort by risk-adjusted score
        sorted_ideas = sorted(
            risk_adjusted_ideas, key=lambda x: x["risk_adjusted_score"], reverse=True
        )

        selected = sorted_ideas[:target_count]

        avg_risk_score = sum(idea["risk_adjusted_score"] for idea in selected) / len(
            selected
        )

        return SelectionStrategy(
            name="Risk Optimized",
            description="Selection optimized for risk-adjusted returns",
            selected_ideas=selected,
            selection_rationale=f"Selected ideas with highest risk-adjusted scores (avg: {avg_risk_score:.2f})",
            strategy_score=avg_risk_score,
            risks=[
                "May be too conservative",
                "Could miss high-potential breakthrough ideas",
            ],
        )

    def _innovation_focused_strategy(
        self, ideas: List[Dict[str, Any]], target_count: int
    ) -> SelectionStrategy:
        """Strategy focused on innovation potential"""

        # Sort by innovation score with breakthrough bonus
        def innovation_priority(idea):
            scoring = idea.get("scoring", {})
            idea_score = scoring.get("idea_score", IdeaScore())
            breakthrough_analysis = scoring.get("breakthrough_analysis")

            priority = idea_score.innovation_score

            # Breakthrough bonus
            if breakthrough_analysis:
                if breakthrough_analysis.is_moonshot:
                    priority += 3.0
                elif breakthrough_analysis.is_breakthrough:
                    priority += 2.0

            return priority

        sorted_ideas = sorted(ideas, key=innovation_priority, reverse=True)
        selected = sorted_ideas[:target_count]

        avg_innovation = sum(
            idea.get("scoring", {}).get("idea_score", IdeaScore()).innovation_score
            for idea in selected
        ) / len(selected)

        return SelectionStrategy(
            name="Innovation Focused",
            description="Selection prioritizing innovation and breakthrough potential",
            selected_ideas=selected,
            selection_rationale=f"Selected highest innovation ideas (avg innovation: {avg_innovation:.2f})",
            strategy_score=avg_innovation,
            risks=[
                "High technical risk",
                "May lack market viability",
                "Extended development timelines",
            ],
        )

    def _analyze_consensus(self, strategies: List[SelectionStrategy]) -> Dict[str, Any]:
        """Analyze consensus across different strategies"""
        # Count how many strategies selected each idea
        idea_votes = {}

        for strategy in strategies:
            for idea in strategy.selected_ideas:
                idea_id = id(idea)
                if idea_id not in idea_votes:
                    idea_votes[idea_id] = {"idea": idea, "votes": 0, "strategies": []}
                idea_votes[idea_id]["votes"] += 1
                idea_votes[idea_id]["strategies"].append(strategy.name)

        # Categorize ideas by consensus level
        total_strategies = len(strategies)
        consensus_categories = {
            "strong_consensus": [],  # Selected by 80%+ strategies
            "moderate_consensus": [],  # Selected by 60-79% strategies
            "weak_consensus": [],  # Selected by 40-59% strategies
            "no_consensus": [],  # Selected by <40% strategies
        }

        for idea_data in idea_votes.values():
            vote_ratio = idea_data["votes"] / total_strategies

            if vote_ratio >= 0.8:
                consensus_categories["strong_consensus"].append(idea_data)
            elif vote_ratio >= 0.6:
                consensus_categories["moderate_consensus"].append(idea_data)
            elif vote_ratio >= 0.4:
                consensus_categories["weak_consensus"].append(idea_data)
            else:
                consensus_categories["no_consensus"].append(idea_data)

        return {
            "consensus_categories": consensus_categories,
            "total_unique_ideas": len(idea_votes),
            "consensus_strength": len(consensus_categories["strong_consensus"])
            / len(idea_votes)
            if idea_votes
            else 0,
        }

    def _apply_safety_checks(
        self, original_ideas: List[Dict[str, Any]], consensus_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply safety checks to prevent dropping excellent ideas"""
        safety_results = {
            "must_preserve_ideas": [],
            "safety_violations": [],
            "preservation_overrides": [],
        }

        # Identify must-preserve ideas
        for idea in original_ideas:
            scoring = idea.get("scoring", {})
            composite_score = scoring.get("composite_score", 0)
            breakthrough_analysis = scoring.get("breakthrough_analysis")

            # Safety criteria
            must_preserve = False
            preservation_reasons = []

            # High composite score
            if composite_score >= self.safety_preservation_threshold:
                must_preserve = True
                preservation_reasons.append(
                    f"High composite score ({composite_score:.2f})"
                )

            # Moonshot ideas
            if breakthrough_analysis and breakthrough_analysis.is_moonshot:
                must_preserve = True
                preservation_reasons.append("Moonshot potential")

            # Exceptional innovation with reasonable viability
            idea_score = scoring.get("idea_score", IdeaScore())
            if idea_score.innovation_score >= 9.0 and idea_score.viability_score >= 6.0:
                must_preserve = True
                preservation_reasons.append("Exceptional innovation with viability")

            if must_preserve:
                safety_results["must_preserve_ideas"].append(
                    {"idea": idea, "reasons": preservation_reasons}
                )

        # Check if must-preserve ideas are in consensus
        consensus_ideas = set()
        for category in consensus_analysis["consensus_categories"].values():
            for item in category:
                consensus_ideas.add(id(item["idea"]))

        for preserve_item in safety_results["must_preserve_ideas"]:
            if id(preserve_item["idea"]) not in consensus_ideas:
                safety_results["safety_violations"].append(
                    {
                        "idea": preserve_item["idea"],
                        "violation": "Must-preserve idea not in consensus selection",
                        "reasons": preserve_item["reasons"],
                    }
                )

        return safety_results

    def _generate_ensemble_selection(
        self,
        strategies: List[SelectionStrategy],
        consensus_analysis: Dict[str, Any],
        safety_checks: Dict[str, Any],
        target_count: int,
    ) -> List[Dict[str, Any]]:
        """Generate final selection using ensemble approach"""
        final_selection = []

        # Step 1: Add all must-preserve ideas
        for preserve_item in safety_checks["must_preserve_ideas"]:
            if len(final_selection) < target_count:
                final_selection.append(preserve_item["idea"])

        # Step 2: Add strong consensus ideas
        consensus_cats = consensus_analysis["consensus_categories"]
        for item in consensus_cats.get("strong_consensus", []):
            if len(final_selection) < target_count and id(item["idea"]) not in {
                id(idea) for idea in final_selection
            }:
                final_selection.append(item["idea"])

        # Step 3: Add moderate consensus ideas
        for item in consensus_cats.get("moderate_consensus", []):
            if len(final_selection) < target_count and id(item["idea"]) not in {
                id(idea) for idea in final_selection
            }:
                final_selection.append(item["idea"])

        # Step 4: Fill remaining slots with weighted strategy selection
        if len(final_selection) < target_count:
            remaining_slots = target_count - len(final_selection)
            selected_ids = {id(idea) for idea in final_selection}

            # Collect all remaining candidates with weighted scores
            candidates = []

            for strategy in strategies:
                strategy_weight = self.strategy_weights.get(
                    strategy.name.lower().replace(" ", "_"), 0.1
                )

                for idea in strategy.selected_ideas:
                    if id(idea) not in selected_ids:
                        composite_score = idea.get("scoring", {}).get(
                            "composite_score", 0
                        )
                        weighted_score = composite_score * strategy_weight

                        candidates.append(
                            {
                                "idea": idea,
                                "weighted_score": weighted_score,
                                "strategy": strategy.name,
                            }
                        )

            # Sort by weighted score and select top candidates
            candidates.sort(key=lambda x: x["weighted_score"], reverse=True)

            for candidate in candidates[:remaining_slots]:
                final_selection.append(candidate["idea"])

        return final_selection[:target_count]

    def _identify_dropped_high_value_ideas(
        self,
        original_ideas: List[Dict[str, Any]],
        final_selection: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify high-value ideas that were dropped"""
        final_ids = {id(idea) for idea in final_selection}
        dropped_high_value = []

        for idea in original_ideas:
            if id(idea) not in final_ids:
                scoring = idea.get("scoring", {})
                composite_score = scoring.get("composite_score", 0)
                breakthrough_analysis = scoring.get("breakthrough_analysis")

                # Check if it's high value
                if composite_score >= self.high_value_warning_threshold or (
                    breakthrough_analysis and breakthrough_analysis.is_breakthrough
                ):
                    dropped_high_value.append(
                        {
                            "idea": idea,
                            "composite_score": composite_score,
                            "drop_reason": self._determine_drop_reason(idea, scoring),
                        }
                    )

        return dropped_high_value

    def _determine_drop_reason(
        self, idea: Dict[str, Any], scoring: Dict[str, Any]
    ) -> str:
        """Determine why a high-value idea was dropped"""
        idea_score = scoring.get("idea_score", IdeaScore())

        if idea_score.confidence_score < 5.0:
            return "Low confidence in assessment"
        elif idea_score.viability_score < 4.0:
            return "Low viability score"
        elif idea_score.get_risk_level() == "Very High Risk":
            return "Very high risk level"
        else:
            return "Dropped due to portfolio optimization constraints"

    def _generate_selection_warnings(
        self,
        final_selection: List[Dict[str, Any]],
        dropped_high_value: List[Dict[str, Any]],
        safety_checks: Dict[str, Any],
    ) -> List[str]:
        """Generate warnings about the selection"""
        warnings = []

        # Safety violation warnings
        for violation in safety_checks["safety_violations"]:
            warnings.append(
                f"CRITICAL: Must-preserve idea '{violation['idea'].get('name', 'Unknown')}' "
                f"was dropped despite meeting safety criteria: {', '.join(violation['reasons'])}"
            )

        # High-value drop warnings
        for dropped in dropped_high_value:
            idea_name = dropped["idea"].get("name", "Unknown")
            score = dropped["composite_score"]
            reason = dropped["drop_reason"]

            warnings.append(
                f"WARNING: High-value idea '{idea_name}' (score: {score:.2f}) "
                f"was dropped due to: {reason}"
            )

        # Portfolio balance warnings
        innovation_scores = [
            idea.get("scoring", {}).get("idea_score", IdeaScore()).innovation_score
            for idea in final_selection
        ]

        if innovation_scores:
            avg_innovation = sum(innovation_scores) / len(innovation_scores)
            if avg_innovation < 6.0:
                warnings.append(
                    f"PORTFOLIO WARNING: Low average innovation score ({avg_innovation:.2f}) "
                    f"in final selection may limit breakthrough potential"
                )

        # Breakthrough preservation warning
        breakthrough_count = sum(
            1
            for idea in final_selection
            if idea.get("scoring", {}).get("breakthrough_analysis", {}).is_breakthrough
        )

        if breakthrough_count == 0:
            warnings.append(
                "PORTFOLIO WARNING: No breakthrough ideas in final selection. "
                "Consider including at least one breakthrough idea for innovation balance."
            )

        return warnings

    def _calculate_selection_confidence(
        self,
        strategies: List[SelectionStrategy],
        consensus_analysis: Dict[str, Any],
        safety_checks: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the final selection"""
        confidence_factors = []

        # Consensus strength
        consensus_strength = consensus_analysis.get("consensus_strength", 0)
        confidence_factors.append(consensus_strength * 10)

        # Strategy agreement (average strategy scores)
        avg_strategy_score = sum(s.strategy_score for s in strategies) / len(strategies)
        confidence_factors.append(avg_strategy_score)

        # Safety compliance
        must_preserve_count = len(safety_checks["must_preserve_ideas"])
        violations_count = len(safety_checks["safety_violations"])

        if must_preserve_count > 0:
            safety_compliance = 1 - (violations_count / must_preserve_count)
        else:
            safety_compliance = 1.0

        confidence_factors.append(safety_compliance * 10)

        # Strategy diversity (higher diversity = more robust selection)
        strategy_variance = self._calculate_strategy_score_variance(strategies)
        diversity_score = min(
            10.0, strategy_variance * 2
        )  # Higher variance = more diverse
        confidence_factors.append(diversity_score)

        # Calculate weighted average
        weights = [0.3, 0.25, 0.3, 0.15]
        confidence = sum(
            score * weight for score, weight in zip(confidence_factors, weights)
        )

        return round(min(10.0, max(0.0, confidence)), 2)

    def _calculate_strategy_score_variance(
        self, strategies: List[SelectionStrategy]
    ) -> float:
        """Calculate variance in strategy scores"""
        scores = [s.strategy_score for s in strategies]

        if len(scores) <= 1:
            return 0.0

        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)

        return variance**0.5  # Return standard deviation
