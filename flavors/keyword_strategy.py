#!/usr/bin/env python3
"""
Keyword Strategy Module - Flavor-Based Reddit Query Customization

Handles the generation of Reddit search queries based on flavor configuration.
Supports seed terms, exclusions, patterns, synonyms, stemming, and entity extraction.
"""

import re
import json
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Optional imports for advanced features
try:
    import nltk
    from nltk.corpus import wordnet
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.info("NLTK not available - synonym and stemming features disabled")

@dataclass
class QuerySet:
    """Structured set of Reddit queries for a specific JTBD/flavor combination."""
    jtbd: str
    base_queries: List[str]  # Core queries directly from JTBD
    expanded_queries: List[str]  # Queries with synonyms/stemming
    pattern_queries: List[str]  # Queries using flavor-specific patterns
    subreddit_specific: Dict[str, List[str]]  # Subreddit-tailored queries
    excluded_terms_found: List[str]  # Terms that were filtered out
    
    def get_all_queries(self, limit: int = None) -> List[str]:
        """Get all queries combined, deduplicated, and optionally limited."""
        all_queries = []
        all_queries.extend(self.base_queries)
        all_queries.extend(self.expanded_queries) 
        all_queries.extend(self.pattern_queries)
        
        # Add subreddit-specific queries
        for subreddit_queries in self.subreddit_specific.values():
            all_queries.extend(subreddit_queries)
        
        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for query in all_queries:
            if query.lower() not in seen and len(query.strip()) > 5:
                seen.add(query.lower())
                unique_queries.append(query)
        
        return unique_queries[:limit] if limit else unique_queries

