@echo off
setlocal EnableDelayedExpansion

:: Solicita o saldo
set /p SALDO="Digite seu saldo atual: "

:: Substitui vírgula por ponto, caso exista
set "SALDO=!SALDO:,=.!"

:: Configura o PYTHONPATH
set PYTHONPATH=%~dp0;%PYTHONPATH%

:: Executa o programa
python run_advisor.py -v !SALDO! %*
if !ERRORLEVEL! neq 0 (
    echo Ocorreu um erro ao executar o programa.
    pause
    exit /b 1
)

pause