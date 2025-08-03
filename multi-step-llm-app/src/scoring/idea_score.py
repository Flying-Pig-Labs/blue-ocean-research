"""
Multi-Dimensional Idea Scoring Framework
=======================================

Implements comprehensive scoring for product ideas with weighted composite scores
and detailed sub-dimension analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import yaml
import os
from pathlib import Path


@dataclass
class IdeaScore:
    """
    Multi-dimensional scoring framework for product ideas
    
    Attributes:
        viability_score: Technical and market feasibility (0-10)
        innovation_score: Degree of innovation and novelty (0-10)  
        breakthrough_score: Potential for game-changing impact (0-10)
        confidence_score: Certainty in assessment (0-10)
        composite_score: Weighted overall score (0-10)
        raw_scores: Original unprocessed scores
        metadata: Additional scoring context
    """
    
    viability_score: float = 0.0
    innovation_score: float = 0.0
    breakthrough_score: float = 0.0
    confidence_score: float = 0.0
    composite_score: float = 0.0
    
    # Detailed sub-scores
    raw_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Sub-dimension breakdowns
    viability_breakdown: Dict[str, float] = field(default_factory=dict)
    innovation_breakdown: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load scoring configuration from YAML file"""
        if config_path is None:
            # Look for scoring_config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "scoring_config.yaml"
        
        if not os.path.exists(config_path):
            # Return default configuration
            return cls._get_default_config()
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """Default scoring configuration"""
        return {
            'weights': {
                'viability': 0.35,
                'innovation': 0.25, 
                'breakthrough': 0.25,
                'confidence': 0.15
            },
            'viability_factors': {
                'technical_feasibility': 0.30,
                'market_readiness': 0.25,
                'resource_requirements': 0.20,
                'time_to_market': 0.15,
                'competitive_moat': 0.10
            },
            'innovation_factors': {
                'novelty': 0.40,
                'uniqueness': 0.30,
                'disruption_potential': 0.20,
                'technology_advancement': 0.10
            },
            'breakthrough_thresholds': {
                'moonshot_threshold': 8.5,
                'game_changer_threshold': 7.5,
                'incremental_threshold': 5.0
            }
        }
    
    @classmethod
    def from_idea_data(cls, idea: Dict[str, Any], config: Optional[Dict] = None) -> 'IdeaScore':
        """Create IdeaScore from idea dictionary"""
        if config is None:
            config = cls.load_config()
        
        # Extract existing scores
        viability = idea.get('viability_score', 5.0)
        innovation = idea.get('innovation_score', 5.0)
        
        # Calculate breakthrough score if not provided
        breakthrough = idea.get('breakthrough_score')
        if breakthrough is None:
            breakthrough = cls._calculate_breakthrough_score(idea, config)
        
        # Calculate confidence score
        confidence = cls._calculate_confidence_score(idea, config)
        
        # Parse viability breakdown
        viability_breakdown = cls._parse_viability_breakdown(idea)
        
        # Parse innovation breakdown  
        innovation_breakdown = cls._parse_innovation_breakdown(idea)
        
        # Calculate composite score
        composite = cls._calculate_composite_score(
            viability, innovation, breakthrough, confidence, config
        )
        
        return cls(
            viability_score=viability,
            innovation_score=innovation,
            breakthrough_score=breakthrough,
            confidence_score=confidence,
            composite_score=composite,
            raw_scores={
                'original_viability': idea.get('viability_score', 5.0),
                'original_innovation': idea.get('innovation_score', 5.0),
                'calculated_breakthrough': breakthrough,
                'calculated_confidence': confidence
            },
            viability_breakdown=viability_breakdown,
            innovation_breakdown=innovation_breakdown,
            metadata={
                'idea_name': idea.get('name', 'Unknown'),
                'zone_name': idea.get('zone_name', 'Unknown'),
                'scoring_timestamp': cls._get_timestamp()
            }
        )
    
    @staticmethod
    def _calculate_breakthrough_score(idea: Dict[str, Any], config: Dict) -> float:
        """Calculate breakthrough potential score"""
        # Use innovation score as base
        innovation_base = idea.get('innovation_score', 5.0)
        
        # Look for breakthrough indicators in text
        value_prop = idea.get('value_proposition', '').lower()
        features = str(idea.get('features', [])).lower()
        differentiation = idea.get('differentiation', '').lower()
        
        all_text = f"{value_prop} {features} {differentiation}"
        
        # Breakthrough keywords and their weights
        breakthrough_keywords = {
            'revolutionary': 2.0,
            'paradigm shift': 2.0,
            'breakthrough': 1.8,
            'disruptive': 1.5,
            'game changer': 1.5,
            'first-ever': 1.3,
            'unprecedented': 1.3,
            'innovative': 1.0,
            'novel': 1.0,
            'unique': 0.8,
            'advanced': 0.5
        }
        
        # Calculate keyword boost
        keyword_boost = 0.0
        for keyword, weight in breakthrough_keywords.items():
            if keyword in all_text:
                keyword_boost += weight
        
        # Apply diminishing returns to keyword boost
        keyword_boost = min(keyword_boost, 3.0)
        
        # Combine with innovation score
        breakthrough_score = min(10.0, innovation_base + keyword_boost)
        
        return round(breakthrough_score, 2)
    
    @staticmethod
    def _calculate_confidence_score(idea: Dict[str, Any], config: Dict) -> float:
        """Calculate confidence in the scoring assessment"""
        confidence_factors = []
        
        # Factor 1: Completeness of data
        required_fields = ['name', 'value_proposition', 'viability_score', 'innovation_score']
        completeness = sum(1 for field in required_fields if idea.get(field)) / len(required_fields)
        confidence_factors.append(completeness * 10)
        
        # Factor 2: Detail level in descriptions
        text_fields = ['value_proposition', 'features', 'differentiation']
        avg_length = sum(len(str(idea.get(field, ''))) for field in text_fields) / len(text_fields)
        detail_score = min(10.0, avg_length / 20)  # 200 chars = full score
        confidence_factors.append(detail_score)
        
        # Factor 3: Consistency check
        viability = idea.get('viability_score', 5.0)
        innovation = idea.get('innovation_score', 5.0)
        
        # High innovation + low viability should reduce confidence
        if innovation > 8 and viability < 4:
            consistency_penalty = 2.0
        elif abs(innovation - viability) > 4:
            consistency_penalty = 1.0
        else:
            consistency_penalty = 0.0
        
        consistency_score = max(1.0, 8.0 - consistency_penalty)
        confidence_factors.append(consistency_score)
        
        # Factor 4: Viability detail availability
        viability_details = idea.get('viability_details', {})
        if isinstance(viability_details, dict) and len(viability_details) > 3:
            detail_confidence = 9.0
        elif viability_details:
            detail_confidence = 6.0
        else:
            detail_confidence = 4.0
        confidence_factors.append(detail_confidence)
        
        # Calculate weighted average
        weights = [0.3, 0.2, 0.3, 0.2]
        confidence = sum(score * weight for score, weight in zip(confidence_factors, weights))
        
        return round(min(10.0, max(1.0, confidence)), 2)
    
    @staticmethod
    def _parse_viability_breakdown(idea: Dict[str, Any]) -> Dict[str, float]:
        """Parse viability sub-scores from idea data"""
        viability_details = idea.get('viability_details', {})
        
        if isinstance(viability_details, dict):
            breakdown = {}
            # Map common field names
            field_mapping = {
                'technical_feasibility': ['technical_feasibility', 'tech_feasibility', 'technical'],
                'market_readiness': ['market_readiness', 'market_ready', 'market'],
                'resource_requirements': ['resource_requirements', 'resources', 'resource_needs'],
                'time_to_market': ['time_to_market', 'time_market', 'development_time'],
                'competitive_moat': ['competitive_moat', 'moat', 'defensibility']
            }
            
            for standard_name, possible_names in field_mapping.items():
                for name in possible_names:
                    if name in viability_details:
                        breakdown[standard_name] = float(viability_details[name])
                        break
                else:
                    # Default score if not found
                    breakdown[standard_name] = 5.0
            
            return breakdown
        
        # Return default breakdown
        return {
            'technical_feasibility': 5.0,
            'market_readiness': 5.0,
            'resource_requirements': 5.0,
            'time_to_market': 5.0,
            'competitive_moat': 5.0
        }
    
    @staticmethod
    def _parse_innovation_breakdown(idea: Dict[str, Any]) -> Dict[str, float]:
        """Parse innovation sub-scores from idea data"""
        # Calculate innovation breakdown from available data
        innovation_score = idea.get('innovation_score', 5.0)
        
        # Estimate sub-components based on text analysis
        value_prop = idea.get('value_proposition', '').lower()
        features = str(idea.get('features', [])).lower()
        
        # Novelty score
        novelty_keywords = ['new', 'first', 'novel', 'never before', 'unprecedented']
        novelty_boost = sum(1 for keyword in novelty_keywords if keyword in value_prop) * 0.5
        novelty_score = min(10.0, innovation_score + novelty_boost)
        
        # Uniqueness score  
        unique_keywords = ['unique', 'exclusive', 'proprietary', 'patented', 'distinctive']
        unique_boost = sum(1 for keyword in unique_keywords if keyword in value_prop) * 0.5
        uniqueness_score = min(10.0, innovation_score + unique_boost)
        
        # Disruption potential
        disrupt_keywords = ['disrupt', 'transform', 'revolutionize', 'paradigm', 'breakthrough']
        disrupt_boost = sum(1 for keyword in disrupt_keywords if keyword in value_prop) * 0.7
        disruption_score = min(10.0, innovation_score + disrupt_boost)
        
        # Technology advancement
        tech_keywords = ['ai', 'machine learning', 'blockchain', 'quantum', 'advanced algorithm']
        tech_boost = sum(1 for keyword in tech_keywords if keyword in features) * 0.8
        tech_score = min(10.0, innovation_score + tech_boost)
        
        return {
            'novelty': round(novelty_score, 1),
            'uniqueness': round(uniqueness_score, 1),
            'disruption_potential': round(disruption_score, 1),
            'technology_advancement': round(tech_score, 1)
        }
    
    @staticmethod
    def _calculate_composite_score(viability: float, innovation: float, 
                                 breakthrough: float, confidence: float, 
                                 config: Dict) -> float:
        """Calculate weighted composite score"""
        weights = config.get('weights', {})
        
        # Get weights with defaults
        w_viability = weights.get('viability', 0.35)
        w_innovation = weights.get('innovation', 0.25) 
        w_breakthrough = weights.get('breakthrough', 0.25)
        w_confidence = weights.get('confidence', 0.15)
        
        # Calculate weighted score
        composite = (
            viability * w_viability +
            innovation * w_innovation +
            breakthrough * w_breakthrough +
            confidence * w_confidence
        )
        
        return round(composite, 2)
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp for metadata"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'viability_score': self.viability_score,
            'innovation_score': self.innovation_score,
            'breakthrough_score': self.breakthrough_score,
            'confidence_score': self.confidence_score,
            'composite_score': self.composite_score,
            'raw_scores': self.raw_scores,
            'viability_breakdown': self.viability_breakdown,
            'innovation_breakdown': self.innovation_breakdown,
            'metadata': self.metadata
        }
    
    def is_high_potential(self, config: Optional[Dict] = None) -> bool:
        """Check if idea meets high potential criteria"""
        if config is None:
            config = self.load_config()
        
        thresholds = config.get('breakthrough_thresholds', {})
        game_changer_threshold = thresholds.get('game_changer_threshold', 7.5)
        
        return (
            self.composite_score >= game_changer_threshold or
            self.breakthrough_score >= game_changer_threshold or
            (self.innovation_score >= 8.0 and self.viability_score >= 6.0)
        )
    
    def is_moonshot(self, config: Optional[Dict] = None) -> bool:
        """Check if idea qualifies as moonshot"""
        if config is None:
            config = self.load_config()
        
        thresholds = config.get('breakthrough_thresholds', {})
        moonshot_threshold = thresholds.get('moonshot_threshold', 8.5)
        
        return (
            self.breakthrough_score >= moonshot_threshold or
            (self.innovation_score >= 9.0 and self.composite_score >= 8.0)
        )
    
    def get_risk_level(self) -> str:
        """Determine risk level based on scores"""
        if self.viability_score >= 8.0 and self.confidence_score >= 8.0:
            return "Low Risk"
        elif self.viability_score >= 6.0 and self.confidence_score >= 6.0:
            return "Medium Risk"
        elif self.viability_score >= 4.0:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def __str__(self) -> str:
        """String representation"""
        return (
            f"IdeaScore(composite={self.composite_score}, "
            f"viability={self.viability_score}, "
            f"innovation={self.innovation_score}, "
            f"breakthrough={self.breakthrough_score}, "
            f"confidence={self.confidence_score})"
        )