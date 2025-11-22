from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests
import csv

# ---------------- FLASK APP SETUP ---------------- #
app = Flask(__name__)
app.secret_key = "something-very-secret-change-this"

API_BASE = "https://www.dnd5eapi.co/api/2014"

# ---------------- DATABASE ---------------- #
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()  # call this at startup

# ---------------- LOGIN SYSTEM ---------------- #
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(id=row[0], username=row[1], password_hash=row[2])
    return None

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/charactercreation")
@login_required
def charactercreation():
    classes = requests.get(f"{API_BASE}/classes").json().get("results", [])
    races   = requests.get(f"{API_BASE}/races").json().get("results", [])
    return render_template("charactercreation.html", classes=classes, races=races)

@app.route("/wikipage")
def wikipage():
    return render_template("wikipage.html")

@app.route("/classpage")
def classpage():
    return render_template("classpage.html")

@app.route('/class/<index>')
def class_detail(index):
    data = requests.get(f"{API_BASE}/classes/{index}").json()
    return render_template("class_detail.html", data=data)

@app.route("/spellpage")
def spellpage():
    spells = []
    with open("dnd-spells.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            spells.append(row)
    return render_template("spellpage.html", spells=spells)

@app.route("/item")
def itempage():
    item_list = requests.get(f"{API_BASE}/equipment").json().get("results", [])
    return render_template("itempage.html", items=item_list)

# ---------------- AUTH ROUTES ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            flash("Registration successful! You can now log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row[1], password):
            user = User(id=row[0], username=username, password_hash=row[1])
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("home"))

# ---------------- RUN APP ---------------- #
if __name__ == "__main__":
    app.run(debug=True)
