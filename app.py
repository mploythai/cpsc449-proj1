from quart import Quart, request, make_response, render_template_string
from functools import wraps
import sqlite3
import base64
import hashlib
import secrets
import uuid
import json

app = Quart(__name__)
connect = sqlite3.connect("data.db")
cursor = connect.cursor()

ALGORITHM = "pbkdf2_sha256"


def auth(fcn):
    @wraps(fcn)
    async def wrapper(*args, **kwargs):
        cursor.execute(
            "create table if not exists accounts (id text, username text not null, password text not null)"
        )

        auth = request.authorization
        if auth and auth.type == "basic" and auth.username and auth.password:
            user = str(auth.username)
            reformattedUser = user.replace(" ", "_")

            data = cursor.execute(
                f"select * from accounts where username='{reformattedUser}'"
            ).fetchone()

            if data:
                if verifyPass(f"{auth.password}", f"{data[2]}"):
                    return await fcn(*args, **kwargs)
            else:
                register(reformattedUser, auth.password)
                return await fcn(*args, **kwargs)

        return await make_response(
            "Couldn not verify!",
            401,
            {"WWW-Authenticate": 'Basic realm="Login required"'},
        )

    return wrapper


def verifyPass(pwd, pwdHash):
    if (pwdHash or "").count("$") != 3:
        return False
    algo, iter, salt, hash = pwdHash.split("$", 3)
    iter = int(iter, base=10)
    assert algo == ALGORITHM
    compare = hashPass(pwd, salt, iter)
    return secrets.compare_digest(pwdHash, compare)


def hashPass(pwd, salt=None, iter=260000):
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(pwd, str)
    pwHash = hashlib.pbkdf2_hmac(
        "sha256", pwd.encode("utf-8"), salt.encode("utf-8"), iter
    )
    hash = base64.b64encode(pwHash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iter, salt, hash)


def register(user, pwd):
    encryptedPwd = hashPass(pwd)
    cursor.execute(
        f"insert into accounts values ('{uuid.uuid4()}', '{user}', '{encryptedPwd}')"
    )
    connect.commit()


@app.route("/")
@auth
async def index():
    return {"authenticated": True}, 200


@app.route("/data")
@auth
async def data():
    data = cursor.execute("select * from accounts").fetchall()

    return await render_template_string(f"{data}")


@app.route("/game")
@auth
async def game():
    # code by yahya
    createWordTables()
    data = cursor.execute(
        "select word from correctWords order by Random() limit 1"
    ).fetchone()

    return await createGameTable(data[0])


def createWordTables():
    # code by yahya
    correct = cursor.execute("create table if not exists correctWords (word text)")
    valid = cursor.execute("create table if not exists validWords (word text)")

    if not correct.fetchone():
        jsonFile = open("data/correct.json")
        file = json.load(jsonFile)
        for i in file:
            cursor.execute(f"insert into correctWords values ('{i}')")

    if not valid.fetchone():
        jsonFile = open("data/valid.json")
        file = json.load(jsonFile)
        for i in file:
            cursor.execute(f"insert into validWords values ('{i}')")


async def createGameTable(word):
    # code by juan
    user = cursor.execute(
        f"select username from accounts where username='mike-ploythai'"
    ).fetchone()
    tableName = f"{word}_{user}"

    cursor.execute(
        f"create table if not exists {tableName} (id text, word text, tries numeric, history text)"
    )
    cursor.execute(
        f"insert into {tableName} values ('{uuid.uuid4()}', '{word}', 5, '')"
    )
    connect.commit()

    return await render_template_string(
        f"{cursor.execute(f'select * from {tableName}').fetchall()}"
    )


@app.route("/prev-game")
@auth
async def prevGame():
    return


if __name__ == "__main__":
    app.run()
