# VS Code Setup Guide

## Fixing Import Errors in VS Code

The import errors you're seeing are because VS Code is using a different Python interpreter than the one where we installed the packages. Here's how to fix it:

### Step 1: Select the Correct Python Interpreter

1. **Open VS Code** in your Protein App folder
2. **Press `Ctrl+Shift+P`** to open the command palette
3. **Type "Python: Select Interpreter"** and select it
4. **Choose the virtual environment interpreter**:
   - Look for: `./venv/Scripts/python.exe` or `venv/bin/python`
   - It should show something like: `Python 3.x.x ('venv': venv)`

### Step 2: Verify the Selection

1. **Check the bottom-left corner** of VS Code
2. **You should see** something like: `Python 3.x.x ('venv': venv)`
3. **If you see a different Python version**, repeat Step 1

### Step 3: Reload VS Code

1. **Press `Ctrl+Shift+P`** again
2. **Type "Developer: Reload Window"** and select it
3. **Wait for VS Code to reload**

### Step 4: Verify the Fix

After reloading, the import errors should disappear:
- ✅ `Import "google.oauth2" could not be resolved` - should be gone
- ✅ `Import "dotenv" could not be resolved` - should be gone

### Alternative: Manual Interpreter Selection

If the automatic selection doesn't work:

1. **Press `Ctrl+Shift+P`**
2. **Type "Python: Select Interpreter"**
3. **Click "Enter interpreter path..."**
4. **Enter the full path**: `C:\Users\MSI\Desktop\Protein App\venv\Scripts\python.exe`

### Troubleshooting

If you still see errors:

1. **Make sure the virtual environment is activated** in your terminal:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

2. **Check that packages are installed**:
   ```bash
   pip list | findstr google
   pip list | findstr dotenv
   ```

3. **Restart VS Code completely** and try again

### Why This Happens

- VS Code was using your system Python interpreter
- We installed packages in a virtual environment
- VS Code needs to use the same interpreter where packages are installed

### For Future Development

Always activate the virtual environment before working:
```bash
.\venv\Scripts\Activate.ps1
```

This ensures you're using the correct Python environment with all the required packages.
