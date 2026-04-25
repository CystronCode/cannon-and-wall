# stage_1/app.py
# Cannon & Wall -- Vulnerable Target App (Stage 1)
# WARNING: This file is intentionally vulnerable for security training purposes.
# DO NOT deploy this in production.

from flask import Flask, request, session, jsonify

app = Flask(__name__)
app.secret_key = "hardcoded_secret_123"

# Lines 10-20: SQLi vulnerability lives here
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    # VULN: sqli -- string interpolation directly into SQL query
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # Attacker input: ' OR 1=1-- bypasses this check entirely
    users = {"admin": "password123", "user1": "secret"}
    if username in users and users[username] == password:
        session["user"] = username
        return jsonify({"status": "ok", "user": username})
    return jsonify({"status": "fail"}), 401

# Lines 25-35: XSS vulnerability lives here
@app.route("/comments", methods=["GET"])
def comments():
    comment = request.args.get("comment", "")
    # VULN: xss -- user input rendered directly into HTML without escaping
    return f"<html><body><div>{comment}</div></body></html>"
    # Attacker input: <script>alert('xss')</script> executes in browser



# blank line above (line 35)
# blank line above (line 36)
# blank line above (line 37)
# blank line above (line 38)
# Lines 40-55: Broken Auth vulnerability lives here
@app.route("/dashboard", methods=["GET"])
def dashboard():
    # VULN: broken_auth -- session user is set from request without server validation
    if request.args.get("user"):
        session["user"] = request.args.get("user")
    user = session.get("user")
    if not user:
        return jsonify({"status": "unauthorized"}), 401
    return jsonify({"status": "ok", "dashboard": f"Welcome {user}"})

@app.route("/health")
def health():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(debug=False, port=5001)
