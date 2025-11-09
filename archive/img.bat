@echo off
python "%~dp0img.py" %*

:: %~dp0 → expands to the directory of the .bat file.
:: %* → passes any arguments you type to the Python script.