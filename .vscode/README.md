# VS Code Configuration

This directory contains VS Code configuration files for the ActivityWatch project.

## Files

- **settings.json** - Workspace settings including pytest configuration
- **launch.json** - Debug configurations for running and debugging tests
- **tasks.json** - Task definitions for common test operations
- **extensions.json** - Recommended VS Code extensions

## Quick Start

1. **Open the project in VS Code**
2. **Install recommended extensions** (VS Code will prompt you)
3. **Open a test file** (e.g., `tests/test_api.py`)
4. **Click "Run Test"** above any test function

## Features

### Test Discovery
- Automatic test discovery when opening test files
- Test icons (▶️) appear next to test functions
- Test Explorer panel shows all tests organized by file

### Running Tests
- Click "Run Test" / "Debug Test" buttons above functions
- Use Test Explorer panel for bulk operations
- Command Palette: "Python: Run All Tests"
- Tasks: Predefined test runs (Run All Tests, Run API Tests, etc.)

### Debugging
- Set breakpoints in tests or code
- Use F5 to start debugging
- Multiple debug configurations available:
  - Debug current test file
  - Debug all tests
  - Debug specific test suites

### Tasks
- Run All Tests
- Run API Tests
- Run WebUI Tests
- Run Integration Tests
- Run Tests with Coverage
- Install Test Dependencies

## Configuration Details

### settings.json
- Enables pytest testing framework
- Configures test discovery
- Sets up Python paths
- Configures auto-test discovery on save

### launch.json
- Debug configurations for different test scenarios
- Proper environment variable setup
- Python path configuration

### tasks.json
- Shell tasks for running tests
- Integration with VS Code's task system
- Can be run from Command Palette

## Troubleshooting

If tests aren't discovered:
1. Check Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Verify pytest is installed: `python3 -m pytest --version`

For more details, see `tests/VSCODE_SETUP.md`.

