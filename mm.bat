@echo off
python "%~dp0mew.py" %*

:: %~dp0 → expands to the directory of the .bat file.
:: %* → passes any arguments you type to the Python script.