# Café 77 — Kitchen Request Demo

## How to run

### Windows
Double-click `START.bat`

### Mac / Linux
```
pip install flask "qrcode[pil]"
python app.py
```

## What happens
1. Server starts and prints your PC's local IP + port
2. Open browser on your PC → http://localhost:5077
3. You'll see QR codes for 3 outlets on the dashboard
4. Scan any QR with your phone (must be on same WiFi)
5. Select items and submit on your phone
6. Watch the transfer appear on the PC dashboard in real time

## Outlets in this demo
- Outlet 1 — Colombo 3
- Outlet 2 — Colombo 5
- Outlet 3 — Colombo 7

Each outlet has its own QR code and its own regular item list.
Staff can also search for other kitchen items from the portal.

## Files
- app.py              — Flask server + SQLite database logic
- templates/
  - dashboard.html    — PC live dashboard
  - portal.html       — Mobile request portal (what staff see)
- static/qr/          — QR code images (auto-generated on startup)
- cafe77.db           — SQLite database (auto-created on startup)
