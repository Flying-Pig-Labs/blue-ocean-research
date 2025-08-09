# Proposed Context Structure for Conviction-Based README Generation

## Current Problem
We're dumping raw JSON data without narrative structure. The LLM sees data points but not the journey of discovery that led to the breakthrough.

## Proposed Context Structure

```python
context = {
    # 1. THE ORIGINAL HYPOTHESIS
    "research_foundation": {
        "original_research": research_analysis.get("content", ""),  # The raw markdown
        "initial_hypothesis": research_analysis.get("executive_summary", ""),
        "market_assumptions": research_analysis.get("key_assumptions", []),
        "research_scope": {
            "participants": research_analysis.get("participants", "Unknown"),
            "timeframe": research_analysis.get("timeframe", ""),
            "methodology": research_analysis.get("methodology", "")
        }
    },
    
    # 2. THE DISCOVERY JOURNEY
    "discovery_progression": {
        "stage_1_insights": {
            "what_we_thought": research_analysis.get("initial_findings", ""),
            "what_surprised_us": research_analysis.get("unexpected_findings", []),
            "key_quotes": research_analysis.get("notable_quotes", []),
            "emerging_patterns": research_analysis.get("patterns", [])
        },
        
        "stage_2_validation": {
            "jtbd_discoveries": {
                "total_jobs_identified": len(jtbd_data.get("jtbd_data", {}).get("jobs_list", [])),
                "top_3_critical_jobs": sorted(
                    jtbd_data.get("jtbd_data", {}).get("jobs_list", []),
                    key=lambda x: x.get("opportunity_score", 0),
                    reverse=True
                )[:3],
                "biggest_surprise": self._find_biggest_jtbd_surprise(jtbd_data),
                "underserved_score_average": self._calculate_underserved_score(jtbd_data)
            },
            "reddit_evidence": {
                "discussions_analyzed": len(reddit_discussions),
                "subreddits_covered": self._get_unique_subreddits(reddit_discussions),
                "most_passionate_topics": self._get_most_engaged_topics(reddit_discussions),
                "verbatim_pain_quotes": self._extract_pain_quotes(reddit_discussions)[:5],
                "validation_strength": self._calculate_validation_strength(reddit_discussions)
            }
        },
        
        "stage_3_breakthrough": {
            "opportunity_zones": {
                "total_zones_discovered": len(zones_data.get("clustered_zones", {})),
                "dominant_zone": self._get_dominant_zone(zones_with_percentages),
                "market_concentration": {
                    "top_zone_percentage": zones_with_percentages[0].get("market_opportunity_percentage", 0),
                    "top_2_zones_combined": sum([z.get("market_opportunity_percentage", 0) for z in zones_with_percentages[:2]]),
                    "concentration_insight": self._get_concentration_insight(zones_with_percentages)
                },
                "pain_convergence": {
                    "most_severe_dimension": self._get_most_severe_pain_dimension(zones_data),
                    "cross_zone_pattern": self._find_cross_zone_pattern(zones_data),
                    "unifying_theme": self._extract_unifying_theme(zones_data)
                }
            }
        }
    },
    
    # 3. THE "HOLY SHIT" MOMENTS
    "breakthrough_insights": {
        "primary_revelation": self._synthesize_primary_insight(all_data),
        "supporting_revelations": [
            {
                "insight": "...",
                "evidence": "...",
                "implication": "..."
            }
        ],
        "market_blindspot": {
            "what_everyone_missed": "...",
            "why_they_missed_it": "...",
            "our_unique_understanding": "..."
        },
        "timing_catalyst": {
            "why_now": "...",
            "convergence_factors": [...],
            "window_of_opportunity": "..."
        }
    },
    
    # 4. THE STRATEGIC RESPONSE
    "innovation_strategy": {
        "portfolio_thesis": self._generate_portfolio_thesis(ideas_data),
        "domino_strategy": {
            "beachhead": zones_with_percentages[0],
            "expansion_path": self._map_expansion_path(zones_with_percentages),
            "network_effects": self._identify_network_effects(ideas_data)
        },
        "competitive_moat": {
            "unfair_advantages": self._extract_unfair_advantages(all_data),
            "barriers_we_create": self._identify_barriers(ideas_data),
            "lock_in_mechanisms": self._find_lock_ins(ideas_data)
        }
    },
    
    # 5. THE EVIDENCE STRENGTH
    "conviction_metrics": {
        "data_analyzed": {
            "total_data_points": self._count_total_datapoints(all_data),
            "reddit_discussions": len(reddit_discussions),
            "jtbds_validated": len(jtbd_data.get("jtbd_data", {}).get("jobs_list", [])),
            "pain_dimensions_measured": 8,
            "opportunity_zones_mapped": len(zones_data.get("clustered_zones", {}))
        },
        "confidence_indicators": {
            "cross_validation_score": self._calculate_cross_validation(all_data),
            "evidence_convergence": self._measure_convergence(all_data),
            "signal_strength": self._calculate_signal_strength(all_data)
        },
        "market_signals": {
            "tam": financial_projections.get("total_addressable_market", ""),
            "growth_rate": financial_projections.get("market_growth_rate", ""),
            "urgency_indicators": self._extract_urgency_signals(all_data)
        }
    },
    
    # 6. THE NARRATIVE ARC
    "story_elements": {
        "hook": self._generate_hook(breakthrough_insights),
        "tension": self._identify_tension_points(all_data),
        "resolution": self._map_resolution_path(ideas_data),
        "transformation": self._describe_transformation(all_data),
        "call_to_adventure": self._create_call_to_action(all_data)
    }
}
```

