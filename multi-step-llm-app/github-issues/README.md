# GitHub Issues for Multi-Step LLM Application

This directory contains detailed GitHub issues to be created for improving the Multi-Step LLM Application pipeline. Each issue is comprehensive and ready to be copied into GitHub.

## Issues to Create

### 1. 🧪 [Integration Testing CLI](./issue-1-integration-testing.md)
**Title**: Add Integration Testing CLI for Individual Component Testing

**Summary**: Create a comprehensive integration testing CLI that allows testing each pipeline component individually with real API calls, helping developers verify behavior and debug issues in isolation.

**Key Features**:
- Test individual components with real API calls
- Predefined test scenarios
- Interactive debugging mode
- Performance monitoring
- HTML test reports

**Labels**: `enhancement`, `testing`, `developer-tools`

---

### 2. 📊 [Comprehensive Logging System](./issue-2-logging-system.md)
**Title**: Implement Comprehensive Logging System for CLI and File Output

**Summary**: Add extensive logging that provides detailed visibility into pipeline execution, with output to both CLI (with rich formatting) and structured log files for debugging and monitoring.

**Key Features**:
- Structured logging to files and console
- API call tracking with costs
- Performance metrics
- Log analysis tools
- Session-based organization

**Labels**: `enhancement`, `logging`, `monitoring`

---

### 3. 🐛 [DEBUG Mode](./issue-3-debug-mode.md)
**Title**: Add DEBUG Mode with Cost-Effective Model Switching

**Summary**: Implement a DEBUG mode that automatically switches all LLM calls to cheaper models (Claude Sonnet) and enables verbose logging, allowing full pipeline testing without high costs.

**Key Features**:
- Automatic model switching to cheaper alternatives
- Verbose logging of all operations
- Cost tracking and savings display
- Auto-enabled for integration tests
- Configurable debug options

**Labels**: `enhancement`, `cost-optimization`, `developer-tools`

---

### 4. 🎯 [Sophisticated Scoring System](./issue-4-sophisticated-scoring.md)
**Title**: Implement Sophisticated Scoring with Smart Filtering

**Summary**: Create a more nuanced scoring and filtering system that respects zone importance while ensuring breakthrough ideas aren't filtered out due to rigid percentage cutoffs.

**Key Features**:
- Multi-dimensional scoring framework
- Breakthrough idea detection
- Flexible quota system
- Cross-zone optimization
- Safety checks against dropping gems

**Labels**: `enhancement`, `algorithm`, `critical`

---

### 5. 📈 [Fix Mermaid Diagram](./issue-5-mermaid-diagram-fix.md)
**Title**: Fix Mermaid Diagram for Accuracy and Clarity

**Summary**: Correct the pipeline flow diagram to accurately represent the actual data flow, removing misleading elements and improving visual clarity.

**Key Changes**:
- Show single EXA call (not 5)
- Group clustering operations
- Remove unnecessary diamond shapes
- Show percentage filtering
- Add visual grouping for clarity

**Labels**: `documentation`, `bug`, `good-first-issue`

---

## Creating the Issues

To create these issues on GitHub:

1. Go to: https://github.com/Flying-Pig-Labs/helios/issues
2. Click "New Issue"
3. Copy the title from above
4. Copy the entire content from the linked markdown file
5. Add the suggested labels
6. Submit the issue

## Priority Order

Recommended implementation order:

1. **Issue #5** (Mermaid Diagram) - Quick fix, improves documentation immediately
2. **Issue #2** (Logging) - Foundation for debugging other features
3. **Issue #3** (DEBUG Mode) - Enables cost-effective development
4. **Issue #1** (Integration Testing) - Builds on logging and debug mode
5. **Issue #4** (Scoring System) - Most complex, benefits from other improvements

## Dependencies

- Issue #1 depends on Issue #2 (logging) and Issue #3 (debug mode)
- Issue #3 can use Issue #2's logging system
- Issue #4 benefits from Issue #2's logging for transparency
- Issue #5 is independent and can be done immediately

## Estimated Effort

| Issue | Effort | Impact | Complexity |
|-------|--------|--------|------------|
| #1 | High (2-3 days) | High | Medium |
| #2 | Medium (1-2 days) | High | Low |
| #3 | Medium (1-2 days) | High | Medium |
| #4 | High (3-4 days) | Critical | High |
| #5 | Low (1 hour) | Medium | Low |

## Success Metrics

After implementing all issues:

- 90% reduction in debugging time (logging + integration tests)
- 80-90% cost savings during development (debug mode)
- Zero breakthrough ideas lost to filtering (sophisticated scoring)
- Clear, accurate documentation (fixed diagram)
- Component-level testing capability (integration CLI)

## Notes

- All issues include detailed implementation plans
- Each issue has clear success criteria
- Code examples are provided where relevant
- Benefits and rationale are explained
- Related issues are cross-referenced