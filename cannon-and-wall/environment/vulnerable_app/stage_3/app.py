# stage_3/app.py
# Cannon & Wall -- Vulnerable Target App (Stage 3)
# Difficulty: Hard -- chained + partially obfuscated vulnerabilities
# WARNING: This file is intentionally vulnerable for security training purposes.
# DO NOT deploy this in production.

from flask import Flask, request, session, jsonify, make_response

app = Flask(__name__)
# VULN: broken_auth -- secret derived from a predictable pattern (Lines 55-75)
_parts = ["sup3r", "_s3cr", "3t_k3y"]
app.secret_key = "".join(_parts)

# --- Chained SQLi route (Lines 12-28) ---
# Obfuscation: query is built via string join, not a single f-string.
# The vulnerability is identical in effect but harder to spot syntactically.
@app.route("/portal", methods=["POST"])
def portal():
    uid  = request.form.get("uid", "")
    token = request.form.get("token", "")
    # VULN: sqli -- parts are joined then executed; parameterization is absent
    parts = [
        "SELECT role FROM users WHERE uid='",
        uid,
        "' AND token='",
        token,
        "'"
    ]
    query = "".join(parts)
    users = {"root": "tok3n!", "viewer": "v13w3r"}
    if uid in users and users[uid] == token:
        session["uid"]  = uid
        session["role"] = "admin" if uid == "root" else "viewer"
        return jsonify({"status": "ok", "role": session["role"]})
    return jsonify({"status": "fail"}), 401

# --- Reflected XSS in error handler (Lines 32-50) ---
@app.route("/report", methods=["GET"])
def report():
    ref  = request.args.get("ref", "")
    page = request.args.get("page", "1")
    # VULN: xss -- ref parameter reflected without escaping inside an attribute value
    # Obfuscation: the XSS is inside an href attribute, not a plain text node
    html = (
        "<html><body>"
        "<h2>Report Page</h2>"
        f'<a href="/back?to={ref}">Back</a>'
        f"<p>Page {page}</p>"
        "</body></html>"
    )
    return html

# --- Broken Auth via predictable session fixation (Lines 55-75) ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # VULN: broken_auth -- any request can set its own role via a cookie
    override = request.cookies.get("role_override")
    if override:
        session["role"] = override          # attacker sets role=admin via cookie
    role = session.get("role", "guest")
    if role != "admin":
        return jsonify({"status": "forbidden"}), 403
    return jsonify({"status": "ok", "panel": "admin_data"})

@app.route("/health")
def health():
    return jsonify({"status": "running", "stage": 3})

if __name__ == "__main__":
    app.run(debug=False, port=5003)
    