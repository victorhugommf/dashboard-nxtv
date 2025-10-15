#!/usr/bin/env python3
"""
Comprehensive Test Runner for Multi-Domain Dashboard
Runs all comprehensive tests including integration, end-to-end, performance, and data isolation tests
Requirements: 7.1, 7.2, 7.3, 7.4
"""

import unittest
import sys
import os
import time
import json
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all comprehensive test modules
from test_comprehensive_multi_domain import (
    TestMultiDomainIntegration,
    TestEndToEndMultiDomain,
    TestPerformanceMultiDomain,
    TestDataIsolationCompliance
)
from test_performance_stress import (
    TestHighLoadPerformance,
    TestStressConditions
)

# Import existing integration tests
from test_integration_multi_domain import TestMultiDomainIntegration as ExistingIntegration
from test_cache_integration import TestCacheIntegration
from test_security_integration import TestSecurityFlaskIntegration


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_category(self, category_name, test_classes):
        """Run a category of tests and collect results"""
        print(f"\n{'='*80}")
        print(f"RUNNING {category_name.upper()} TESTS")
        print(f"{'='*80}")
        
        category_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'execution_time': 0,
            'test_classes': {}
        }
        
        category_start = time.time()
        
        for test_class in test_classes:
            print(f"\nRunning {test_class.__name__}...")
            
            # Create test suite for this class
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            
            # Run tests with custom result collector
            class_start = time.time()
            runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout, buffer=True)
            result = runner.run(suite)
            class_end = time.time()
            
            # Collect results
            class_results = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'execution_time': class_end - class_start,
                'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
            }
            
            category_results['test_classes'][test_class.__name__] = class_results
            category_results['total_tests'] += class_results['tests_run']
            category_results['passed'] += (class_results['tests_run'] - class_results['failures'] - class_results['errors'])
            category_results['failed'] += class_results['failures']
            category_results['errors'] += class_results['errors']
            category_results['skipped'] += class_results['skipped']
            
            print(f"  ✓ {test_class.__name__}: {class_results['tests_run']} tests, "
                  f"{class_results['success_rate']:.1f}% success rate, "
                  f"{class_results['execution_time']:.2f}s")
        
        category_end = time.time()
        category_results['execution_time'] = category_end - category_start
        
        self.test_results[category_name] = category_results
        
        print(f"\n{category_name.upper()} SUMMARY:")
        print(f"  Total Tests: {category_results['total_tests']}")
        print(f"  Passed: {category_results['passed']}")
        print(f"  Failed: {category_results['failed']}")
        print(f"  Errors: {category_results['errors']}")
        print(f"  Execution Time: {category_results['execution_time']:.2f}s")
        
        return category_results['failed'] == 0 and category_results['errors'] == 0
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        self.start_time = time.time()
        
        print("MULTI-DOMAIN DASHBOARD - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print("Testing Requirements:")
        print("  7.1 - Complete data isolation between domains")
        print("  7.2 - Multi-domain simultaneous access")
        print("  7.3 - Performance under concurrent load")
        print("  7.4 - Data isolation compliance verification")
        
        all_passed = True
        
        # Test categories with their respective test classes
        test_categories = [
            ("Integration Tests", [
                TestMultiDomainIntegration,
                ExistingIntegration,
                TestCacheIntegration
            ]),
            ("End-to-End Tests", [
                TestEndToEndMultiDomain
            ]),
            ("Performance Tests", [
                TestPerformanceMultiDomain,
                TestHighLoadPerformance
            ]),
            ("Stress Tests", [
                TestStressConditions
            ]),
            ("Data Isolation Tests", [
                TestDataIsolationCompliance
            ]),
            ("Security Integration Tests", [
                TestSecurityFlaskIntegration
            ])
        ]
        
        # Run each category
        for category_name, test_classes in test_categories:
            try:
                category_passed = self.run_test_category(category_name, test_classes)
                if not category_passed:
                    all_passed = False
            except Exception as e:
                print(f"ERROR in {category_name}: {str(e)}")
                all_passed = False
        
        self.end_time = time.time()
        
        # Generate final report
        self.generate_final_report()
        
        return all_passed
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        total_execution_time = self.end_time - self.start_time
        
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST SUITE - FINAL REPORT")
        print(f"{'='*80}")
        
        # Overall statistics
        total_tests = sum(category['total_tests'] for category in self.test_results.values())
        total_passed = sum(category['passed'] for category in self.test_results.values())
        total_failed = sum(category['failed'] for category in self.test_results.values())
        total_errors = sum(category['errors'] for category in self.test_results.values())
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"OVERALL STATISTICS:")
        print(f"  Total Tests Run: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Errors: {total_errors}")
        print(f"  Success Rate: {overall_success_rate:.1f}%")
        print(f"  Total Execution Time: {total_execution_time:.2f}s")
        
        # Category breakdown
        print(f"\nCATEGORY BREAKDOWN:")
        for category_name, results in self.test_results.items():
            success_rate = (results['passed'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0
            status = "✓ PASS" if results['failed'] == 0 and results['errors'] == 0 else "✗ FAIL"
            
            print(f"  {category_name:25} | {results['total_tests']:3d} tests | {success_rate:5.1f}% | {results['execution_time']:6.2f}s | {status}")
        
        # Requirements compliance
        print(f"\nREQUIREMENTS COMPLIANCE:")
        
        # Requirement 7.1 - Data Isolation
        isolation_categories = ['Integration Tests', 'Data Isolation Tests']
        isolation_passed = all(
            self.test_results.get(cat, {}).get('failed', 1) == 0 and 
            self.test_results.get(cat, {}).get('errors', 1) == 0 
            for cat in isolation_categories
        )
        print(f"  7.1 - Data Isolation: {'✓ COMPLIANT' if isolation_passed else '✗ NON-COMPLIANT'}")
        
        # Requirement 7.2 - Multi-domain Access
        e2e_passed = (
            self.test_results.get('End-to-End Tests', {}).get('failed', 1) == 0 and
            self.test_results.get('End-to-End Tests', {}).get('errors', 1) == 0
        )
        print(f"  7.2 - Multi-domain Access: {'✓ COMPLIANT' if e2e_passed else '✗ NON-COMPLIANT'}")
        
        # Requirement 7.3 - Performance
        perf_categories = ['Performance Tests', 'Stress Tests']
        perf_passed = all(
            self.test_results.get(cat, {}).get('failed', 1) == 0 and 
            self.test_results.get(cat, {}).get('errors', 1) == 0 
            for cat in perf_categories
        )
        print(f"  7.3 - Performance: {'✓ COMPLIANT' if perf_passed else '✗ NON-COMPLIANT'}")
        
        # Requirement 7.4 - Data Isolation Compliance
        compliance_passed = (
            self.test_results.get('Data Isolation Tests', {}).get('failed', 1) == 0 and
            self.test_results.get('Data Isolation Tests', {}).get('errors', 1) == 0
        )
        print(f"  7.4 - Isolation Compliance: {'✓ COMPLIANT' if compliance_passed else '✗ NON-COMPLIANT'}")
        
        # Performance metrics
        if 'Performance Tests' in self.test_results:
            perf_time = self.test_results['Performance Tests']['execution_time']
            print(f"\nPERFORMANCE METRICS:")
            print(f"  Performance Test Execution: {perf_time:.2f}s")
            print(f"  Average Test Time: {total_execution_time / total_tests:.3f}s per test")
        
        # Save detailed report to file
        self.save_detailed_report()
        
        print(f"\n{'='*80}")
        if total_failed == 0 and total_errors == 0:
            print("🎉 ALL TESTS PASSED - MULTI-DOMAIN SYSTEM IS READY FOR PRODUCTION")
        else:
            print("❌ SOME TESTS FAILED - REVIEW ISSUES BEFORE DEPLOYMENT")
        print(f"{'='*80}")
    
    def save_detailed_report(self):
        """Save detailed test report to JSON file"""
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_execution_time': self.end_time - self.start_time,
            'categories': self.test_results,
            'summary': {
                'total_tests': sum(cat['total_tests'] for cat in self.test_results.values()),
                'total_passed': sum(cat['passed'] for cat in self.test_results.values()),
                'total_failed': sum(cat['failed'] for cat in self.test_results.values()),
                'total_errors': sum(cat['errors'] for cat in self.test_results.values())
            }
        }
        
        # Create reports directory if it doesn't exist
        reports_dir = Path(__file__).parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Save report
        report_file = reports_dir / f'comprehensive_test_report_{int(time.time())}.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")


def main():
    """Main entry point for comprehensive test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive multi-domain tests')
    parser.add_argument('--category', choices=[
        'integration', 'e2e', 'performance', 'stress', 'isolation', 'security', 'all'
    ], default='all', help='Test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    import logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    
    runner = ComprehensiveTestRunner()
    
    if args.category == 'all':
        success = runner.run_all_tests()
    else:
        # Run specific category
        category_map = {
            'integration': [TestMultiDomainIntegration, ExistingIntegration, TestCacheIntegration],
            'e2e': [TestEndToEndMultiDomain],
            'performance': [TestPerformanceMultiDomain, TestHighLoadPerformance],
            'stress': [TestStressConditions],
            'isolation': [TestDataIsolationCompliance],
            'security': [TestSecurityFlaskIntegration]
        }
        
        test_classes = category_map.get(args.category, [])
        success = runner.run_test_category(args.category.title() + ' Tests', test_classes)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()