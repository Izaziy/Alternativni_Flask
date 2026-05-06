import os
import time

from flask import Flask, render_template, request, redirect, session, jsonify
from tinydb import TinyDB, Query

app = Flask(__name__, template_folder="templates1")
app.secret_key = "superskrivnostnikljuc67"

db = TinyDB("db.json")
users = db.table("users")
notes = db.table("notes")
posts = db.table("posts")
follows = db.table("follows")
User = Query()
Note = Query()
Post = Query()
Follow = Query()

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Preveri ali je datoteka dovoljen tip."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    """
    Shrani naloženo datoteko in vrne pot do nje.
    Če datoteke ni ali ni dovoljena, vrne None.
    """
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename):
        return None
    
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{int(time.time() * 1000)}.{ext}"
    
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    return f"uploads/{filename}"

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
    """Dodaj novo beležko. Podpoira AJAX zahtevke."""
    if "user" not in session:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Not logged in")
        return redirect("/login")
 
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
 
    if not title:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Title is required")
        return redirect("/dashboard")
    
    note_id = str(int(time.time() * 1000))
    notes.insert({
        "username": session["user"],
        "title": title,
        "content": content,
        "id": note_id
    })
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True, message="Note added", id=note_id)
 
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
    """Izbriši beležko. Podpoira AJAX zahtevke."""
    if "user" not in session:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Not logged in")
        return redirect("/login")
 
    note = notes.get((Note.id == note_id) & (Note.username == session["user"]))
    if not note:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Note not found")
        return redirect("/dashboard")
    
    notes.remove((Note.id == note_id) & (Note.username == session["user"]))
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True, message="Note deleted")
    
    return redirect("/dashboard")

@app.route("/feed")
def feed():
    if "user" not in session:
        return redirect("/login")
 
    tab = request.args.get("tab", "everyone")
 
    if tab == "following":
        following_list = [f["following"] for f in follows.search(Follow.follower == session["user"])]
        visible_posts = [p for p in posts.all() if p.get("username") in following_list]
    else:
        visible_posts = posts.all()
 
    visible_posts.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
 
    for p in visible_posts:
        u = users.get(User.username == p.get("username"))
        p["avatar"] = (u or {}).get("avatar", "")
 
    return render_template("feed.html", user=session["user"], posts=visible_posts, tab=tab)
 
 
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

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True)

    return redirect("/feed")
 
 
@app.route("/deletepost/<post_id>", methods=["POST"])
def deletepost(post_id):
    """Izbriši prispevek. Podpoira AJAX zahtevke."""
    if "user" not in session:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Not logged in")
        return redirect("/login")
 
    post = posts.get((Post.id == post_id) & (Post.username == session["user"]))
    if not post:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Post not found")
        return redirect("/feed")
    
    if post.get("image"):
        img_path = os.path.join("static", post["image"])
        if os.path.exists(img_path):
            os.remove(img_path)
    
    posts.remove((Post.id == post_id) & (Post.username == session["user"]))
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True, message="Post deleted")
 
    return redirect("/feed")

@app.route("/profile/<username>")
def profile(username):
    if "user" not in session:
        return redirect("/login")
 
    profile_user = users.get(User.username == username)
    if not profile_user:
        return redirect("/feed")
 
    user_posts = posts.search(Post.username == username)
    user_posts.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
 
    follower_count = len(follows.search(Follow.following == username))
    following_count = len(follows.search(Follow.follower == username))
    is_following = bool(follows.get((Follow.follower == session["user"]) & (Follow.following == username)))
    is_own = (session["user"] == username)
 
    return render_template("profile.html",
                           user=session["user"],
                           profile_user=profile_user,
                           user_posts=user_posts,
                           follower_count=follower_count,
                           following_count=following_count,
                           is_following=is_following,
                           is_own=is_own)

@app.route("/follow/<username>", methods=["POST"])
def follow(username):
    """Sledi uporabniku. Podpoira AJAX zahtevke."""
    if "user" not in session:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Not logged in")
        return redirect("/login")
 
    if session["user"] == username:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Cannot follow yourself")
        return redirect(f"/profile/{username}")
 
    already = follows.get((Follow.follower == session["user"]) & (Follow.following == username))
    if not already:
        follows.insert({"follower": session["user"], "following": username})
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True, message="Now following")
 
    return redirect(f"/profile/{username}")
 
 
@app.route("/unfollow/<username>", methods=["POST"])
def unfollow(username):
    """Nehaj slediti uporabniku. Podpoira AJAX zahtevke."""
    if "user" not in session:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=False, message="Not logged in")
        return redirect("/login")
 
    follows.remove((Follow.follower == session["user"]) & (Follow.following == username))
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True, message="Unfollowed")
    
    return redirect(f"/profile/{username}")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect("/login")
 
    user_data = users.get(User.username == session["user"])
    error = None
    success = None
 
    if request.method == "POST":
        action = request.form.get("action")
 
        if action == "profile":
            bio = request.form.get("bio", "").strip()
            avatar_path = save_file(request.files.get("avatar"))
 
            update_data = {"bio": bio}
            if avatar_path:
                old_avatar = user_data.get("avatar", "")
                if old_avatar:
                    old_path = os.path.join("static", old_avatar)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                update_data["avatar"] = avatar_path
 
            users.update(update_data, User.username == session["user"])
            success = "Profile updated."
            user_data = users.get(User.username == session["user"])
 
        elif action == "username":
            new_username = request.form.get("new_username", "").strip()
 
            if not new_username:
                error = "Username cannot be empty."
            elif new_username == session["user"]:
                error = "That's already your username."
            elif users.search(User.username == new_username):
                error = "Username already taken."
            else:
                old = session["user"]
                users.update({"username": new_username}, User.username == old)
                notes.update({"username": new_username}, Note.username == old)
                posts.update({"username": new_username}, Post.username == old)
                follows.update({"follower": new_username}, Follow.follower == old)
                follows.update({"following": new_username}, Follow.following == old)
                session["user"] = new_username
                success = "Username changed successfully."
                user_data = users.get(User.username == new_username)
 
        elif action == "password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")
 
            if not current_pw or not new_pw or not confirm_pw:
                error = "All password fields are required."
            elif user_data.get("password") != current_pw:
                error = "Current password is incorrect."
            elif new_pw != confirm_pw:
                error = "New passwords do not match."
            elif len(new_pw) < 4:
                error = "Password must be at least 4 characters."
            else:
                users.update({"password": new_pw}, User.username == session["user"])
                success = "Password changed successfully."
                success = "Password changed successfully."
 
    return render_template("settings.html", user=session["user"], user_data=user_data,
                           error=error, success=success)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
