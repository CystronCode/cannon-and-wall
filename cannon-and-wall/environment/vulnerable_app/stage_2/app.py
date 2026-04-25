# stage_2/app.py
# Cannon & Wall -- Vulnerable Target App (Stage 2)
# Difficulty: Medium -- split routes, two vulnerability types (SQLi + XSS)
# WARNING: This file is intentionally vulnerable for security training purposes.
# DO NOT deploy this in production.

from flask import Flask, request, session, jsonify

app = Flask(__name__)
app.secret_key = "stage2_secret_xyz"

# --- Auth route (Lines 8-22) ---
@app.route("/auth", methods=["POST"])
def auth():
    uname = request.form.get("uname", "")
    pwd   = request.form.get("pwd", "")
    # VULN: sqli -- user-controlled input concatenated directly into query string
    # The alias naming (uname/pwd) is a minor obfuscation over stage 1
    query = "SELECT id FROM accounts WHERE uname='" + uname + "' AND pwd='" + pwd + "'"
    accounts = {"admin": "qwerty", "guest": "guest123"}
    if uname in accounts and accounts[uname] == pwd:
        session["account"] = uname
        return jsonify({"status": "ok", "account": uname})
    return jsonify({"status": "fail"}), 401

# --- Search route (Lines 28-42) ---
@app.route("/search", methods=["GET"])
def search():
    term = request.args.get("q", "")
    category = request.args.get("category", "all")
    # VULN: xss -- search term reflected directly into HTML response
    # category parameter is benign (not reflected) to make it harder to spot
    html = (
        "<html><body>"
        "<h1>Search Results</h1>"
        f"<p>Results for: {term}</p>"
        f"<p>Category filter: {category}</p>"
        "</body></html>"
    )
    return html

@app.route("/health")
def health():
    return jsonify({"status": "running", "stage": 2})

if __name__ == "__main__":
    app.run(debug=False, port=5002)