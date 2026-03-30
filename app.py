from flask import Flask, render_template, request, redirect, session
from tinydb import TinyDB, Query

app = Flask(__name__, template_folder="templates1")
app.secret_key = "superskrivnostnikljuc"

db = TinyDB("db.json")
users = db.table("users")
User = Query()

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        elif users.search(User.username == username):
            error = "Username already exists."
        else:
            users.insert({"username": username, "password": password, "note": ""})
            return redirect("/login")

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = users.get(User.username == username)

        if not user or user.get("password") != password:
            error = "Invalid username or password."
        else:
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user_data = users.get(User.username == session["user"])
    note = (user_data or {}).get("note", "")

    return render_template("dashboard.html", user=session["user"], note=note)

@app.route("/savenote", methods=["POST"])
def savenote():
    if "user" not in session:
        return redirect("/login")

    note = request.form.get("note", "")
    users.update({"note": note}, User.username == session["user"])
    return "Note saved successfully."

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
