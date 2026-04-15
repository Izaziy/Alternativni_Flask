import os
import time

from flask import Flask, render_template, request, redirect, session
from tinydb import TinyDB, Query

app = Flask(__name__, template_folder="templates1")
app.secret_key = "superskrivnostnikljuc67"

db = TinyDB("db.json")
users = db.table("users")
notes = db.table("notes")
posts = db.table("posts")
User = Query()
Note = Query()
Post = Query()

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            users.insert({"username": username, "password": password})
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
 
 
@app.route("/deletenote/<note_id>", methods=["POST"])
def deletenote(note_id):
    if "user" not in session:
        return redirect("/login")
 
    notes.remove((Note.id == note_id) & (Note.username == session["user"]))
    return redirect("/dashboard")

@app.route("/feed")
def feed():
    if "user" not in session:
        return redirect("/login")
 
    all_posts = posts.all()
    all_posts.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
    return render_template("feed.html", user=session["user"], posts=all_posts)
 
 
@app.route("/addpost", methods=["POST"])
def addpost():
    if "user" not in session:
        return redirect("/login")
 
    content = request.form.get("content", "").strip()
    image_path = None
 
    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{int(time.time() * 1000)}.{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = f"uploads/{filename}"
 
    if content or image_path:
        posts.insert({
            "username": session["user"],
            "content": content,
            "image": image_path,
            "timestamp": int(time.time() * 1000),
            "id": str(int(time.time() * 1000))
        })
 
    return redirect("/feed")
 
 
@app.route("/deletepost/<post_id>", methods=["POST"])
def deletepost(post_id):
    if "user" not in session:
        return redirect("/login")
 
    post = posts.get((Post.id == post_id) & (Post.username == session["user"]))
    if post:
        if post.get("image"):
            img_path = os.path.join("static", post["image"])
            if os.path.exists(img_path):
                os.remove(img_path)
        posts.remove((Post.id == post_id) & (Post.username == session["user"]))
 
    return redirect("/feed")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
