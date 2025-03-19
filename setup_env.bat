@echo off

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not added to PATH.
    echo Please install Python and restart the terminal.
    exit /b 1
)

if not exist .venv (
    echo Virtual environment not found, creating one...
    python -m venv .venv
)

if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

echo Updating pip...
python -m pip install --upgrade pip

if not exist requirements.txt (
    echo ERROR: requirements.txt not found. Skipping package installation.
    exit /b 1
)

echo Installing packages...
pip install -r requirements.txt

echo Setup completed successfully!