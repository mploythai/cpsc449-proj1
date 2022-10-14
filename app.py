import sqlite3
import uuid
from quart import Quart, request, render_template

app = Quart(__name__)


@app.route("/")
async def show_form():
    return await render_template("form.html")


@app.route("/success", methods=["POST"])
async def show_success():
    con = sqlite3.connect("data.db")
    cur = con.cursor()

    form = await request.form
    user = f"{form['username']}"
    pwd = f"{form['password']}"

    if form.get("check"):
        new_user(user, pwd, con, cur)
        return await accept_login(user, pwd, cur)
    else:
        return await accept_login(user, pwd, cur)


def new_user(user, pwd, con, cur):
    cur.execute(
        "CREATE TABLE IF NOT EXISTS accounts (id text, username text NOT NULL UNIQUE, password text NOT NULL)"
    )
    cur.execute(f"INSERT INTO accounts VALUES ('{uuid.uuid4()}', '{user}', '{pwd}')")
    con.commit()


async def accept_login(user, pwd, cur):
    data = cur.execute(
        f"SELECT * FROM accounts WHERE username='{user}' AND password='{pwd}'"
    ).fetchone()

    if data:
        return await render_template("form.html", data=f"{data}")
    else:
        return await render_template("form.html", data="failed login.")
