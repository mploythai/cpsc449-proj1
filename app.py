from quart import Quart, request, make_response, render_template_string
from functools import wraps
import sqlite3
import uuid
import base64
import hashlib
import secrets

app = Quart(__name__)

# connect to sqlite db
connect = sqlite3.connect("data.db")
cursor = connect.cursor()

# for password encryption
ALGORITHM = "pbkdf2_sha256"

# authentication
def auth(fcn):
    @wraps(fcn)
    async def wrapper(*args, **kwargs):
        auth = request.authorization
        # accounts table
        cursor.execute(
            "create table if not exists accounts (id text primary key, username text not null, password text not null)"
        )

        if auth and auth.type == "basic" and auth.username and auth.password:
            # check if user exists in db based in user input
            data = cursor.execute(
                f"select * from accounts where username='{auth.username}'"
            ).fetchone()

            # if the data does exist, check if their password input
            # is correct, then authenticate the user if it is
            # else, put their info into the db and then authenticate
            if data:
                if verify_password(f"{auth.password}", f"{data[2]}"):
                    return await fcn(*args, **kwargs)
            else:
                register(auth.username, auth.password)
                return await fcn(*args, **kwargs)

        # if user presses cancel, return 401 response
        return await make_response(
            "Could not verify!",
            401,
            {"WWW-Authenticate": 'Basic realm="Login required"'},
        )

    return wrapper


# create new user if user dne in the db
def register(user, pwd):
    encrypted_pwd = hash_password(pwd)
    cursor.execute(
        f"insert into accounts values ('{uuid.uuid4()}', '{user}', '{encrypted_pwd}')"
    )
    connect.commit()


# password encryption
def hash_password(password, salt=None, iterations=260000):
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iterations, salt, b64_hash)


# password verification
def verify_password(password, password_hash):
    if (password_hash or "").count("$") != 3:
        return False
    algorithm, iterations, salt, b64_hash = password_hash.split("$", 3)
    iterations = int(iterations, base=10)
    assert algorithm == ALGORITHM
    compare_hash = hash_password(password, salt, iterations)
    return secrets.compare_digest(password_hash, compare_hash)


# main page
@app.route("/")
@auth
async def index():
    return {"authenticated": True}, 200


# page to check if data is being pushed to db properly
@app.route("/data")
@auth
async def data():
    data = cursor.execute("select * from accounts").fetchall()
    return await render_template_string(f"{data}")


# game page
@app.route("/game")
@auth
async def game():
    return "insert game stuff here."


if __name__ == "__main__":
    app.run()
