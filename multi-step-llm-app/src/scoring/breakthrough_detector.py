"""
Breakthrough Idea Detection System
================================

Identifies breakthrough potential, moonshot opportunities, and game-changing ideas
with cross-industry versatility analysis.
"""

from typing import Dict, List, Any, Tuple, Optional
import re
from dataclasses import dataclass
from .idea_score import IdeaScore


@dataclass
class BreakthroughAnalysis:
    """Results of breakthrough detection analysis"""
    is_breakthrough: bool
    is_moonshot: bool
    is_game_changer: bool
    breakthrough_score: float
    moonshot_indicators: List[str]
    scalability_score: float
    versatility_score: float
    risk_factors: List[str]
    opportunity_factors: List[str]
    industry_disruption_potential: Dict[str, float]


class BreakthroughDetector:
    """
    Advanced breakthrough detection system for identifying 
    game-changing and moonshot product ideas
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize breakthrough detector with configuration"""
        if config is None:
            config = IdeaScore.load_config()
        
        self.config = config
        self.breakthrough_thresholds = config.get('breakthrough_thresholds', {})
        
        # Breakthrough keyword patterns
        self.moonshot_patterns = [
            r'\b(revolutionary|paradigm\s+shift|game\s*chang\w+|breakthrough)\b',
            r'\b(unprecedented|never\s+before|first\s+ever|groundbreaking)\b',
            r'\b(transform\w*|disrupt\w*|revolutioniz\w+)\b',
            r'\b(next\s+generation|quantum\s+leap|cutting\s+edge)\b'
        ]
        
        self.scalability_indicators = [
            r'\b(platform|ecosystem|network\s+effect|viral)\b',
            r'\b(scalable|global|worldwide|massive\s+market)\b',
            r'\b(automated|self\-learning|adaptive)\b',
            r'\b(cloud|distributed|decentralized)\b'
        ]
        
        self.versatility_indicators = [
            r'\b(cross\-industry|multi\-sector|universal)\b',
            r'\b(adaptable|flexible|configurable|modular)\b',
            r'\b(api|integration|interoperab\w+)\b',
            r'\b(general\s+purpose|broad\s+application)\b'
        ]
        
        # Industry sectors for cross-industry analysis
        self.industry_sectors = [
            'healthcare', 'finance', 'education', 'retail', 'manufacturing',
            'transportation', 'energy', 'entertainment', 'agriculture', 'real_estate',
            'logistics', 'telecommunications', 'government', 'construction', 'insurance'
        ]
    
    def analyze_idea(self, idea: Dict[str, Any], idea_score: Optional[IdeaScore] = None) -> BreakthroughAnalysis:
        """
        Comprehensive breakthrough analysis of a product idea
        
        Args:
            idea: Product idea dictionary
            idea_score: Optional pre-calculated IdeaScore
            
        Returns:
            BreakthroughAnalysis with detailed assessment
        """
        if idea_score is None:
            idea_score = IdeaScore.from_idea_data(idea, self.config)
        
        # Extract text for analysis
        idea_text = self._extract_idea_text(idea)
        
        # Detect moonshot indicators
        moonshot_indicators = self._detect_moonshot_indicators(idea_text)
        
        # Calculate breakthrough metrics
        breakthrough_score = self._calculate_breakthrough_score(idea, idea_score, moonshot_indicators)
        scalability_score = self._assess_scalability(idea_text)
        versatility_score = self._assess_cross_industry_versatility(idea_text)
        
        # Determine breakthrough categories
        is_moonshot = self._is_moonshot(breakthrough_score, moonshot_indicators, idea_score)
        is_game_changer = self._is_game_changer(breakthrough_score, scalability_score, idea_score)
        is_breakthrough = is_moonshot or is_game_changer or breakthrough_score >= 7.5
        
        # Risk and opportunity analysis
        risk_factors = self._identify_risk_factors(idea, idea_score)
        opportunity_factors = self._identify_opportunity_factors(idea, idea_score, moonshot_indicators)
        
        # Industry disruption potential
        industry_disruption = self._assess_industry_disruption_potential(idea_text, breakthrough_score)
        
        return BreakthroughAnalysis(
            is_breakthrough=is_breakthrough,
            is_moonshot=is_moonshot,
            is_game_changer=is_game_changer,
            breakthrough_score=breakthrough_score,
            moonshot_indicators=moonshot_indicators,
            scalability_score=scalability_score,
            versatility_score=versatility_score,
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            industry_disruption_potential=industry_disruption
        )
    
    def _extract_idea_text(self, idea: Dict[str, Any]) -> str:
        """Extract all text content from idea for analysis"""
        text_fields = [
            'name', 'value_proposition', 'features', 'differentiation',
            'target_segment', 'description'
        ]
        
        text_parts = []
        for field in text_fields:
            value = idea.get(field, '')
            if isinstance(value, list):
                text_parts.extend(str(item) for item in value)
            elif value:
                text_parts.append(str(value))
        
        return ' '.join(text_parts).lower()
    
    def _detect_moonshot_indicators(self, text: str) -> List[str]:
        """Detect moonshot indicators in idea text"""
        indicators = []
        
        for pattern in self.moonshot_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    indicators.extend([m for m in match if m])
                else:
                    indicators.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_indicators = []
        for indicator in indicators:
            if indicator.lower() not in seen:
                seen.add(indicator.lower())
                unique_indicators.append(indicator)
        
        return unique_indicators
    
    def _calculate_breakthrough_score(self, idea: Dict[str, Any], 
                                    idea_score: IdeaScore, 
                                    moonshot_indicators: List[str]) -> float:
        """Calculate comprehensive breakthrough score"""
        # Base score from IdeaScore
        base_score = idea_score.breakthrough_score
        
        # Moonshot indicator boost
        indicator_boost = min(2.0, len(moonshot_indicators) * 0.5)
        
        # Innovation and viability combination boost
        innovation = idea_score.innovation_score
        viability = idea_score.viability_score
        
        # High innovation + reasonable viability = breakthrough potential
        if innovation >= 8.0 and viability >= 5.0:
            combo_boost = 1.0
        elif innovation >= 7.0 and viability >= 6.0:
            combo_boost = 0.5
        else:
            combo_boost = 0.0
        
        # Technical advancement boost
        tech_boost = self._assess_technical_advancement(idea)
        
        # Market size potential boost
        market_boost = self._assess_market_size_potential(idea)
        
        # Combine all factors
        breakthrough_score = min(10.0, base_score + indicator_boost + combo_boost + tech_boost + market_boost)
        
        return round(breakthrough_score, 2)
    
    def _assess_technical_advancement(self, idea: Dict[str, Any]) -> float:
        """Assess technical advancement level"""
        idea_text = self._extract_idea_text(idea)
        
        advanced_tech_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'quantum computing', 'blockchain', 'nanotechnology',
            'biotechnology', 'genetic engineering', 'neural networks',
            'computer vision', 'natural language processing', 'robotics',
            'augmented reality', 'virtual reality', 'iot', 'edge computing'
        ]
        
        tech_score = 0.0
        for keyword in advanced_tech_keywords:
            if keyword in idea_text:
                tech_score += 0.3
        
        return min(1.5, tech_score)
    
    def _assess_market_size_potential(self, idea: Dict[str, Any]) -> float:
        """Assess market size and growth potential"""
        idea_text = self._extract_idea_text(idea)
        target_segment = idea.get('target_segment', '').lower()
        
        large_market_indicators = [
            'global', 'worldwide', 'international', 'billions',
            'mass market', 'consumer', 'enterprise', 'b2b',
            'growing market', 'expanding', 'emerging market'
        ]
        
        market_score = 0.0
        for indicator in large_market_indicators:
            if indicator in idea_text or indicator in target_segment:
                market_score += 0.2
        
        return min(1.0, market_score)
    
    def _assess_scalability(self, text: str) -> float:
        """Assess scalability potential of the idea"""
        scalability_score = 0.0
        
        for pattern in self.scalability_indicators:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            scalability_score += matches * 0.5
        
        # Additional scalability factors
        if 'software' in text or 'digital' in text or 'app' in text:
            scalability_score += 1.0
        
        if 'hardware' in text or 'manufacturing' in text:
            scalability_score -= 0.5  # Harder to scale
        
        if 'network' in text or 'community' in text:
            scalability_score += 0.5  # Network effects
        
        return min(10.0, max(0.0, scalability_score))
    
    def _assess_cross_industry_versatility(self, text: str) -> float:
        """Assess cross-industry application potential"""
        versatility_score = 0.0
        
        for pattern in self.versatility_indicators:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            versatility_score += matches * 0.5
        
        # Check for industry-specific mentions
        industry_mentions = 0
        for sector in self.industry_sectors:
            if sector in text:
                industry_mentions += 1
        
        # Multiple industry mentions suggest versatility
        if industry_mentions >= 3:
            versatility_score += 2.0
        elif industry_mentions >= 2:
            versatility_score += 1.0
        
        return min(10.0, max(0.0, versatility_score))
    
    def _is_moonshot(self, breakthrough_score: float, 
                    moonshot_indicators: List[str], 
                    idea_score: IdeaScore) -> bool:
        """Determine if idea qualifies as moonshot"""
        moonshot_threshold = self.breakthrough_thresholds.get('moonshot_threshold', 8.5)
        
        return (
            breakthrough_score >= moonshot_threshold or
            len(moonshot_indicators) >= 3 or
            (idea_score.innovation_score >= 9.0 and breakthrough_score >= 8.0) or
            idea_score.is_moonshot(self.config)
        )
    
    def _is_game_changer(self, breakthrough_score: float, 
                        scalability_score: float, 
                        idea_score: IdeaScore) -> bool:
        """Determine if idea qualifies as game changer"""
        game_changer_threshold = self.breakthrough_thresholds.get('game_changer_threshold', 7.5)
        
        return (
            breakthrough_score >= game_changer_threshold or
            (scalability_score >= 7.0 and idea_score.innovation_score >= 8.0) or
            (idea_score.composite_score >= 8.0 and breakthrough_score >= 7.0)
        )
    
    def _identify_risk_factors(self, idea: Dict[str, Any], idea_score: IdeaScore) -> List[str]:
        """Identify key risk factors for the idea"""
        risks = []
        
        # Technical risks
        if idea_score.viability_breakdown.get('technical_feasibility', 5.0) < 6.0:
            risks.append("Technical feasibility concerns")
        
        # Market risks
        if idea_score.viability_breakdown.get('market_readiness', 5.0) < 6.0:
            risks.append("Market readiness uncertainty")
        
        # Resource risks
        if idea_score.viability_breakdown.get('resource_requirements', 5.0) < 5.0:
            risks.append("High resource requirements")
        
        # Time risks
        if idea_score.viability_breakdown.get('time_to_market', 5.0) < 5.0:
            risks.append("Extended development timeline")
        
        # Competitive risks
        if idea_score.viability_breakdown.get('competitive_moat', 5.0) < 6.0:
            risks.append("Limited competitive protection")
        
        # Confidence risks
        if idea_score.confidence_score < 6.0:
            risks.append("Assessment uncertainty")
        
        # Innovation vs viability mismatch
        if idea_score.innovation_score > 8.0 and idea_score.viability_score < 5.0:
            risks.append("High innovation with low viability")
        
        return risks
    
    def _identify_opportunity_factors(self, idea: Dict[str, Any], 
                                    idea_score: IdeaScore, 
                                    moonshot_indicators: List[str]) -> List[str]:
        """Identify key opportunity factors for the idea"""
        opportunities = []
        
        # Innovation opportunities
        if idea_score.innovation_score >= 8.0:
            opportunities.append("High innovation potential")
        
        # Breakthrough opportunities
        if moonshot_indicators:
            opportunities.append(f"Breakthrough indicators: {', '.join(moonshot_indicators[:3])}")
        
        # Market opportunities
        if idea_score.viability_breakdown.get('market_readiness', 5.0) >= 7.0:
            opportunities.append("Strong market readiness")
        
        # Competitive opportunities
        if idea_score.viability_breakdown.get('competitive_moat', 5.0) >= 7.0:
            opportunities.append("Strong competitive protection")
        
        # Technical opportunities
        if idea_score.viability_breakdown.get('technical_feasibility', 5.0) >= 8.0:
            opportunities.append("High technical feasibility")
        
        # Scalability opportunities
        idea_text = self._extract_idea_text(idea)
        if any(indicator in idea_text for indicator in ['platform', 'ecosystem', 'network']):
            opportunities.append("Platform/ecosystem potential")
        
        return opportunities
    
    def _assess_industry_disruption_potential(self, text: str, breakthrough_score: float) -> Dict[str, float]:
        """Assess disruption potential across different industries"""
        industry_disruption = {}
        
        for sector in self.industry_sectors:
            base_score = breakthrough_score * 0.6  # Base disruption potential
            
            # Sector-specific mentions boost score
            if sector in text:
                base_score += 2.0
            
            # Related terms boost
            sector_terms = {
                'healthcare': ['medical', 'health', 'patient', 'clinical', 'diagnosis'],
                'finance': ['financial', 'banking', 'payment', 'investment', 'trading'],
                'education': ['learning', 'teaching', 'educational', 'student', 'training'],
                'retail': ['shopping', 'commerce', 'customer', 'sales', 'store'],
                'manufacturing': ['production', 'factory', 'assembly', 'supply chain'],
                'transportation': ['logistics', 'delivery', 'mobility', 'vehicle', 'travel'],
                'energy': ['power', 'renewable', 'solar', 'wind', 'battery'],
                'entertainment': ['media', 'content', 'gaming', 'streaming', 'social'],
                'agriculture': ['farming', 'crop', 'livestock', 'agricultural', 'food'],
                'real_estate': ['property', 'housing', 'construction', 'building'],
                'logistics': ['supply chain', 'warehouse', 'distribution', 'shipping'],
                'telecommunications': ['communication', 'network', 'connectivity', 'telecom'],
                'government': ['public', 'civic', 'municipal', 'regulation', 'policy'],
                'construction': ['building', 'infrastructure', 'engineering', 'architecture'],
                'insurance': ['risk', 'coverage', 'claims', 'underwriting', 'actuarial']
            }
            
            related_terms = sector_terms.get(sector, [])
            term_matches = sum(1 for term in related_terms if term in text)
            base_score += term_matches * 0.3
            
            # Cap the score at 10.0
            industry_disruption[sector] = min(10.0, max(0.0, base_score))
        
        return industry_disruption
    
    def get_breakthrough_summary(self, analysis: BreakthroughAnalysis) -> Dict[str, Any]:
        """Generate a summary of breakthrough analysis"""
        return {
            'breakthrough_category': self._get_breakthrough_category(analysis),
            'key_strengths': self._get_key_strengths(analysis),
            'key_risks': analysis.risk_factors[:3],  # Top 3 risks
            'top_opportunities': analysis.opportunity_factors[:3],  # Top 3 opportunities
            'disruptive_industries': self._get_top_disruptive_industries(analysis),
            'overall_assessment': self._get_overall_assessment(analysis)
        }
    
    def _get_breakthrough_category(self, analysis: BreakthroughAnalysis) -> str:
        """Categorize the breakthrough level"""
        if analysis.is_moonshot:
            return "Moonshot"
        elif analysis.is_game_changer:
            return "Game Changer"
        elif analysis.is_breakthrough:
            return "Breakthrough"
        else:
            return "Incremental Innovation"
    
    def _get_key_strengths(self, analysis: BreakthroughAnalysis) -> List[str]:
        """Identify key strengths of the idea"""
        strengths = []
        
        if analysis.breakthrough_score >= 8.0:
            strengths.append("High breakthrough potential")
        
        if analysis.scalability_score >= 7.0:
            strengths.append("Strong scalability")
        
        if analysis.versatility_score >= 6.0:
            strengths.append("Cross-industry applicability")
        
        if analysis.moonshot_indicators:
            strengths.append("Strong innovation signals")
        
        return strengths
    
    def _get_top_disruptive_industries(self, analysis: BreakthroughAnalysis, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get top industries for disruption potential"""
        sorted_industries = sorted(
            analysis.industry_disruption_potential.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_industries[:top_n]
    
    def _get_overall_assessment(self, analysis: BreakthroughAnalysis) -> str:
        """Provide overall assessment of the idea"""
        if analysis.is_moonshot:
            return "Revolutionary idea with paradigm-shifting potential"
        elif analysis.is_game_changer:
            return "Game-changing idea with significant market impact potential"
        elif analysis.is_breakthrough:
            return "Breakthrough idea with strong innovation characteristics"
        elif analysis.breakthrough_score >= 6.0:
            return "Promising idea with good innovation potential"
        else:
            return "Incremental improvement with limited breakthrough potential"