## Helper Methods Needed

```python
def _find_biggest_jtbd_surprise(self, jtbd_data):
    """Find the JTBD with highest opportunity score but lowest current satisfaction"""
    jobs = jtbd_data.get("jtbd_data", {}).get("jobs_list", [])
    if not jobs:
        return None
    
    # Find job with biggest gap between importance and satisfaction
    return max(jobs, key=lambda j: 
        (j.get("importance", 0) - j.get("satisfaction", 10)) * j.get("opportunity_score", 0)
    )

def _calculate_underserved_score(self, jtbd_data):
    """Calculate average underserved score (importance - satisfaction)"""
    jobs = jtbd_data.get("jtbd_data", {}).get("jobs_list", [])
    if not jobs:
        return 0
    
    scores = [j.get("importance", 0) - j.get("satisfaction", 10) for j in jobs]
    return sum(scores) / len(scores)

def _get_dominant_zone(self, zones_with_percentages):
    """Get the zone with highest market opportunity"""
    if not zones_with_percentages:
        return None
    
    zone = zones_with_percentages[0]
    return {
        "name": zone.get("name"),
        "percentage": zone.get("market_opportunity_percentage"),
        "why_dominant": f"Addresses {len(zone.get('jtbds_addressed', []))} critical jobs with {zone.get('evidence_strength', {}).get('score', 0)}/10 evidence strength"
    }

def _get_concentration_insight(self, zones_with_percentages):
    """Interpret what the concentration pattern means"""
    if not zones_with_percentages:
        return "No clear pattern"
    
    top_percentage = zones_with_percentages[0].get("market_opportunity_percentage", 0)
    
    if top_percentage > 40:
        return "MASSIVE CONCENTRATION: One zone dominates the entire market opportunity"
    elif top_percentage > 30:
        return "STRONG LEADER: Clear primary opportunity with supporting zones"
    else:
        return "DISTRIBUTED OPPORTUNITY: Multiple viable entry points"

def _synthesize_primary_insight(self, all_data):
    """Generate the single most important insight from all data"""
    # This would analyze patterns across all stages to find the breakthrough
    # For example: "87% of users are desperately trying to [JOB] but every solution fails because [REASON]"
    pass

def _extract_pain_quotes(self, reddit_discussions):
    """Pull actual user quotes expressing pain"""
    # Filter for high-emotion, high-engagement comments
    pass

def _generate_portfolio_thesis(self, ideas_data):
    """Create a unified thesis for why these 10 ideas form a coherent strategy"""
    pass
```

## Key Improvements Over Current Approach

### 1. **Journey Structure**
Instead of dumping data, we tell the story of discovery:
- What we started with
- What surprised us
- What breakthrough we found
- Why it matters

### 2. **Highlight Contrasts**
Show the delta between expectations and reality:
- "We thought X, but discovered Y"
- "Everyone assumes A, but the data shows B"

### 3. **Evidence Hierarchy**
Not all evidence is equal:
- Primary revelation (the big insight)
- Supporting evidence (proof points)
- Validation metrics (why we're confident)

### 4. **Strategic Narrative**
Connect insights to action:
- Discovery → Opportunity → Strategy → Urgency

### 5. **Emotional Progression**
Build conviction through stages:
- Curiosity → Surprise → Realization → Conviction → Action

## Example Context Output

```json
{
  "research_foundation": {
    "original_research": "We set out to understand why productivity tools fail...",
    "research_scope": {
      "participants": "247 knowledge workers",
      "timeframe": "3 months",
      "methodology": "Interviews, surveys, behavioral observation"
    }
  },
  
  "discovery_progression": {
    "stage_2_validation": {
      "jtbd_discoveries": {
        "biggest_surprise": {
          "job_statement": "When I need to share context with my team",
          "opportunity_score": 9.2,
          "importance": 9,
          "satisfaction": 2,
          "insight": "This job has a 7-point gap - largest we've ever seen"
        }
      },
      "reddit_evidence": {
        "verbatim_pain_quotes": [
          "I spend 3 hours a day just explaining things that should be obvious",
          "Every new team member takes 6 months to understand our system",
          "We've tried 5 different tools and none solve the real problem"
        ]
      }
    }
  },
  
  "breakthrough_insights": {
    "primary_revelation": "87% of productivity loss isn't from bad tools - it's from context fragmentation. Every solution optimizes the wrong thing.",
    "market_blindspot": {
      "what_everyone_missed": "Tools focus on individual productivity when the problem is team context",
      "why_they_missed_it": "Easier to measure individual metrics than team cognition",
      "our_unique_understanding": "We found the pattern by analyzing communication overhead, not task completion"
    }
  }
}
```

This structure gives Opus 4.1:
1. The narrative arc to follow
2. The evidence to support claims
3. The emotional beats to hit
4. The strategic reasoning to convey
5. The urgency to communicate

Would you like me to implement this context structure in the code?