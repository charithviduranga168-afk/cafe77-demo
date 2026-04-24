import os, sqlite3, json, secrets, socket
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, g
import qrcode

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'cafe77.db')

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
        {"id": "p2", "name": "Club sandwich",       "unit": "pcs"},
        {"id": "p4", "name": "Chicken rice box",    "unit": "boxes"},
        {"id": "p5", "name": "Chocolate mousse",    "unit": "cups"},
    ],
    "outlet-3": [
        {"id": "p1", "name": "Egg salad sandwich",  "unit": "pcs"},
        {"id": "p4", "name": "Chicken rice box",    "unit": "boxes"},
        {"id": "p6", "name": "Mango lassi base",    "unit": "litres"},
        {"id": "p7", "name": "Lemon tart",          "unit": "pcs"},
    ],
}

ALL_PRODUCTS = [
    {"id": "p1",  "name": "Egg salad sandwich",  "unit": "pcs"},
    {"id": "p2",  "name": "Club sandwich",        "unit": "pcs"},
    {"id": "p3",  "name": "Iced coffee base",     "unit": "litres"},
    {"id": "p4",  "name": "Chicken rice box",     "unit": "boxes"},
    {"id": "p5",  "name": "Chocolate mousse",     "unit": "cups"},
    {"id": "p6",  "name": "Mango lassi base",     "unit": "litres"},
    {"id": "p7",  "name": "Lemon tart",           "unit": "pcs"},
    {"id": "p8",  "name": "Tomato soup",          "unit": "litres"},
    {"id": "p9",  "name": "Garlic bread",         "unit": "pcs"},
    {"id": "p10", "name": "Caesar salad",         "unit": "portions"},
    {"id": "p11", "name": "Pasta bolognese",      "unit": "portions"},
    {"id": "p12", "name": "Grilled chicken",      "unit": "pcs"},
]

TOKEN_MAP = {o["token"]: o for o in OUTLETS}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    with app.app_context():
        db = sqlite3.connect(DB)
        db.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ref         TEXT NOT NULL,
                outlet_id   TEXT NOT NULL,
                outlet_name TEXT NOT NULL,
                items_json  TEXT NOT NULL,
                note        TEXT,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT NOT NULL
            )
        """)
        db.commit()
        db.close()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def generate_qr_codes(base_url):
    for outlet in OUTLETS:
        url = f"{base_url}/request/{outlet['token']}"
        img = qrcode.QRCode(version=2, box_size=10, border=4,
                            error_correction=qrcode.constants.ERROR_CORRECT_M)
        img.add_data(url)
        img.make(fit=True)
        qr_img = img.make_image(fill_color="#1D9E75", back_color="white")
        path = os.path.join(os.path.dirname(__file__), "static", "qr", f"{outlet['id']}.png")
        qr_img.save(path)

def make_ref():
    return "KR-" + datetime.now().strftime("%Y%m%d") + "-" + str(secrets.token_hex(2)).upper()


# ── ROUTES ──────────────────────────────────────────────────────────────────

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

@app.route("/search")
def search():
    token = request.args.get("token", "")
    q = request.args.get("q", "").lower().strip()
    if not TOKEN_MAP.get(token):
        return jsonify([]), 403
    if not q:
        return jsonify([])
    results = [p for p in ALL_PRODUCTS if q in p["name"].lower()]
    return jsonify(results[:8])

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    token   = data.get("token", "")
    outlet  = TOKEN_MAP.get(token)
    if not outlet:
        return jsonify({"ok": False, "error": "Invalid token"}), 403
    items   = data.get("items", [])
    note    = data.get("note", "").strip()
    if not items:
        return jsonify({"ok": False, "error": "No items selected"}), 400
    ref = make_ref()
    db = get_db()
    db.execute(
        "INSERT INTO transfers (ref,outlet_id,outlet_name,items_json,note,status,created_at) VALUES (?,?,?,?,?,?,?)",
        (ref, outlet["id"], outlet["name"], json.dumps(items), note, "pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    db.commit()
    return jsonify({"ok": True, "ref": ref})

@app.route("/api/transfers")
def api_transfers():
    db = get_db()
    rows = db.execute("SELECT * FROM transfers ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/update-status", methods=["POST"])
def update_status():
    data = request.get_json()
    db = get_db()
    db.execute("UPDATE transfers SET status=? WHERE id=?", (data["status"], data["id"]))
    db.commit()
    return jsonify({"ok": True})

@app.route("/qr/<outlet_id>.png")
def qr_image(outlet_id):
    from flask import send_from_directory
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static", "qr"), f"{outlet_id}.png")


if __name__ == "__main__":
    init_db()
    ip = get_local_ip()
    port = 5077
    base_url = f"http://{ip}:{port}"
    print(f"\n{'='*52}")
    print(f"  Café 77 Kitchen Request Demo")
    print(f"{'='*52}")
    print(f"  PC dashboard  →  {base_url}")
    print(f"  Generating QR codes for your phone...")
    generate_qr_codes(base_url)
    print(f"  QR codes ready. Open dashboard to see them.")
    print(f"{'='*52}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
