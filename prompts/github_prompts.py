"""
GitHub Integration Prompts

This module contains prompts for generating GitHub content including
README files and issue descriptions.
"""

README_GENERATION_PROMPT = """
Generate a comprehensive README.md file for a GitHub repository based on the following market research and analysis data.

The README should include:
1. Executive summary of the market opportunity
2. Key findings from Jobs-to-be-Done analysis
3. Weighted opportunity zones with market sizes
4. Product ideas overview with links to issues
5. Strategic consolidation opportunities
6. Implementation roadmap
7. Financial projections
8. Success metrics

Make it professional, well-structured with markdown formatting, and include relevant emojis for visual appeal.
Focus on actionable insights and clear value propositions.

Research Data:
{research_data}

JTBD Analysis:
{jtbd_data}

Opportunity Zones:
{zones_data}

Product Ideas:
{ideas_data}
"""

ISSUE_GENERATION_PROMPT = """
Generate a detailed GitHub issue for a product idea with the following information:

Product Idea:
{product_idea}

Related JTBD Data:
{jtbd_context}

The issue should include:
1. Clear overview of the product concept
2. Target jobs-to-be-done with opportunity scores
3. Value proposition
4. Key features list
5. Market analysis and sizing
6. Feasibility scores
7. Business case (time, cost, revenue model)
8. Implementation priority and phasing
9. Success criteria
10. Next steps

Format using GitHub-flavored markdown with clear sections and appropriate labels.
"""

CONSOLIDATION_ISSUE_PROMPT = """
Generate a GitHub issue for a strategic consolidation opportunity that combines multiple product ideas.

Consolidation Opportunity:
{consolidation_data}

Individual Product Ideas:
{product_ideas}

The issue should explain:
1. The strategic rationale for consolidation
2. Combined market potential
3. Synergies between products
4. Implementation complexity
5. Phased rollout approach
6. Resource requirements
7. Risk factors and mitigation

Make it clear this is a higher-level strategic initiative that encompasses multiple product concepts.
"""
