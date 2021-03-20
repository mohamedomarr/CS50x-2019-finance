import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
  #raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query DataBase for user's Stocks and Amount of Shares
    rows = db.execute(
        "SELECT stock, SUM(shares) FROM trans INNER JOIN stocks ON trans.stockid = stocks.stockid WHERE id = :userid GROUP BY stock HAVING SUM(shares) >= 1", userid=session["user_id"])

    total = 0
    # iterate over rows list
    x = 0
    while x < len(rows):

        # lookup for Stock Name and Current Price using user's Stock Symbol
        quote = lookup(rows[x]["stock"])
        rows[x]["name"] = quote["name"]
        rows[x]["price"] = quote["price"]
        total += (rows[x]["price"] * rows[x]["SUM(shares)"])
        x += 1

    # Query for user's cash
    cash = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])

    total += cash[0]["cash"]

    return render_template("index.html", rows=rows, cash=usd(cash[0]["cash"]), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol isn't blank
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Ensure shares isn't blank
        if not request.form.get("shares"):
            return apology("missing shares", 400)

        # Ensure shares isn't non-numeric
        if not request.form.get("shares").isdigit():
            return apology("invalid shares", 400)

        # look up stocks for the provided symbol.
        quote = lookup(request.form.get("symbol"))

        # Ensure the symbol isn't invlid
        if quote == None:
            return apology("invalid symbol", 400)

        # Get the current Time
        now = datetime.datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")

        # Declare a variable for the final price
        final_price = float(quote["price"]) * int(request.form.get("shares"))

        # Query for user's cash
        cash_list = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
        cash = cash_list[0]["cash"]

        # Ensure if user can't afford stock price
        if cash < final_price:
            return apology("can't afford", 400)

        # Query for user's stock
        result = db.execute("SELECT stock FROM stocks WHERE stock = :symbol", symbol=quote["symbol"])

        # If user's stock isn't exist.
        if len(result) != 1:
            db.execute("INSERT INTO stocks (stock) VALUES(:symbol)", symbol=quote["symbol"])

        # If user's stock is exist.
        rows = db.execute("SELECT stockid FROM stocks WHERE stock = :symbol", symbol=quote["symbol"])
        stockid = rows[0]["stockid"]

        # Insert transaction infos into Database
        db.execute("INSERT INTO trans (id, stockid, shares, price, time) VALUES (:userid, :stockid, :shares, :price, :time)",
                   userid=session["user_id"], stockid=stockid, shares=request.form.get("shares"), price=quote["price"], time=time)

        # Update user amount of cash
        db.execute("UPDATE users SET cash = cash - :final_price WHERE id = :userid",
                   final_price=final_price, userid=session["user_id"])

        flash('Bought!')
        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username AVAILABLE, else false, in JSON format"""

    username = request.args.get("username")

    if len(username) > 0:

        # Check if username is already exists
        result = db.execute("SELECT * FROM users WHERE username = :username",
                            username=username)

        # if username is already exists apology
        if len(result) != 1:
            return jsonify(True)

        else:
            return jsonify(False)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Query DataBase for user's Stocks and Amount of Shares
    rows = db.execute(
        "SELECT stock, shares, price, time FROM trans INNER JOIN stocks ON trans.stockid = stocks.stockid WHERE id = :userid", userid=session["user_id"])

    return render_template("history.html", rows=rows)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol isn't blank
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        usersymbol = request.form.get("symbol")
        quote = lookup(usersymbol)

        if quote == None:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", name=quote["name"], price=usd(quote["price"]), symbol=quote["symbol"])

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username isn't blank
        if not request.form.get("username"):
            return apology("missing username", 400)

        # Ensure password isn't blank
        if not request.form.get("password"):
            return apology("missing password", 400)

        # Ensure passwords is match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Encrypt user's password
        else:
            hash = generate_password_hash(request.form.get("password"))

        # Ensure username isn't already exists
        result = db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get("username"))

        # if username is already exists apology
        if len(result) == 1:
            return apology("username taken", 400)

        # if isn't already exists inset user's username and passowrd to query
        else:
            db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                       username=request.form.get("username"), hash=hash)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash('Registered!')
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Query DataBase for user's Stocks
    rows = db.execute(
        "SELECT stock FROM trans INNER JOIN stocks ON trans.stockid = stocks.stockid WHERE id = :userid GROUP BY stock", userid=session["user_id"])

    if request.method == "POST":

        # Ensure symbol is selected
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Ensure shares isn't blank
        if not request.form.get("shares"):
            return apology("missing shares", 400)

        # Get user inputs
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Query DataBase for user's Shares
        user_shares = db.execute("SELECT stocks.stockid, SUM(shares) FROM trans INNER JOIN stocks ON trans.stockid = stocks.stockid WHERE id = :userid AND stock = :symbol GROUP BY stock",
                                 userid=session["user_id"], symbol=request.form.get("symbol"))

        # Ensure input shares is available
        if int(shares) > user_shares[0]["SUM(shares)"]:
            return apology("too many shares", 400)

        # Lookup for stock price
        quote = lookup(symbol)
        price = quote["price"]

        # Get the current Time
        now = datetime.datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")

        # Insert transaction infos into Database
        db.execute("INSERT INTO trans (id, stockid, shares, price, time) VALUES (:userid, :stockid, -:shares, :price, :time)",
                   userid=session["user_id"], stockid=user_shares[0]["stockid"], shares=shares, price=price, time=time)
        final_price = float(price) * int(shares)

        # Update user amount of cash
        db.execute("UPDATE users SET cash = cash + :final_price WHERE id = :userid",
                   final_price=final_price, userid=session["user_id"])

        flash("Sold!")
        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("sell.html", rows=rows)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User Settings"""
    # Query for username
    username = db.execute("SELECT username FROM users WHERE id = :userid", userid=session["user_id"])

    if request.method == "POST":

        if 'password' in request.form:
            # Ensure old password isn't blank
            if not request.form.get("oldpassword"):
                return apology("missing old password", 400)

            # Ensure new password isn't blank
            if not request.form.get("password"):
                return apology("missing new password", 400)

            # Ensure passwords is match
            if request.form.get("password") != request.form.get("confirmation"):
                return apology("new passwords don't match", 400)

            # Query database for password
            rows = db.execute("SELECT hash FROM users WHERE id = :userid", userid=session["user_id"])

            # Ensure old password is correct
            if not check_password_hash(rows[0]["hash"], request.form.get("oldpassword")):
                return apology("invalid old password", 403)

            # Encrypt user's password
            hash = generate_password_hash(request.form.get("password"))

            # Update user Password
            db.execute("UPDATE users SET hash = :hash WHERE id = :userid", userid=session["user_id"], hash=hash)

            flash("Password Successfully Changed!")
            return redirect("/settings")

        elif 'username' in request.form:

             # Ensure username isn't blank
            if not request.form.get("new_username"):
                return apology("missing new username", 400)

            # Ensure password isn't blank
            if not request.form.get("userpassword"):
                return apology("missing password", 400)

            # Ensure username isn't already exists
            result = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("new_username"))

            # if username is already exists apology
            if len(result) == 1:
                return apology("username taken", 400)

            # Query database for password
            rows = db.execute("SELECT hash FROM users WHERE id = :userid", userid=session["user_id"])

            # Ensure user's password is correct
            if not check_password_hash(rows[0]["hash"], request.form.get("userpassword")):
                return apology("invalid password", 403)

            # Update user Username
            db.execute("UPDATE users SET username = :username WHERE id = :userid",
                       userid=session["user_id"], username=request.form.get("new_username"))

            flash("Username Successfully Changed!")
            return redirect("/settings")
    else:
        return render_template("settings.html", username=username[0]["username"])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
