#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Comprehensive Test Suite Runner for Multi-Step LLM Pipeline

Runs:
- Unit tests for all Lambda handlers
- Integration tests for complete workflows
- Performance and scalability tests
- Security validation tests
- Architecture compliance validation
- Test coverage analysis
- Generates detailed reports
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time

def run_command(cmd, timeout=300):
    """Run command with timeout and return results"""
    print(f"🔄 Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Completed in {duration:.1f}s")
            return True, result.stdout, result.stderr
        else:
            print(f"❌ Failed in {duration:.1f}s (exit code: {result.returncode})")
            print(f"Error: {result.stderr}")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout after {timeout}s")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False, "", str(e)

def run_unit_tests():
    """Run unit tests for Lambda handlers and core components"""
    print("\n" + "="*80)
    print("🧪 RUNNING UNIT TESTS")
    print("="*80)
    
    test_files = [
        "tests/test_lambda_handler.py",
        "tests/test_research_analyzer.py", 
        "tests/test_jobs_researcher.py",
        "tests/test_cluster_jtbd.py",
        "tests/test_value_curve_mapper.py",
        "tests/test_product_idea_generator.py",
        "tests/test_idea_consolidator.py",
        "tests/test_github_integration.py"
    ]
    
    # Filter to only existing test files
    existing_tests = [t for t in test_files if Path(t).exists()]
    
    if not existing_tests:
        print("❌ No unit test files found")
        return False
    
    cmd = [
        sys.executable, "-m", "pytest",
        "-v", "--tb=short",
        "-m", "unit or not slow",  # Run unit tests, exclude slow tests
        "--maxfail=5"
    ] + existing_tests
    
    success, stdout, stderr = run_command(cmd, timeout=180)
    
    if success:
        print("✅ Unit tests PASSED")
    else:
        print("❌ Unit tests FAILED")
        print(stderr)
    
    return success

def run_integration_tests():
    """Run integration tests for complete workflows"""
    print("\n" + "="*80)  
    print("🔗 RUNNING INTEGRATION TESTS")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_integration_e2e.py",
        "-v", "--tb=short",
        "-m", "integration",
        "--maxfail=3"
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=300)
    
    if success:
        print("✅ Integration tests PASSED")
    else:
        print("❌ Integration tests FAILED")
        print(stderr)
    
    return success

def run_serverless_tests():
    """Run serverless architecture specific tests"""
    print("\n" + "="*80)
    print("🏗️  RUNNING SERVERLESS ARCHITECTURE TESTS")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_serverless_architecture.py",
        "tests/test_lambda_handler.py",
        "-v", "--tb=short",
        "--maxfail=5"
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=240)
    
    if success:
        print("✅ Serverless architecture tests PASSED")
    else:
        print("❌ Serverless architecture tests FAILED")
        print(stderr)
    
    return success

def run_performance_tests():
    """Run performance and scalability tests"""
    print("\n" + "="*80)
    print("⚡ RUNNING PERFORMANCE TESTS")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_performance_scalability.py",
        "-v", "--tb=short",
        "-m", "not stress",  # Exclude stress tests for regular runs
        "--maxfail=3"
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=300)
    
    if success:
        print("✅ Performance tests PASSED")
    else:
        print("❌ Performance tests FAILED") 
        print(stderr)
    
    return success

def run_security_tests():
    """Run security validation tests"""
    print("\n" + "="*80)
    print("🔒 RUNNING SECURITY VALIDATION TESTS") 
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_security_validation.py",
        "-v", "--tb=short",
        "-m", "security",
        "--maxfail=5"
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=240)
    
    if success:
        print("✅ Security tests PASSED")
    else:
        print("❌ Security tests FAILED")
        print(stderr)
    
    return success

def run_coverage_analysis():
    """Run test coverage analysis"""
    print("\n" + "="*80)
    print("📊 RUNNING COVERAGE ANALYSIS")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=html:test_reports/coverage_html",
        "--cov-report=json:test_reports/coverage.json",
        "--cov-report=term-missing",
        "--cov-fail-under=60",  # Lower threshold for serverless tests
        "-v", "--tb=short",
        "-m", "not slow and not stress"  # Exclude slow/stress tests
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=600)
    
    if success:
        print("✅ Coverage analysis COMPLETED")
        # Extract coverage percentage from output
        for line in stdout.split('\n'):
            if 'TOTAL' in line and '%' in line:
                print(f"📈 {line.strip()}")
    else:
        print("❌ Coverage analysis FAILED")
        print(stderr)
    
    return success