class KeywordStrategyEngine:
    """
    Generates flavor-customized Reddit search queries.
    
    Handles the complete keyword strategy pipeline:
    1. Extract base terms from JTBD
    2. Apply seed terms and exclusions from flavor config
    3. Expand with synonyms and stemming (if enabled)
    4. Apply query patterns (templates)
    5. Generate subreddit-specific variations
    6. Filter and rank final query set
    """
    
    def __init__(self):
        """Initialize the keyword strategy engine."""
        self.stemmer = PorterStemmer() if NLTK_AVAILABLE else None
        
    def extract_base_keywords(self, jtbd: str) -> List[str]:
        """Extract base keywords from a JTBD statement."""
        # Remove common JTBD pattern words
        stop_patterns = [
            r'\bwhen i\b', r'\bi want to\b', r'\bso i can\b', r'\bso that i\b',
            r'\bwithout\b', r'\bwhile\b', r'\bbefore\b', r'\bafter\b'
        ]
        
        cleaned_jtbd = jtbd.lower()
        for pattern in stop_patterns:
            cleaned_jtbd = re.sub(pattern, ' ', cleaned_jtbd, flags=re.IGNORECASE)
        
        # Extract meaningful words (2+ chars, not pure numbers)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', cleaned_jtbd)
        
        # Filter common words
        common_words = {
            'and', 'the', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one',
            'our', 'had', 'will', 'there', 'each', 'which', 'she', 'how', 'what', 'who', 'why',
            'need', 'want', 'have', 'get', 'make', 'find', 'way', 'time', 'help', 'good', 'best'
        }
        
        keywords = [word for word in words if word not in common_words and len(word) > 2]
        return keywords[:10]  # Top 10 keywords
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word using WordNet."""
        if not NLTK_AVAILABLE:
            return []
        
        synonyms = set()
        try:
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ')
                    if synonym != word and len(synonym) > 2:
                        synonyms.add(synonym)
        except Exception as e:
            logger.debug(f"Error getting synonyms for '{word}': {e}")
        
        return list(synonyms)[:3]  # Limit to 3 synonyms per word
    
    def apply_stemming(self, words: List[str]) -> List[str]:
        """Apply stemming to a list of words."""
        if not NLTK_AVAILABLE or not self.stemmer:
            return words
        
        stemmed = []
        for word in words:
            try:
                stemmed_word = self.stemmer.stem(word)
                if stemmed_word != word and len(stemmed_word) > 2:
                    stemmed.append(stemmed_word)
            except Exception as e:
                logger.debug(f"Error stemming '{word}': {e}")
        
        return stemmed
    
    def apply_query_patterns(self, keywords: List[str], patterns: List[str]) -> List[str]:
        """Apply query template patterns to keywords."""
        if not patterns:
            # Default patterns for Reddit queries
            patterns = [
                "how to {term}",
                "{term} problems", 
                "{term} issues",
                "{term} frustration",
                "{term} help needed",
                "struggling with {term}",
                "{term} advice",
                "{term} tips"
            ]
        
        pattern_queries = []
        for pattern in patterns:
            for keyword in keywords[:5]:  # Limit to top 5 keywords
                if '{term}' in pattern:
                    query = pattern.format(term=keyword)
                    pattern_queries.append(query)
        
        return pattern_queries
    
    def generate_subreddit_specific_queries(
        self, base_queries: List[str], subreddit_hints: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Generate queries tailored to specific subreddits."""
        subreddit_queries = {}
        
        for domain, subreddits in subreddit_hints.items():
            domain_queries = []
            
            # Add domain-specific context to base queries
            for query in base_queries[:3]:  # Top 3 base queries
                # Add domain context
                domain_query = f"{query} {domain}"
                domain_queries.append(domain_query)
                
                # Add subreddit-specific variations
                for subreddit in subreddits[:2]:  # Max 2 subreddits per domain
                    if subreddit.lower() in ['realestate', 'investing']:
                        # Financial context
                        domain_queries.append(f"{query} investment")
                        domain_queries.append(f"{query} market")
                    elif subreddit.lower() in ['smallbusiness', 'entrepreneur']:
                        # Business context
                        domain_queries.append(f"{query} business")
                        domain_queries.append(f"{query} startup")
            
            subreddit_queries[domain] = domain_queries[:5]  # Limit per domain
        
        return subreddit_queries
    
    def filter_excluded_terms(self, queries: List[str], exclusions: List[str]) -> Tuple[List[str], List[str]]:
        """Filter out queries containing excluded terms."""
        if not exclusions:
            return queries, []
        
        exclusion_patterns = [re.escape(term.lower()) for term in exclusions]
        combined_pattern = '|'.join(exclusion_patterns)
        
        filtered_queries = []
        excluded_found = []
        
        for query in queries:
            if re.search(combined_pattern, query.lower()):
                # Find which exclusion term matched
                for exclusion in exclusions:
                    if exclusion.lower() in query.lower():
                        excluded_found.append(f"'{exclusion}' in '{query}'")
                        break
            else:
                filtered_queries.append(query)
        
        return filtered_queries, excluded_found
    
    def generate_query_set(
        self, jtbd: str, reddit_strategy: Any, analysis_content: str = ""
    ) -> QuerySet:
        """
        Generate a complete query set for a JTBD using flavor configuration.
        
        Args:
            jtbd: Jobs-to-be-Done statement
            reddit_strategy: RedditSearchStrategy config from flavor
            analysis_content: Original research content (for entity extraction)
            
        Returns:
            QuerySet with all generated queries organized by type
        """
        # Step 1: Extract base keywords from JTBD
        base_keywords = self.extract_base_keywords(jtbd)
        
        # Step 2: Add seed terms from flavor config
        all_keywords = base_keywords.copy()
        if hasattr(reddit_strategy, 'seed_terms') and reddit_strategy.seed_terms:
            all_keywords.extend(reddit_strategy.seed_terms)
        
        # Step 3: Generate base queries from keywords
        base_queries = []
        for keyword in all_keywords[:8]:  # Top 8 keywords
            base_queries.extend([
                keyword,
                f"{keyword} problem",
                f"{keyword} issue"
            ])
        
        # Step 4: Expand with synonyms (if enabled)
        expanded_queries = []
        if getattr(reddit_strategy, 'enable_synonyms', True):
            for keyword in base_keywords[:5]:  # Top 5 for synonym expansion
                synonyms = self.get_synonyms(keyword)
                for synonym in synonyms:
                    expanded_queries.append(synonym)
                    expanded_queries.append(f"{synonym} problem")
        
        # Step 5: Apply stemming (if enabled)
        if getattr(reddit_strategy, 'enable_stemming', True):
            stemmed_words = self.apply_stemming(base_keywords)
            for stemmed in stemmed_words:
                expanded_queries.append(stemmed)
        
        # Step 6: Apply query patterns
        patterns = getattr(reddit_strategy, 'query_patterns', [])
        pattern_queries = self.apply_query_patterns(all_keywords, patterns)
        
        # Step 7: Generate subreddit-specific queries
        subreddit_hints = getattr(reddit_strategy, 'subreddit_hints', {})
        subreddit_queries = self.generate_subreddit_specific_queries(
            base_queries, subreddit_hints
        )
        
        # Step 8: Apply exclusions
        exclusions = getattr(reddit_strategy, 'exclusion_terms', [])
        
        base_queries, base_excluded = self.filter_excluded_terms(base_queries, exclusions)
        expanded_queries, exp_excluded = self.filter_excluded_terms(expanded_queries, exclusions)
        pattern_queries, pat_excluded = self.filter_excluded_terms(pattern_queries, exclusions)
        
        # Filter subreddit queries
        for domain in subreddit_queries:
            subreddit_queries[domain], sub_excluded = self.filter_excluded_terms(
                subreddit_queries[domain], exclusions
            )
        
        all_excluded = base_excluded + exp_excluded + pat_excluded
        
        return QuerySet(
            jtbd=jtbd,
            base_queries=base_queries[:5],  # Top 5 base queries
            expanded_queries=expanded_queries[:5],  # Top 5 expanded
            pattern_queries=pattern_queries[:5],  # Top 5 pattern-based
            subreddit_specific=subreddit_queries,
            excluded_terms_found=all_excluded
        )

def generate_flavor_queries(jtbds: List[str], flavor_config: Any, analysis_content: str = "") -> Dict[str, QuerySet]:
    """
    Generate Reddit queries for all JTBDs using flavor configuration.
    
    Args:
        jtbds: List of JTBD statements
        flavor_config: Complete flavor configuration
        analysis_content: Original research content
        
    Returns:
        Dict mapping JTBD index to QuerySet
    """
    engine = KeywordStrategyEngine()
    reddit_strategy = flavor_config.reddit_strategy
    
    query_sets = {}
    
    for idx, jtbd in enumerate(jtbds):
        try:
            query_set = engine.generate_query_set(jtbd, reddit_strategy, analysis_content)
            query_sets[f"jtbd_{idx:03d}"] = query_set
            
            logger.info(f"Generated {len(query_set.get_all_queries())} queries for JTBD {idx + 1}")
            
            if query_set.excluded_terms_found:
                logger.info(f"Excluded {len(query_set.excluded_terms_found)} queries due to exclusion terms")
                
        except Exception as e:
            logger.error(f"Error generating queries for JTBD {idx + 1}: {e}")
            # Fallback to simple keyword extraction
            keywords = engine.extract_base_keywords(jtbd)
            query_sets[f"jtbd_{idx:03d}"] = QuerySet(
                jtbd=jtbd,
                base_queries=keywords[:5],
                expanded_queries=[],
                pattern_queries=[],
                subreddit_specific={},
                excluded_terms_found=[]
            )
    
    return query_sets