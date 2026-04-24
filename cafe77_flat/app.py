import os, json, secrets, io, threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
import qrcode

app = Flask(__name__)

_transfers = []
_lock = threading.Lock()
_next_id = [1]

def insert_transfer(ref, outlet_id, outlet_name, items, note):
    with _lock:
        row = {
            "id": _next_id[0], "ref": ref, "outlet_id": outlet_id,
            "outlet_name": outlet_name, "items_json": json.dumps(items),
            "note": note or "", "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _transfers.append(row)
        _next_id[0] += 1
        return row

def all_transfers():
    with _lock:
        return list(reversed(_transfers))

def update_status(tid, status):
    with _lock:
        for t in _transfers:
            if t["id"] == tid:
                t["status"] = status

OUTLETS = [
    {"id": "outlet-1", "name": "Outlet 1 — Colombo 3", "token": "tok-o1-cafe77"},
    {"id": "outlet-2", "name": "Outlet 2 — Colombo 5", "token": "tok-o2-cafe77"},
    {"id": "outlet-3", "name": "Outlet 3 — Colombo 7", "token": "tok-o3-cafe77"},
]

OUTLET_PRODUCTS = {
    "outlet-1": [
        {"id": "p1", "name": "Egg salad sandwich", "unit": "pcs"},
        {"id": "p2", "name": "Club sandwich",      "unit": "pcs"},
        {"id": "p3", "name": "Iced coffee base",   "unit": "litres"},
    ],
    "outlet-2": [
        {"id": "p2", "name": "Club sandwich",      "unit": "pcs"},
        {"id": "p4", "name": "Chicken rice box",   "unit": "boxes"},
        {"id": "p5", "name": "Chocolate mousse",   "unit": "cups"},
    ],
    "outlet-3": [
        {"id": "p1", "name": "Egg salad sandwich", "unit": "pcs"},
        {"id": "p4", "name": "Chicken rice box",   "unit": "boxes"},
        {"id": "p6", "name": "Mango lassi base",   "unit": "litres"},
        {"id": "p7", "name": "Lemon tart",         "unit": "pcs"},
    ],
}

ALL_PRODUCTS = [
    {"id": "p1",  "name": "Egg salad sandwich", "unit": "pcs"},
    {"id": "p2",  "name": "Club sandwich",       "unit": "pcs"},
    {"id": "p3",  "name": "Iced coffee base",    "unit": "litres"},
    {"id": "p4",  "name": "Chicken rice box",    "unit": "boxes"},
    {"id": "p5",  "name": "Chocolate mousse",    "unit": "cups"},
    {"id": "p6",  "name": "Mango lassi base",    "unit": "litres"},
    {"id": "p7",  "name": "Lemon tart",          "unit": "pcs"},
    {"id": "p8",  "name": "Tomato soup",         "unit": "litres"},
    {"id": "p9",  "name": "Garlic bread",        "unit": "pcs"},
    {"id": "p10", "name": "Caesar salad",        "unit": "portions"},
    {"id": "p11", "name": "Pasta bolognese",     "unit": "portions"},
    {"id": "p12", "name": "Grilled chicken",     "unit": "pcs"},
]

TOKEN_MAP = {o["token"]: o for o in OUTLETS}

def make_ref():
    return "KR-" + datetime.now().strftime("%Y%m%d") + "-" + secrets.token_hex(2).upper()

@app.route("/")
def index():
    return render_template("dashboard.html", outlets=OUTLETS)

@app.route("/request/<token>")
def portal(token):
    outlet = TOKEN_MAP.get(token)
    if not outlet:
        return "Invalid or expired link.", 404
    products = OUTLET_PRODUCTS.get(outlet["id"], [])
    return render_template("portal.html", outlet=outlet, products=products)

@app.route("/qr/<token>.png")
def qr_image(token):
    outlet = TOKEN_MAP.get(token)
    if not outlet:
        return "Not found", 404
    base = request.host_url.rstrip("/")
    url  = f"{base}/request/{token}"
    qr   = qrcode.QRCode(version=2, box_size=10, border=4,
                          error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1D9E75", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/search")
def search():
    token = request.args.get("token", "")
    if not TOKEN_MAP.get(token):
        return jsonify([]), 403
    q = request.args.get("q", "").lower().strip()
    if not q:
        return jsonify([])
    results = [p for p in ALL_PRODUCTS if q in p["name"].lower()]
    return jsonify(results[:8])

@app.route("/submit", methods=["POST"])
def submit():
    data   = request.get_json()
    token  = data.get("token", "")
    outlet = TOKEN_MAP.get(token)
    if not outlet:
        return jsonify({"ok": False, "error": "Invalid token"}), 403
    items = data.get("items", [])
    if not items:
        return jsonify({"ok": False, "error": "No items selected"}), 400
    ref = make_ref()
    insert_transfer(ref, outlet["id"], outlet["name"], items, data.get("note", ""))
    return jsonify({"ok": True, "ref": ref})

@app.route("/api/transfers")
def api_transfers():
    return jsonify(all_transfers())

@app.route("/api/update-status", methods=["POST"])
def api_update_status():
    data = request.get_json()
    update_status(int(data["id"]), data["status"])
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, port=5077)
