# Ideation Flow Upgrade Summary

## What was done
- Introduced an extensible flow-selection mechanism (`--flow-type` CLI arg or `IDEATION_TYPE` env var) allowing the ideation pipeline to choose between five flows (`innovation`, `medical-device`, `private-equity`, `city-revitalization`, `data-center`).
- Refactored `run_pipeline.py` into an orchestrator that dispatches to `IdeationFlow` classes. The existing multi-stage process now lives in `InnovationFlow`, while new `SimpleIdeationFlow` subclasses execute a single Opus 4.1 call and publish ten parsed ideas to GitHub.
- Updated `run_pipeline_v2.py` and `batch_wrapper.py` to forward the selected flow so AWS Batch jobs can run the appropriate path without changing higher-level cloud logic.

## Why it was done
- The previous pipeline supported only a single complex "innovation" flow. Adding a flow-selection abstraction decouples the ideation logic from the orchestrator, enabling future flows to plug in with minimal changes.
- Simplified flows (medical device, private equity, city revitalization, data center) require only a one-shot LLM call; the refactor isolates the heavy multi-stage pipeline so these new paths remain lightweight and easy to maintain.

## Future work to make this production-ready
- Implement real prompts and response-parsing logic for each `SimpleIdeationFlow` variant; current parsing assumes a simple newline-separated list.
- Integrate actual Opus 4.1 API credentials and error handling, including rate-limiting and retries.
- Expand tests to cover flow selection, LLM interactions, and GitHub repository creation for each flow type; raise coverage above the current threshold failure.
- Provide configuration or template repositories for each flow as needed and document prompts and expected outputs.

## Questions
- Are the prompt formats different for each flow, or can a single template be parameterized per `flow_type`?
- Should the orchestrator support additional metadata (e.g., market identifiers) that downstream flows may require?

## Concerns
- Test coverage currently fails, suggesting minimal existing tests; reaching the configured 70% threshold may require significant effort.
- Error handling for GitHub interactions and LLM responses remains basic; unhandled failures could leave partially created repositories.

