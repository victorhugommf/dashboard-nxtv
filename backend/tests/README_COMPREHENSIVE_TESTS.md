# Comprehensive Multi-Domain Test Suite

This directory contains a comprehensive test suite for the multi-domain dashboard system, covering all aspects of multi-domain functionality, performance, and data isolation.

## Test Coverage

The comprehensive test suite addresses the following requirements:

- **7.1** - Complete data isolation between domains
- **7.2** - Multi-domain simultaneous access  
- **7.3** - Performance under concurrent load
- **7.4** - Data isolation compliance verification

## Test Structure

### Core Test Files

#### `test_comprehensive_multi_domain.py`
Main comprehensive test suite containing:

- **TestMultiDomainIntegration**: Integration tests for multi-domain functionality
  - Complete data isolation verification
  - Cache isolation between domains
  - Theme isolation verification

- **TestEndToEndMultiDomain**: End-to-end tests with multiple domains
  - Simultaneous multi-domain requests
  - Complete data flow verification
  - Error isolation between domains

- **TestPerformanceMultiDomain**: Performance tests for concurrent access
  - Concurrent domain access performance
  - Cache performance under load
  - Memory usage optimization

- **TestDataIsolationCompliance**: Strict data isolation compliance tests
  - Sensitive data isolation (banking example)
  - Cache key isolation verification
  - Error message isolation
  - Concurrent access isolation

#### `test_performance_stress.py`
Performance and stress testing:

- **TestHighLoadPerformance**: High load performance tests
  - High concurrency data fetching
  - Cache performance under stress
  - Memory usage under load

- **TestStressConditions**: Stress condition testing
  - Rapid cache expiration stress
  - Concurrent domain switching
  - Error recovery stress testing

#### `run_comprehensive_tests.py`
Comprehensive test runner with detailed reporting:
- Runs all test categories
- Generates detailed performance reports
- Validates requirements compliance
- Saves test results to JSON files

#### `test_validation.py`
Test validation and setup verification:
- Validates test imports
- Checks dependencies
- Verifies backend modules
- Runs basic functionality tests

## Running Tests

### Prerequisites

Ensure all dependencies are installed:
```bash
pip install pandas psutil
```

### Validation

First, validate that all tests can run:
```bash
cd backend/tests
python test_validation.py
```

### Running All Tests

Run the complete comprehensive test suite:
```bash
python run_comprehensive_tests.py
```

### Running Specific Categories

Run specific test categories:
```bash
# Integration tests only
python run_comprehensive_tests.py --category integration

# Performance tests only  
python run_comprehensive_tests.py --category performance

# End-to-end tests only
python run_comprehensive_tests.py --category e2e

# Stress tests only
python run_comprehensive_tests.py --category stress

# Data isolation tests only
python run_comprehensive_tests.py --category isolation

# Security integration tests only
python run_comprehensive_tests.py --category security
```

### Verbose Output

Run with verbose output for debugging:
```bash
python run_comprehensive_tests.py --verbose
```

### Running Individual Test Files

Run individual test files directly:
```bash
# Comprehensive multi-domain tests
python -m unittest test_comprehensive_multi_domain -v

# Performance and stress tests
python -m unittest test_performance_stress -v

# Existing integration tests
python -m unittest test_integration_multi_domain -v
```

## Test Reports

### Console Output

The test runner provides detailed console output including:
- Real-time test execution status
- Category-wise results summary
- Overall statistics and success rates
- Requirements compliance verification
- Performance metrics

### JSON Reports

Detailed test reports are saved to `reports/` directory:
- Timestamp-based filenames
- Complete test execution data
- Performance metrics
- Category breakdowns
- Requirements compliance status

## Test Categories Explained

### Integration Tests (Requirement 7.1)
- Verify complete data isolation between domains
- Test cache isolation mechanisms
- Validate theme and configuration isolation
- Ensure no cross-domain data leakage

### End-to-End Tests (Requirement 7.2)
- Test simultaneous access to multiple domains
- Verify complete workflow functionality
- Test error isolation between domains
- Validate concurrent multi-domain operations

### Performance Tests (Requirement 7.3)
- Measure performance under concurrent load
- Test cache efficiency with multiple domains
- Monitor memory usage and optimization
- Validate response times under stress

### Data Isolation Tests (Requirement 7.4)
- Strict compliance verification for sensitive data
- Test isolation with banking/financial scenarios
- Verify cache key isolation mechanisms
- Test error message isolation
- Validate concurrent access isolation

### Stress Tests
- High load performance testing
- Rapid cache expiration scenarios
- Concurrent domain switching stress
- Error recovery and resilience testing

## Performance Benchmarks

The test suite includes performance benchmarks:

- **Concurrent Access**: Tests with up to 50 concurrent requests
- **Memory Usage**: Monitors memory consumption under load
- **Cache Performance**: Tests cache hit/miss ratios and response times
- **Error Recovery**: Tests system resilience under failure conditions

## Expected Results

### Success Criteria

All tests should pass with:
- 100% data isolation between domains
- Sub-second response times for most operations
- Memory usage under 500MB for high-load scenarios
- 90%+ success rate under stress conditions
- Zero cross-domain data leakage

### Performance Targets

- **Concurrent Requests**: Handle 50+ concurrent requests in <10 seconds
- **Cache Operations**: 1000+ cache operations in <5 seconds  
- **Memory Efficiency**: <500MB for 10 domains with large datasets
- **Error Recovery**: 90%+ success rate with 30% simulated error rate

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure backend modules are in Python path
2. **Missing Dependencies**: Install pandas, psutil, and other requirements
3. **Permission Errors**: Ensure write access to reports directory
4. **Memory Issues**: Reduce test dataset sizes for resource-constrained environments

### Debug Mode

Run with verbose logging for debugging:
```bash
python run_comprehensive_tests.py --verbose
```

### Individual Test Debugging

Run specific test methods for focused debugging:
```bash
python -m unittest test_comprehensive_multi_domain.TestMultiDomainIntegration.test_complete_data_isolation_between_domains -v
```

## Continuous Integration

The comprehensive test suite is designed for CI/CD integration:

- Exit codes: 0 for success, 1 for failure
- JSON report generation for CI parsing
- Configurable verbosity levels
- Category-specific test execution
- Performance regression detection

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Include appropriate requirement references in docstrings
3. Add performance benchmarks for new functionality
4. Update this README with new test descriptions
5. Ensure tests are isolated and don't affect other tests

## Requirements Mapping

| Requirement | Test Files | Test Classes |
|-------------|------------|--------------|
| 7.1 - Data Isolation | `test_comprehensive_multi_domain.py` | `TestMultiDomainIntegration`, `TestDataIsolationCompliance` |
| 7.2 - Multi-domain Access | `test_comprehensive_multi_domain.py` | `TestEndToEndMultiDomain` |
| 7.3 - Performance | `test_comprehensive_multi_domain.py`, `test_performance_stress.py` | `TestPerformanceMultiDomain`, `TestHighLoadPerformance` |
| 7.4 - Isolation Compliance | `test_comprehensive_multi_domain.py` | `TestDataIsolationCompliance` |