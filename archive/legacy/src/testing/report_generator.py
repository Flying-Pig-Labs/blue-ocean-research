"""
Report Generator

Generates comprehensive HTML and JSON reports for integration testing results
with visualization, performance metrics, and detailed analysis.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from ..utils.pipeline_logger import get_logger
from ..models.logging_models import ComponentType


@dataclass
class ReportConfig:
    """Configuration for report generation"""

    include_debug_data: bool = True
    include_performance_metrics: bool = True
    include_validation_details: bool = True
    include_charts: bool = True
    theme: str = "default"  # default, dark, minimal
    export_formats: List[str] = None

    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["html", "json"]


class ReportGenerator:
    """Generates comprehensive test reports"""

    def __init__(self, logger=None):
        """Initialize the report generator"""
        self.logger = logger or get_logger()

        # HTML templates
        self.html_template = self._get_html_template()
        self.css_styles = self._get_css_styles()
        self.js_scripts = self._get_js_scripts()

        self.logger.info("Report generator initialized", ComponentType.MAIN_PIPELINE)

    def generate_report(
        self,
        test_results: List[Dict[str, Any]],
        output_dir: str = "test_reports",
        config: Optional[ReportConfig] = None,
    ) -> str:
        """Generate comprehensive test report"""
        if config is None:
            config = ReportConfig()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Process and analyze results
            report_data = self._process_test_results(test_results, config)

            # Generate reports in requested formats
            generated_files = []

            if "html" in config.export_formats:
                html_file = output_path / f"integration_test_report_{timestamp}.html"
                self._generate_html_report(report_data, html_file, config)
                generated_files.append(str(html_file))

            if "json" in config.export_formats:
                json_file = output_path / f"integration_test_report_{timestamp}.json"
                self._generate_json_report(report_data, json_file)
                generated_files.append(str(json_file))

            # Generate summary file
            summary_file = output_path / f"test_summary_{timestamp}.txt"
            self._generate_summary_report(report_data, summary_file)
            generated_files.append(str(summary_file))

            self.logger.info(
                f"Generated test reports",
                ComponentType.MAIN_PIPELINE,
                metadata={
                    "files_generated": len(generated_files),
                    "output_dir": output_dir,
                },
            )

            return generated_files[0] if generated_files else ""

        except Exception as e:
            self.logger.error(
                f"Error generating reports: {e}", ComponentType.MAIN_PIPELINE
            )
            raise

    def _process_test_results(
        self, test_results: List[Dict[str, Any]], config: ReportConfig
    ) -> Dict[str, Any]:
        """Process and analyze test results for reporting"""
        if not test_results:
            return {"error": "No test results provided"}

        # Basic statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result.get("success", False))
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        # Component analysis
        component_stats = {}
        for result in test_results:
            component = result.get("component", "unknown")
            if component not in component_stats:
                component_stats[component] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "total_time": 0,
                    "total_cost": 0,
                    "total_tokens": 0,
                }

            stats = component_stats[component]
            stats["total"] += 1
            if result.get("success", False):
                stats["passed"] += 1
            else:
                stats["failed"] += 1

            # Performance data
            if "performance" in result:
                perf = result["performance"]
                stats["total_time"] += perf.get("duration_seconds", 0)
                stats["total_cost"] += perf.get("estimated_cost", 0)
                stats["total_tokens"] += perf.get("total_tokens", 0)

        # Calculate averages
        for component, stats in component_stats.items():
            if stats["total"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["total"]
                stats["avg_cost"] = stats["total_cost"] / stats["total"]
                stats["avg_tokens"] = stats["total_tokens"] / stats["total"]
                stats["success_rate"] = (stats["passed"] / stats["total"]) * 100

        # Validation analysis
        validation_summary = self._analyze_validation_results(test_results)

        # Performance analysis
        performance_summary = self._analyze_performance_results(test_results)

        # Error analysis
        error_analysis = self._analyze_errors(test_results)

        # Debug data analysis (if available)
        debug_analysis = {}
        if config.include_debug_data:
            debug_analysis = self._analyze_debug_data(test_results)

        return {
            "metadata": {
                "report_generated": datetime.now().isoformat(),
                "total_tests": total_tests,
                "config": {
                    "include_debug_data": config.include_debug_data,
                    "include_performance_metrics": config.include_performance_metrics,
                    "theme": config.theme,
                },
            },
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
            },
            "component_analysis": component_stats,
            "validation_summary": validation_summary,
            "performance_summary": performance_summary,
            "error_analysis": error_analysis,
            "debug_analysis": debug_analysis,
            "raw_results": test_results,
        }

    def _analyze_validation_results(
        self, test_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze validation results across all tests"""
        validation_data = []
        for result in test_results:
            if "validation" in result:
                validation_data.append(result["validation"])

        if not validation_data:
            return {"message": "No validation data available"}

        total_checks = sum(v.get("total_checks", 0) for v in validation_data)
        passed_checks = sum(v.get("passed_checks", 0) for v in validation_data)
        total_errors = sum(len(v.get("errors", [])) for v in validation_data)

        # Error categorization
        error_types = {}
        severity_counts = {"error": 0, "warning": 0, "info": 0}

        for validation in validation_data:
            for error in validation.get("errors", []):
                error_type = error.get("error_type", "unknown")
                severity = error.get("severity", "error")

                error_types[error_type] = error_types.get(error_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "check_pass_rate": (passed_checks / total_checks) * 100
            if total_checks > 0
            else 0,
            "total_errors": total_errors,
            "error_types": error_types,
            "severity_distribution": severity_counts,
            "validation_details": validation_data,
        }

    def _analyze_performance_results(
        self, test_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze performance metrics across all tests"""
        performance_data = []
        for result in test_results:
            if "performance" in result:
                performance_data.append(result["performance"])

        if not performance_data:
            return {"message": "No performance data available"}

        total_duration = sum(p.get("duration_seconds", 0) for p in performance_data)
        total_cost = sum(p.get("estimated_cost", 0) for p in performance_data)
        total_tokens = sum(p.get("total_tokens", 0) for p in performance_data)
        # Handle api_calls being either a list or an integer
        total_api_calls = sum(
            len(p["api_calls"])
            if isinstance(p.get("api_calls"), list)
            else p.get("total_api_calls", 0)
            for p in performance_data
        )

        avg_duration = total_duration / len(performance_data)
        avg_cost = total_cost / len(performance_data)
        avg_tokens = total_tokens / len(performance_data)

        # Performance trends
        durations = [p.get("duration_seconds", 0) for p in performance_data]
        costs = [p.get("estimated_cost", 0) for p in performance_data]

        return {
            "total_duration": total_duration,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_api_calls": total_api_calls,
            "averages": {
                "duration": avg_duration,
                "cost": avg_cost,
                "tokens": avg_tokens,
            },
            "ranges": {
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "min_cost": min(costs) if costs else 0,
                "max_cost": max(costs) if costs else 0,
            },
            "performance_details": performance_data,
        }

    def _analyze_errors(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze errors and failures across all tests"""
        errors = []
        failure_patterns = {}

        for result in test_results:
            if not result.get("success", True):
                error_msg = result.get("error_message", "Unknown error")
                errors.append(
                    {
                        "component": result.get("component", "unknown"),
                        "error": error_msg,
                        "timestamp": result.get("timestamp", ""),
                    }
                )

                # Categorize error patterns
                if "timeout" in error_msg.lower():
                    failure_patterns["timeout"] = failure_patterns.get("timeout", 0) + 1
                elif "api" in error_msg.lower():
                    failure_patterns["api_error"] = (
                        failure_patterns.get("api_error", 0) + 1
                    )
                elif "import" in error_msg.lower() or "module" in error_msg.lower():
                    failure_patterns["import_error"] = (
                        failure_patterns.get("import_error", 0) + 1
                    )
                else:
                    failure_patterns["other"] = failure_patterns.get("other", 0) + 1

        return {
            "total_errors": len(errors),
            "error_list": errors,
            "failure_patterns": failure_patterns,
            "most_common_failure": max(failure_patterns.items(), key=lambda x: x[1])[0]
            if failure_patterns
            else None,
        }

    def _analyze_debug_data(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze debug data if available"""
        debug_sessions = []
        total_debug_cost = 0
        total_debug_tokens = 0

        for result in test_results:
            if result.get("debug_mode", False) and "debug_data" in result:
                debug_data = result["debug_data"]
                debug_sessions.append(debug_data)

                # Extract cost and token data
                if "cost_tracking" in debug_data:
                    cost_data = debug_data["cost_tracking"]
                    total_debug_cost += cost_data.get("session_cost", 0)
                    total_debug_tokens += cost_data.get("session_tokens", 0)

        if not debug_sessions:
            return {"message": "No debug data available"}

        return {
            "debug_sessions_count": len(debug_sessions),
            "total_debug_cost": total_debug_cost,
            "total_debug_tokens": total_debug_tokens,
            "average_debug_cost": total_debug_cost / len(debug_sessions),
            "average_debug_tokens": total_debug_tokens / len(debug_sessions),
            "debug_details": debug_sessions,
        }

    def _generate_html_report(
        self, report_data: Dict[str, Any], output_file: Path, config: ReportConfig
    ):
        """Generate HTML report"""
        # Prepare data for HTML template
        template_data = {
            "title": "Integration Test Report",
            "generated_time": report_data["metadata"]["report_generated"],
            "summary": report_data["summary"],
            "component_analysis": report_data["component_analysis"],
            "validation_summary": report_data["validation_summary"],
            "performance_summary": report_data["performance_summary"],
            "error_analysis": report_data["error_analysis"],
            "debug_analysis": report_data.get("debug_analysis", {}),
            "include_debug": config.include_debug_data,
            "include_performance": config.include_performance_metrics,
            "theme": config.theme,
        }

        # Generate HTML content
        html_content = self._render_html_template(template_data)

        with open(output_file, "w") as f:
            f.write(html_content)

    def _generate_json_report(self, report_data: Dict[str, Any], output_file: Path):
        """Generate JSON report"""
        with open(output_file, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

    def _generate_summary_report(self, report_data: Dict[str, Any], output_file: Path):
        """Generate text summary report"""
        summary = report_data["summary"]
        component_analysis = report_data["component_analysis"]

        content = f"""INTEGRATION TEST SUMMARY REPORT
Generated: {report_data["metadata"]["report_generated"]}

OVERALL RESULTS:
Total Tests: {summary["total_tests"]}
Passed: {summary["passed_tests"]}
Failed: {summary["failed_tests"]}
Success Rate: {summary["success_rate"]:.1f}%

COMPONENT BREAKDOWN:
"""

        for component, stats in component_analysis.items():
            content += f"""
{component.upper()}:
  Tests: {stats["total"]} (Passed: {stats["passed"]}, Failed: {stats["failed"]})
  Success Rate: {stats.get("success_rate", 0):.1f}%
  Avg Duration: {stats.get("avg_time", 0):.2f}s
  Avg Cost: ${stats.get("avg_cost", 0):.4f}
  Avg Tokens: {stats.get("avg_tokens", 0):,.0f}
"""

        # Add performance summary
        if "performance_summary" in report_data:
            perf = report_data["performance_summary"]
            if "total_duration" in perf:
                content += f"""
PERFORMANCE SUMMARY:
Total Duration: {perf["total_duration"]:.2f}s
Total Cost: ${perf["total_cost"]:.4f}
Total Tokens: {perf["total_tokens"]:,}
Total API Calls: {perf["total_api_calls"]}
"""

        # Add error summary
        if "error_analysis" in report_data:
            errors = report_data["error_analysis"]
            if errors.get("total_errors", 0) > 0:
                content += f"""
ERROR SUMMARY:
Total Errors: {errors["total_errors"]}
Failure Patterns: {errors.get("failure_patterns", {})}
Most Common Failure: {errors.get("most_common_failure", "None")}
"""

        with open(output_file, "w") as f:
            f.write(content)

    def _render_html_template(self, data: Dict[str, Any]) -> str:
        """Render HTML template with data"""
        # Simple template rendering (could be enhanced with proper templating engine)
        html = self.html_template.format(
            title=data["title"],
            generated_time=data["generated_time"],
            css_styles=self.css_styles,
            js_scripts=self.js_scripts,
            summary_json=json.dumps(data["summary"]),
            component_json=json.dumps(data["component_analysis"]),
            validation_json=json.dumps(data["validation_summary"]),
            performance_json=json.dumps(data["performance_summary"]),
            error_json=json.dumps(data["error_analysis"]),
            debug_json=json.dumps(data["debug_analysis"]),
            include_debug="true" if data["include_debug"] else "false",
            include_performance="true" if data["include_performance"] else "false",
        )
        return html

    def _get_html_template(self) -> str:
        """Get HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="timestamp">Generated: {generated_time}</p>
        </header>
        
        <section class="summary">
            <h2>Test Summary</h2>
            <div id="summary-content"></div>
        </section>
        
        <section class="component-analysis">
            <h2>Component Analysis</h2>
            <div id="component-content"></div>
        </section>
        
        <section class="validation-results">
            <h2>Validation Results</h2>
            <div id="validation-content"></div>
        </section>
        
        <section class="performance-metrics" style="display: {include_performance};">
            <h2>Performance Metrics</h2>
            <div id="performance-content"></div>
        </section>
        
        <section class="debug-data" style="display: {include_debug};">
            <h2>Debug Analysis</h2>
            <div id="debug-content"></div>
        </section>
        
        <section class="error-analysis">
            <h2>Error Analysis</h2>
            <div id="error-content"></div>
        </section>
    </div>
    
    <script>
        const summaryData = {summary_json};
        const componentData = {component_json};
        const validationData = {validation_json};
        const performanceData = {performance_json};
        const errorData = {error_json};
        const debugData = {debug_json};
    </script>
    <script>{js_scripts}</script>
</body>
</html>"""

    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        header h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        
        .timestamp {
            margin: 0.5rem 0 0 0;
            opacity: 0.8;
        }
        
        section {
            background: white;
            margin-bottom: 2rem;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
            margin-top: 0;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .metric-label {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        .chart-container {
            height: 300px;
            margin: 1rem 0;
        }
        
        .error-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 1rem;
            background: #f8f9fa;
        }
        
        .error-item {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #dc3545;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            header h1 {
                font-size: 2rem;
            }
            
            .metric-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
        }
        """

    def _get_js_scripts(self) -> str:
        """Get JavaScript for interactive features"""
        return """
        function renderSummary() {
            const container = document.getElementById('summary-content');
            const data = summaryData;
            
            container.innerHTML = `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value ${data.success_rate >= 80 ? 'success' : data.success_rate >= 60 ? 'warning' : 'error'}">${data.success_rate.toFixed(1)}%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.total_tests}</div>
                        <div class="metric-label">Total Tests</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value success">${data.passed_tests}</div>
                        <div class="metric-label">Passed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value ${data.failed_tests > 0 ? 'error' : 'success'}">${data.failed_tests}</div>
                        <div class="metric-label">Failed</div>
                    </div>
                </div>
            `;
        }
        
        function renderComponentAnalysis() {
            const container = document.getElementById('component-content');
            const data = componentData;
            
            let tableHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th>Tests</th>
                            <th>Success Rate</th>
                            <th>Avg Duration</th>
                            <th>Avg Cost</th>
                            <th>Avg Tokens</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            for (const [component, stats] of Object.entries(data)) {
                const successRate = stats.success_rate || 0;
                const successClass = successRate >= 80 ? 'success' : successRate >= 60 ? 'warning' : 'error';
                
                tableHTML += `
                    <tr>
                        <td><strong>${component}</strong></td>
                        <td>${stats.total} (${stats.passed}/${stats.failed})</td>
                        <td class="${successClass}">${successRate.toFixed(1)}%</td>
                        <td>${(stats.avg_time || 0).toFixed(2)}s</td>
                        <td>$${(stats.avg_cost || 0).toFixed(4)}</td>
                        <td>${(stats.avg_tokens || 0).toLocaleString()}</td>
                    </tr>
                `;
            }
            
            tableHTML += '</tbody></table>';
            container.innerHTML = tableHTML;
        }
        
        function renderValidationResults() {
            const container = document.getElementById('validation-content');
            const data = validationData;
            
            if (data.message) {
                container.innerHTML = `<p>${data.message}</p>`;
                return;
            }
            
            const passRate = data.check_pass_rate || 0;
            const passRateClass = passRate >= 90 ? 'success' : passRate >= 70 ? 'warning' : 'error';
            
            container.innerHTML = `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value ${passRateClass}">${passRate.toFixed(1)}%</div>
                        <div class="metric-label">Check Pass Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.total_checks}</div>
                        <div class="metric-label">Total Checks</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value success">${data.passed_checks}</div>
                        <div class="metric-label">Passed Checks</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value ${data.total_errors > 0 ? 'error' : 'success'}">${data.total_errors}</div>
                        <div class="metric-label">Total Errors</div>
                    </div>
                </div>
                
                <h3>Error Distribution by Severity</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value error">${data.severity_distribution.error || 0}</div>
                        <div class="metric-label">Errors</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value warning">${data.severity_distribution.warning || 0}</div>
                        <div class="metric-label">Warnings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.severity_distribution.info || 0}</div>
                        <div class="metric-label">Info</div>
                    </div>
                </div>
            `;
        }
        
        function renderPerformanceMetrics() {
            const container = document.getElementById('performance-content');
            const data = performanceData;
            
            if (data.message) {
                container.innerHTML = `<p>${data.message}</p>`;
                return;
            }
            
            container.innerHTML = `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">${data.total_duration.toFixed(2)}s</div>
                        <div class="metric-label">Total Duration</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">$${data.total_cost.toFixed(4)}</div>
                        <div class="metric-label">Total Cost</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.total_tokens.toLocaleString()}</div>
                        <div class="metric-label">Total Tokens</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.total_api_calls}</div>
                        <div class="metric-label">API Calls</div>
                    </div>
                </div>
                
                <h3>Averages</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">${data.averages.duration.toFixed(2)}s</div>
                        <div class="metric-label">Avg Duration</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">$${data.averages.cost.toFixed(4)}</div>
                        <div class="metric-label">Avg Cost</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.averages.tokens.toLocaleString()}</div>
                        <div class="metric-label">Avg Tokens</div>
                    </div>
                </div>
            `;
        }
        
        function renderErrorAnalysis() {
            const container = document.getElementById('error-content');
            const data = errorData;
            
            if (data.total_errors === 0) {
                container.innerHTML = '<p class="success">No errors found in test results!</p>';
                return;
            }
            
            let html = `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value error">${data.total_errors}</div>
                        <div class="metric-label">Total Errors</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.most_common_failure || 'None'}</div>
                        <div class="metric-label">Most Common</div>
                    </div>
                </div>
                
                <h3>Failure Patterns</h3>
                <div class="metric-grid">
            `;
            
            for (const [pattern, count] of Object.entries(data.failure_patterns)) {
                html += `
                    <div class="metric-card">
                        <div class="metric-value">${count}</div>
                        <div class="metric-label">${pattern.replace('_', ' ').toUpperCase()}</div>
                    </div>
                `;
            }
            
            html += '</div>';
            
            if (data.error_list.length > 0) {
                html += '<h3>Error Details</h3><div class="error-list">';
                for (const error of data.error_list) {
                    html += `
                        <div class="error-item">
                            <strong>${error.component}:</strong> ${error.error}
                        </div>
                    `;
                }
                html += '</div>';
            }
            
            container.innerHTML = html;
        }
        
        function renderDebugAnalysis() {
            const container = document.getElementById('debug-content');
            const data = debugData;
            
            if (data.message) {
                container.innerHTML = `<p>${data.message}</p>`;
                return;
            }
            
            container.innerHTML = `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">${data.debug_sessions_count}</div>
                        <div class="metric-label">Debug Sessions</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">$${data.total_debug_cost.toFixed(4)}</div>
                        <div class="metric-label">Total Debug Cost</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.total_debug_tokens.toLocaleString()}</div>
                        <div class="metric-label">Total Debug Tokens</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">$${data.average_debug_cost.toFixed(4)}</div>
                        <div class="metric-label">Avg Cost per Session</div>
                    </div>
                </div>
            `;
        }
        
        // Initialize report when page loads
        document.addEventListener('DOMContentLoaded', function() {
            renderSummary();
            renderComponentAnalysis();
            renderValidationResults();
            renderPerformanceMetrics();
            renderErrorAnalysis();
            renderDebugAnalysis();
        });
        """
