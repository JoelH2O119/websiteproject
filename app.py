from flask import Flask, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests
import csv

app = Flask(__name__)
app.secret_key = "something-very-secret-change-this"

API_BASE = "https://www.dnd5eapi.co/api/2014"

# ---------------- DATABASE INIT ---------------- #

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Characters table
    c.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            class TEXT,
            race TEXT,
            alignment TEXT,
            str INTEGER,
            dex INTEGER,
            con INTEGER,
            int INTEGER,
            wis INTEGER,
            cha INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- LOGIN HELPERS ---------------- #

def login_required(f):
    """Decorator to restrict access to logged-in users."""
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("You must be logged in to access this page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

def get_current_user():
    """Return the logged-in user's info from the database."""
    if "user_id" in session:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE id = ?", (session["user_id"],))
        row = c.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1]}
    return None


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("index.html", user=get_current_user())

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
            session["user_id"] = row[0]
            flash("Logged in successfully!")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.")
    return redirect(url_for("home"))

# ---------------- RESTRICTED PAGES ---------------- #

@app.route("/charactercreation")
@login_required
def charactercreation():
    classes = requests.get(f"{API_BASE}/classes").json().get("results", [])
    races = requests.get(f"{API_BASE}/races").json().get("results", [])
    return render_template("charactercreation.html", classes=classes, races=races)

@app.route("/createcharacter", methods=["POST"])
@login_required
def create_character():
    data = request.form
    user = get_current_user()
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO characters 
        (user_id, name, class, race, alignment, str, dex, con, int, wis, cha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["id"],
        data["name"],
        data["class"],
        data["race"],
        data["alignment"],
        data["str"],
        data["dex"],
        data["con"],
        data["int"],
        data["wis"],
        data["cha"]
    ))
    conn.commit()
    conn.close()
    flash("Character created!")
    return redirect(url_for("character_list"))

@app.route("/characters")
@login_required
def character_list():
    user = get_current_user()
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM characters WHERE user_id = ?", (user["id"],))
    chars = c.fetchall()
    conn.close()
    return render_template("my_character.html", chars=chars)

# ---------------- OTHER PAGES ---------------- #

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


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
