# Testing Guide - DJs Timeline-maskin

This guide explains how to effectively use the comprehensive test suite (120 tests) in your daily development workflow.

## Test Suite Overview

Your project has **120 tests** organized in two main categories:

### Phase 1: Autonomous Tests (115 tests)
- **Runtime**: ~2 seconds
- **User involvement**: Zero
- **Purpose**: Catch bugs early, verify core functionality
- **Files**: `test_filename_parser.py`, `test_pdf_processor.py`, `test_excel_manager.py`, `test_config.py`

### Phase 2: Semi-Autonomous Integration Tests (5 tests)
- **Runtime**: ~1-2 seconds  
- **User involvement**: Review detailed output
- **Purpose**: Verify complete workflows work correctly
- **File**: `test_integration_workflows.py`

## Daily Development Workflow

### Before Making Changes
```bash
# Ensure current state is stable
cd "C:\Dropbox\Dokument\Python\APP DJs Timeline-maskin\DJs Timeline-maskin (projekt)"
python -m pytest tests/ -v
ruff check . --fix
```

### After Making Changes

**1. Quick feedback (run relevant subset first):**
```bash
# If you changed filename parsing logic
python -m pytest tests/test_filename_parser.py -v

# If you changed PDF operations  
python -m pytest tests/test_pdf_processor.py -v

# If you changed Excel operations (safe tests only)
python -m pytest tests/test_excel_manager.py -v

# If you changed configuration management
python -m pytest tests/test_config.py -v
```

**2. Full verification:**
```bash
# Run all autonomous tests
python -m pytest tests/ -v --tb=short

# Run integration tests with detailed output
python -m pytest tests/test_integration_workflows.py -v -s
```

### Before Committing Changes
```bash
# Always run full test suite before commit
python -m pytest tests/ -v
ruff check . --fix

# If all tests pass, commit with confidence
git add .
git commit -m "v2.2.3 Your change description"
```

## Specific Use Cases

### When Adding New Features

1. **Start with stable baseline:**
   ```bash
   python -m pytest tests/test_integration_workflows.py::TestIntegrationWorkflows::test_end_to_end_pdf_workflow -v -s
   ```

2. **Develop and test your feature**

3. **Verify no regressions:**
   ```bash
   python -m pytest tests/ -v
   ```

### When Fixing Bugs

1. **Run specific test to reproduce issue:**
   ```bash
   # Example for PDF corruption bug
   python -m pytest tests/test_pdf_processor.py::TestPDFProcessor::test_validate_pdf_file_corrupted -v
   ```

2. **Fix the bug**

3. **Verify fix and check for regressions:**
   ```bash
   python -m pytest tests/test_pdf_processor.py -v
   python -m pytest tests/test_integration_workflows.py -v -s
   ```

### Before Releasing to Users

```bash
# Comprehensive verification
python -m pytest tests/ -v --tb=short

# Manual review of integration workflows
python -m pytest tests/test_integration_workflows.py -v -s
# Review all output carefully to ensure workflows behave correctly
```

## Integration Test Output Guide

The Phase 2 integration tests provide detailed output for manual verification:

### 1. PDF Filename Parsing Workflow
**What to review:**
- Realistic Swedish newspaper filenames parse correctly
- ALL-CAPS newspapers (like "AFTONBLADET PLUS") handled properly
- Date extraction works for various formats
- Page count parsing is accurate

### 2. PDF Processing Workflow  
**What to review:**
- Normal PDFs: Should show correct page counts
- Encrypted PDFs: Should return 0 pages safely
- Corrupted PDFs: Should show warning with error handling
- Large PDFs: Should handle many pages efficiently

### 3. Configuration Persistence Workflow
**What to review:**
- Swedish characters (åäö) preserved correctly in JSON
- Complex nested data structures save/load properly
- Locked fields functionality works as expected

### 4. Excel Data Preparation Workflow
**What to review:**
- User data takes priority over PDF data when provided
- Empty fields get filled with PDF information automatically
- Date parsing creates proper datetime objects
- Filename integration into Händelse field works correctly

### 5. End-to-End PDF Workflow
**What to review:**
- Complete user workflow from PDF → Excel → Config works
- Swedish characters handled throughout the process
- Date serialization for JSON configuration works
- All workflow steps complete successfully

## Test Safety Notes

### ✅ What the tests DO test:
- Core business logic
- File validation and parsing
- Configuration management  
- Data preparation logic
- Cross-platform compatibility
- Swedish character support

### ⚠️ What the tests AVOID:
- **Hybrid Excel I/O methods** (per your requirements)
- Actual file writing operations
- GUI interactions
- Real PDF file operations

This ensures tests run safely without affecting your working code or files.

## Error Diagnosis

### Common Test Failures and Solutions

**All tests fail with import errors:**
```bash
# Ensure you're in the correct directory
cd "C:\Dropbox\Dokument\Python\APP DJs Timeline-maskin\DJs Timeline-maskin (projekt)"
```

**Unicode display issues in Windows console:**
- Tests automatically handle this - output uses plain text instead of Unicode symbols

**Specific module test failures:**
- Run with `-v` flag for detailed output
- Use `--tb=short` for concise error messages
- Check if your changes affected the tested functionality

## Future Testing Strategy

### Phase 3: Manual Verification Tests (Not yet implemented)
**Could include:**
- Visual/layout testing with real GUI interactions
- Error scenario testing with corrupted files
- Cross-platform testing procedures

### Mixin Testing (Partially planned)
**Could add:**
- PDF Operations Mixin tests
- Excel Operations Mixin tests  
- Event Handlers tests
- Undo/Redo functionality tests

### Real-World Data Testing
**You can add:**
- Tests with your actual PDF files
- Tests with your Excel templates
- Configuration scenarios from real usage

## IDE Integration

**VS Code:**
- Python extension provides test explorer
- Click individual tests to run them
- Built-in test debugging

**PyCharm:**
- Right-click test files → "Run pytest"
- Integrated test runner with results

**Command Line:**
- Always available with `python -m pytest`
- Most reliable and complete output

## Best Practices

1. **Run tests frequently** - catch issues early
2. **Review integration test output** - ensure workflows work correctly  
3. **Use Ruff before commits** - maintain code quality
4. **Test on actual data periodically** - verify real-world scenarios
5. **Add tests for new features** - maintain coverage
6. **Never modify hybrid Excel methods** - tests deliberately avoid these

## Quick Reference Commands

```bash
# Full test suite (daily development)
python -m pytest tests/ -v

# Integration tests only (before releases)  
python -m pytest tests/test_integration_workflows.py -v -s

# Specific module (targeted testing)
python -m pytest tests/test_filename_parser.py -v

# Code quality check
ruff check . --fix

# Silent run (just pass/fail)
python -m pytest tests/ -q

# With coverage (if needed)
python -m pytest tests/ --cov=core
```

This test suite gives you confidence to refactor, add features, and fix bugs while maintaining the stability and quality of your journalism timeline application.