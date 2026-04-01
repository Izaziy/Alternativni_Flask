import time

from flask import Flask, render_template, request, redirect, session
from tinydb import TinyDB, Query

app = Flask(__name__, template_folder="templates1")
app.secret_key = "superskrivnostnikljuc"

db = TinyDB("db.json")
users = db.table("users")
notes = db.table("notes")
User = Query()
Note = Query()

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
 
    user_notes = notes.search(Note.username == session["user"])
    return render_template("dashboard.html", user=session["user"], notes=user_notes)

@app.route("/addnote", methods=["POST"])
def addnote():
    if "user" not in session:
        return redirect("/login")
 
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
 
    if title:
        notes.insert({
            "username": session["user"],
            "title": title,
            "content": content,
            "id": str(int(time.time() * 1000))
        })
 
    return redirect("/dashboard")

@app.route("/savenote", methods=["POST"])
def savenote():
    if "user" not in session:
        return redirect("/login")

    note = request.form.get("note", "")
    notes.insert({"username": session["user"], "content": note})
    return "Note saved successfully."

@app.route("/editnote/<note_id>", methods=["GET", "POST"])
def editnote(note_id):
    if "user" not in session:
        return redirect("/login")
 
    note = notes.get((Note.id == note_id) & (Note.username == session["user"]))
    if not note:
        return redirect("/dashboard")
 
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        notes.update({"title": title, "content": content},
                     (Note.id == note_id) & (Note.username == session["user"]))
        return redirect("/dashboard")
 
    return render_template("editnote.html", note=note)
 
 
@app.route("/deletenote/<note_id>")
def deletenote(note_id):
    if "user" not in session:
        return redirect("/login")
 
    notes.remove((Note.id == note_id) & (Note.username == session["user"]))
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
