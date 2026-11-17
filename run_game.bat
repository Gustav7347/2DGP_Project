@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  set "game_python=python"
) else (
  set "game_python=py -3"
)
%game_python% --version >nul 2>nul
if errorlevel 1 (
  echo Python 3를 설치한 뒤 다시 실행해주세요.
  pause
  exit /b 1
)
%game_python% main.py %*
if errorlevel 1 (
  echo.
  echo 위 오류를 확인해주세요. pico2d가 없으면 이 폴더에서 다음 명령을 실행하세요.
  echo %game_python% -m pip install -r requirements.txt
  pause
  exit /b 1
)
