@echo off
setlocal

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

call .venv\Scripts\activate.bat

echo Updating pip...
python -m pip install --upgrade pip

if not exist requirements.txt (
    echo ERROR: requirements.txt not found. Skipping package installation.
    echo You can manually activate the environment and install packages if needed.
    goto :end
)

echo Installing packages...
python -m pip install -r requirements.txt

:end
echo.
echo =============================
echo SETUP COMPLETED SUCCESSFULLY
echo =============================
echo.
echo Next steps:
echo 1. Activate the virtual environment by running:
echo.
echo     .venv\Scripts\activate
echo.
echo 2. Start the Streamlit app by running:
echo.
echo     streamlit run app.py
echo.
echo Make sure you're in the project's root folder.
echo.
echo --------------------------------------------------
echo You only need to run this setup script once!
echo As long as the ".venv" folder exists, everything
echo stays ready — pip and packages are already set up.
echo Only rerun this script if:
echo  - you delete the .venv folder, OR
echo  - you update requirements.txt
echo --------------------------------------------------
echo.
pause