def run_stress_tests():
    """Run stress tests (optional, for comprehensive validation)"""
    print("\n" + "="*80)
    print("💪 RUNNING STRESS TESTS (Optional)")
    print("="*80)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_performance_scalability.py",
        "-v", "--tb=short", 
        "-m", "stress",
        "--maxfail=2"
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=600)
    
    if success:
        print("✅ Stress tests PASSED")
    else:
        print("❌ Stress tests FAILED (this may be expected)")
        print(stderr)
    
    return success

def generate_validation_report():
    """Generate comprehensive validation report"""
    print("\n" + "="*80)
    print("📄 GENERATING VALIDATION REPORT")
    print("="*80)
    
    try:
        # Ensure test_reports directory exists
        Path("test_reports").mkdir(exist_ok=True)
        
        # Import and run validation reporter
        sys.path.append('.')
        from tests.test_validation_report import ValidationReporter
        
        reporter = ValidationReporter("test_reports")
        results = reporter.run_full_validation()
        
        print("✅ Validation report generated successfully")
        print(f"📄 HTML Report: {results['html_report']}")
        print(f"📄 JSON Report: {results['json_report']}")
        
        return True, results
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False, None

def main():
    """Main test execution function"""
    parser = argparse.ArgumentParser(description="Run comprehensive test validation suite")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--serverless", action="store_true", help="Run serverless tests only")  
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--coverage", action="store_true", help="Run coverage analysis only")
    parser.add_argument("--stress", action="store_true", help="Run stress tests only")
    parser.add_argument("--report", action="store_true", help="Generate report only")
    parser.add_argument("--fast", action="store_true", help="Run fast test suite (unit + serverless)")
    parser.add_argument("--full", action="store_true", help="Run full test suite including stress tests")
    
    args = parser.parse_args()
    
    print("🚀 Multi-Step LLM Pipeline - Comprehensive Test Validation")
    print("="*80)
    print(f"📅 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Track results
    results = {}
    total_start = time.time()
    
    # Determine which tests to run
    if args.fast:
        test_suite = ["unit", "serverless", "coverage"]
    elif args.full:
        test_suite = ["unit", "integration", "serverless", "performance", "security", "coverage", "stress"]
    elif any([args.unit, args.integration, args.serverless, args.performance, args.security, args.coverage, args.stress, args.report]):
        test_suite = []
        if args.unit: test_suite.append("unit")
        if args.integration: test_suite.append("integration") 
        if args.serverless: test_suite.append("serverless")
        if args.performance: test_suite.append("performance")
        if args.security: test_suite.append("security")
        if args.coverage: test_suite.append("coverage")
        if args.stress: test_suite.append("stress")
        if args.report: test_suite.append("report")
    else:
        # Default test suite (excluding stress tests)
        test_suite = ["unit", "serverless", "performance", "security", "coverage"]
    
    print(f"🎯 Running test suite: {', '.join(test_suite)}")
    print()
    
    # Run selected tests
    if "unit" in test_suite:
        results["unit"] = run_unit_tests()
    
    if "integration" in test_suite:
        results["integration"] = run_integration_tests()
        
    if "serverless" in test_suite:
        results["serverless"] = run_serverless_tests()
    
    if "performance" in test_suite:
        results["performance"] = run_performance_tests()
    
    if "security" in test_suite:
        results["security"] = run_security_tests()
        
    if "coverage" in test_suite:
        results["coverage"] = run_coverage_analysis()
    
    if "stress" in test_suite:
        results["stress"] = run_stress_tests()
    
    # Generate comprehensive report
    if "report" in test_suite or len(test_suite) > 2:
        report_success, report_results = generate_validation_report()
        results["report"] = report_success
    
    # Summary
    total_time = time.time() - total_start
    passed_tests = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    print("\n" + "="*80)
    print("🏁 TEST VALIDATION SUMMARY")
    print("="*80)
    print(f"⏱️  Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"✅ Passed: {passed_tests}/{total_tests} test suites")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests} test suites")
    print()
    
    # Detailed results
    for test_type, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_type.title()} Tests")
    
    print("="*80)
    
    # Exit with appropriate code
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print("💥 SOME TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()