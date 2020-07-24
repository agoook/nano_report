@ECHO OFF
chcp 1251 >nul
ECHO "%~1"
python -m streamlit.cli run nanotubes_tem.py "%~1"
pause