# Pytest Setup for VS Code

This guide explains how to use pytest from VS Code after the configuration updates.

## Quick Start

1. **Reload VS Code Window**
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Developer: Reload Window" and press Enter
   - This ensures VS Code picks up the new configuration

2. **Select Python Interpreter**
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Python: Select Interpreter"
   - Choose `.venv/bin/python` from the list
   - VS Code should now use the virtual environment

3. **Open a Test File**
   - Navigate to any test file (e.g., `tests/api/test_api.py`)
   - You should see "Run Test" buttons (▶️) above each test function
   - The Test Explorer panel should appear in the sidebar

## Using the Test Explorer

1. **Open Test Explorer**
   - Click the beaker/flask icon in the sidebar
   - Or press `Cmd+Shift+P` → "Test: Focus on Test View"

2. **Run Tests**
   - Click the play button (▶️) next to any test
   - Right-click for more options (Run, Debug, etc.)
   - Use the play button at the top to run all tests

## Running Tests from Code

1. **Run Individual Test**
   - Click "Run Test" above any test function
   - Or right-click on the test name → "Run Test"

2. **Debug Test**
   - Click "Debug Test" above any test function
   - Or right-click → "Debug Test"
   - Set breakpoints and use the debugger

## Using Tasks

1. **Open Tasks**
   - Press `Cmd+Shift+P` → "Tasks: Run Task"
   - Select from:
     - "Run All Tests"
     - "Run API Tests"
     - "Run WebUI Tests"
     - "Run Integration Tests"
     - "Run Tests with Coverage"
     - "Install Test Dependencies"

2. **Keyboard Shortcut**
   - Press `Cmd+Shift+P` → "Tasks: Run Test Task"
   - Or use the default test task shortcut

## Troubleshooting

### Tests Not Discovered

1. **Check Python Interpreter**
   - Bottom-right corner should show `.venv/bin/python`
   - If not, select it using "Python: Select Interpreter"

2. **Verify Virtual Environment**
   - Ensure `.venv` directory exists
   - Check that pytest is installed: `.venv/bin/pytest --version`

3. **Reload Window**
   - `Cmd+Shift+P` → "Developer: Reload Window"

4. **Check Output**
   - View → Output → Select "Python Test Log"
   - Look for any error messages

### Pytest Not Found

If VS Code can't find pytest:

1. **Verify Installation**
   ```bash
   source .venv/bin/activate
   pytest --version
   ```

2. **Reinstall if Needed**
   ```bash
   source .venv/bin/activate
   pip install -r tests/requirements.txt
   ```

3. **Check Settings**
   - `.vscode/settings.json` should have:
     - `"python.testing.pytestPath": "${workspaceFolder}/.venv/bin/pytest"`
     - `"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"`

### Database Connection Errors

The 24 database connection errors are expected if:
- Docker services aren't running
- Database credentials don't match `.env` file
- Database isn't accessible from host

To fix:
1. Start Docker services: `docker-compose up -d`
2. Verify `.env` file has correct credentials
3. Wait 30-60 seconds for services to initialize

## Configuration Files

- **`.vscode/settings.json`** - VS Code workspace settings
- **`.vscode/launch.json`** - Debug configurations
- **`.vscode/tasks.json`** - Task definitions
- **`pytest.ini`** - Pytest configuration
- **`tests/conftest.py`** - Pytest fixtures

## Features Enabled

✅ Automatic test discovery on save  
✅ Test Explorer panel  
✅ Run/Debug buttons above tests  
✅ Code coverage support  
✅ Debugging with breakpoints  
✅ Task integration  
✅ Virtual environment support  

## Next Steps

1. Reload VS Code window
2. Select the virtual environment interpreter
3. Open a test file and start testing!

