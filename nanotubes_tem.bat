@ECHO OFF
chcp 1251 >nul
CALL d:\tmp\venvs\nano\Scripts\activate.bat
python -m streamlit.cli run nanotubes_tem.py
pause