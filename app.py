import os
from tempfile import mkdtemp

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from helpers import apology, login_required
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# # Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///exp.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

    students = db.execute(
        "SELECT students.s_id, students.first_name, students.second_name, students.section, COUNT(memos.memo) as number_m FROM students JOIN memos ON students.s_id = memos.s_id GROUP BY students.s_id"
    )

    return render_template("index.html", students=students)


@app.route("/student", methods=["GET", "POST"])
@login_required
def student():

    student_id = request.form.get("student")

    memos = db.execute("SELECT * FROM memos WHERE memos.s_id = ?", student_id)
    student = db.execute("SELECT * FROM students WHERE s_id = ?", student_id)
    actions = db.execute("SELECT * FROM actions WHERE actions.s_id = ?", student_id)
    first = student[0]["first_name"]
    second = student[0]["second_name"]
    section = student[0]["section"]
    student = student[0]["s_id"]

    student_name = f"{first} {second} from section {section}"

    return render_template(
        "student.html",
        memos=memos,
        student=student,
        actions=actions,
        student_name=student_name,
    )


@app.route("/response", methods=["GET", "POST"])
@login_required
def response():
    if request.method == "POST":

        action_id = request.form.get("response")
        action = db.execute("SELECT * FROM actions WHERE id = ?", action_id)
        student_id = action[0]["s_id"]
        student = db.execute("SELECT * FROM students WHERE s_id = ?", student_id)

        first_name = student[0]["first_name"]
        second_name = student[0]["second_name"]
        section = student[0]["section"]
        contacted = action[0]["contacted"]
        action_taken = action[0]["action_taken"]

        return render_template(
            "response.html",
            first_name=first_name,
            section=section,
            second_name=second_name,
            action_id=action_id,
            contacted=contacted,
            action_taken=action_taken,
        )

    else:
        return render_template("student.html")


@app.route("/update_action", methods=["GET", "POST"])
@login_required
def update_action():

    if request.method == "POST":
        first_name = request.form.get("first_name")
        second_name = request.form.get("second_name")
        section = request.form.get("section")
        contacted = request.form.get("contacted")
        action_taken = request.form.get("action_taken")
        response = request.form.get("response")
        r_date = request.form.get("response_date")
        action_id = request.form.get("action_id")
        db.execute(
            "UPDATE actions SET response=?, date_of_response=? WHERE id=?",
            response,
            r_date,
            action_id,
        )
        return redirect("/")


@app.route("/action", methods=["GET", "POST"])
@login_required
def make_action():

    if request.method == "POST":

        first_name = request.form.get("first_name")
        second_name = request.form.get("second_name")
        section = request.form.get("section")
        action = request.form.get("action")
        contacted = request.form.get("contacted")
        c_date = request.form.get("contact_date")

        student = db.execute(
            "SELECT * FROM students WHERE first_name = ? AND second_name = ? AND section = ?",
            first_name,
            second_name,
            section,
        )

        s_id = student[0]["s_id"]

        db.execute(
            "INSERT INTO actions (s_id, action_taken, contacted, date_of_contact, response, date_of_response) VALUES (?, ?, ?, ?, 'PENDING', 'PENDING')",
            s_id,
            action,
            contacted,
            c_date,
        )

        return redirect("/")

    else:
        return render_template("action.html")


@app.route("/add_new", methods=["GET", "POST"])
@login_required
def add_new():
    if request.method == "POST":

        student_id = request.form.get("add_memo")

        student = db.execute("SELECT * FROM students WHERE s_id = ?", student_id)

        first_name = student[0]["first_name"]
        second_name = student[0]["second_name"]
        section = student[0]["section"]

        return render_template(
            "add_new_one.html",
            first_name=first_name,
            section=section,
            second_name=second_name,
            s_id=student_id,
        )

    else:
        return render_template("index.html")


@app.route("/add_new_one", methods=["GET", "POST"])
@login_required
def add_new_one():

    if request.method == "POST":
        first_name = request.form.get("first_name")
        second_name = request.form.get("second_name")
        section = request.form.get("section")
        memo = request.form.get("memo")
        teacher = request.form.get("teacher")
        c_date = request.form.get("date")
        s_id = request.form.get("s_id")

        db.execute(
            "INSERT INTO memos (s_id, memo, teacher, date) VALUES (?, ?, ?, ?)",
            s_id,
            memo,
            teacher,
            c_date,
        )

        return redirect("/")
    else:
        return render_template("add_new_one.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/add_memo", methods=["GET", "POST"])
@login_required
def add_memo():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        second_name = request.form.get("second_name")
        section = request.form.get("section")
        memo = request.form.get("memo")
        teacher = request.form.get("teacher")
        c_date = request.form.get("get")

        try:
            student = db.execute(
                "SELECT * FROM students WHERE first_name = ? AND second_name = ? AND section = ?",
                first_name,
                second_name,
                section,
            )

            s_id = student[0]["s_id"]

            db.execute(
                "INSERT INTO memos (s_id, memo, teacher, date) VALUES (?, ?, ?, ?)",
                s_id,
                memo,
                teacher,
                c_date,
            )

            return redirect("/")

        except IndexError:
            db.execute(
                "INSERT INTO students (first_name, second_name, section) VALUES (?, ?, ?)",
                first_name,
                second_name,
                section,
            )

            student = db.execute(
                "SELECT * FROM students WHERE first_name = ? AND second_name = ? AND section = ?",
                first_name,
                second_name,
                section,
            )

            s_id = student[0]["s_id"]

            db.execute(
                "INSERT INTO memos (s_id, memo, teacher, date) VALUES (?, ?, ?, ?)",
                s_id,
                memo,
                teacher,
                c_date,
            )

            return redirect("/")

    else:
        return render_template("add_memo.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        password = request.form.get("password")
        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        confirmation = request.form.get("confirmation")
        if not request.form.get("confirmation"):
            return apology("must confirm password", 400)
        elif password != confirmation:
            return apology("enter password again to confirm", 400)

        hashed = generate_password_hash(password)

        check = db.execute("SELECT * FROM users WHERE username = ?", username)
        if check:
            return apology("username already exist", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed)

        return redirect("/")
    else:
        return render_template("register.html")
