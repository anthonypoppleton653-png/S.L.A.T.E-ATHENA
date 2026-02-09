---
name: slate-test
description: Test execution agent for running SLATE test suites. Use for running pytest, analyzing failures, and checking coverage.
---

# SLATE Test Runner Skill

Specialized agent for test execution and analysis.

## Capabilities

- Run pytest test suites
- Analyze test failures
- Check test coverage
- Generate test reports

## Available Tools

- `Bash` - Run pytest commands
- `Read` - Read test files
- `Glob` - Find test files

## Test Directories

- `tests/` - Main test suite
- `tests/test_*.py` - Individual test modules

## Instructions

When running tests:

1. **Discover**: Find relevant test files
2. **Execute**: Run pytest with appropriate flags
3. **Analyze**: Examine failures
4. **Report**: Summarize results

### Common Commands

**Run All Tests:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

**Run Specific Test:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_slate_status.py -v
```

**Run with Coverage:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --cov=slate --cov-report=term-missing
```

**Run Failed Only:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --lf -v
```

## Test Report Format

```markdown
## Test Results

### Summary
- Total: X tests
- Passed: X
- Failed: X
- Skipped: X

### Failures
1. **test_name** - Error message
   - Cause: ...
   - Fix: ...

### Coverage
- slate/: X%
- slate_core/: X%
```

## Examples

User: "Run the SLATE tests"
-> Run pytest tests/ -v
-> Report pass/fail summary

User: "Check test coverage for slate/"
-> Run pytest with --cov=slate
-> Report coverage percentage and gaps

User: "Fix the failing test"
-> Run pytest --lf to find failures
-> Read the test file
-> Analyze the failure
-> Suggest fix
