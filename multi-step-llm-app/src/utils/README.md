# Utility Modules

Helper components that support logging, debugging and secret management for the
pipeline:

- `pipeline_logger.py` – structured logging with session tracking.
- `debug_config.py` – global debug mode flags and limits.
- `debug_logger.py` – lightweight logger used when debugging is enabled.
- `debug_cost_tracker.py` – estimates API spend and potential savings.
- `debug_dashboard.py` – live Rich dashboard for observing pipeline progress.
- `debug_aware_component.py` – base class that adds debug-aware behaviour to components.
- `secrets_manager.py` – loads credentials from AWS Secrets Manager.

These utilities are imported throughout the codebase but have no external
runtime entry points.
