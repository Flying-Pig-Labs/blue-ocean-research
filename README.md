# Blue Ocean Research

Prototype multi-step LLM pipeline for generating and evaluating product ideas.

The main application lives under `multi-step-llm-app/src` and orchestrates
multiple stages such as research analysis, opportunity clustering and idea
scoring. Key features discovered from the code include:

- Rich logging with optional debug mode and cost tracking.
- Modular scoring subsystem with confidence analysis and portfolio balancing.
- Utilities for loading prompts and managing secrets.

Most executable entry points live in the `multi-step-llm-app/src` directory.
Individual modules include file-level comments describing their roles.
