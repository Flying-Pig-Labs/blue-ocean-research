# Scoring Subsystem

This package implements the idea scoring pipeline used by the multi-step LLM application.

- `idea_score.py` – base data structures and scoring utilities.
- `breakthrough_detector.py` – flags moonshots and other breakthrough ideas.
- `smart_filterer.py` – filters ideas across zones while preserving excellence.
- `confidence_scorer.py` – estimates confidence and applies risk adjustments.
- `cross_zone_optimizer.py` – balances portfolios across opportunity zones.
- `final_selector.py` – ensemble selector that combines multiple strategies.
- `selection_reporter.py` – generates analysis reports of the selection process.

These modules are used together by the product idea generator to select and
explain promising opportunities.
