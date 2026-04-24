@echo off
echo.
echo  Cafe 77 - Kitchen Request Demo
echo  ================================
echo  Installing dependencies...
pip install flask qrcode[pil] --quiet --break-system-packages 2>nul || pip install flask qrcode[pil] --quiet
echo  Starting server...
echo.
python app.py
pause
