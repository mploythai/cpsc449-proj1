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
    # code by mike
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


# for debug
# @app.route("/data")
# @auth
# async def data():
#     data = cursor.execute("select * from accounts").fetchall()

#     return await render_template_string(f"{data}")


@app.route("/game", methods=["POST"])
@auth
async def game():
    return await wordGuess()


@app.route("/game/new", methods=["POST"])
@auth
async def newGame():
    # code by yahya
    createWordTables()
    data = cursor.execute(
        "select word from correctWords order by Random() limit 1"
    ).fetchone()
    await createGameTable(data[0])
    return await wordGuess()


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
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"

    cursor.execute(
        f"create table if not exists {tableName} (word text, tries numeric, history text, won numeric DEFAULT NULL)"
    )
    cursor.execute(
        f"insert into {tableName} (word, tries, history) values ('{word}', 0, '')"
    )
    connect.commit()


async def wordGuess():
    # code by Apurva
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"
    word = cursor.execute(
        f"select word from {tableName} order by rowid desc limit 1"
    ).fetchone()[0]

    validJson = cursor.execute(f"select * from validWords").fetchall()
    guess_result = {}
    guessed_words = [guess_result]

    valid = []
    for i in validJson:
        valid.append(i[0])

    input = await request.get_json()
    entered_word = input["word"]
    if entered_word == word:
        won = 1
        cursor.execute(f"insert won into {tableName} values ({won})")

        return await render_template_string(f"You won\n word is {word}")
    else:
        for i in range(5):
            if entered_word[i] in word:
                if word[i] == entered_word[i]:
                    if entered_word[i] in guess_result:
                        guess_result[entered_word[i] + f"{i}"] = "Correct"
                    else:
                        guess_result[entered_word[i]] = "Correct"
                else:
                    if entered_word[i] in guess_result:
                        guess_result[entered_word[i] + f"{i}"] = "Wrong Position"
                    else:
                        guess_result[entered_word[i]] = "Wrong Position"
            else:
                if entered_word[i] in guess_result:
                    guess_result[entered_word[i] + f"{i}"] = "Wrong"
                else:
                    guess_result[entered_word[i]] = "Wrong"
            cursor.execute(f"insert tries into {tableName} values ({i})")
            connect.commit()

        guessed_words.append(guess_result)
        cursor.execute(
            f"insert into {tableName} (word, tries, history) values ('{word}', 5, '{guessed_words}')"
        )
        connect.commit()

    return await render_template_string(f"Try again.\n {guess_result}")

    # if entered_word in valid:
    #     if entered_word == word:
    #         won = 1
    #         cursor.execute(f"insert won into {tableName} values ({won})")
    #         return await render_template_string(
    #             f"You've won! The word is {entered_word}."
    #         )
    #     else:
    #         for i in range(1, 5):
    #             if entered_word[i] in word:
    #                 position = str(word).find(entered_word[i])
    #                 guess_result[position] = entered_word[i]
    #                 insert_guess = str(guess_result)
    #                 cursor.execute(
    #                     f"insert history into {tableName} values ('{insert_guess}')"
    #                 )
    #                 connect.commit()

    #                 # fetch = cursor.execute(f"select * from {tableName}").fetchone()
    #                 return await render_template_string(f"test")
    #             else:
    #                 return await render_template_string(f"test")
    # else:
    #     return await render_template_string("Invalid word. Try again!")
    # if entered_word in validJson:


@app.route("/prev-game")
@auth
async def prevGame():
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"

    # for debugging purposes
    # print the word from the last game
    return await render_template_string(
        f"{cursor.execute(f'select rowid, * from {tableName} order by rowid desc limit 1, 1').fetchall()}"
    )


@app.route("/in-progress", methods=["GET"])
@auth
async def inProgress():
    # code by juan
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"
    cursor.execute(f"select rowid, tries, history from {tableName} where won IS NULL")
    rows = cursor.fetchall()
    display = []
    for i in rows:
        rowid, tries, history = i
        display.append({"rowid": rowid, "tries": tries, "history": history})
    return json.dumps(display), 200


@app.route("/get-game/<id>", methods=["GET"])
@auth
async def getGame(id):
    # code by juan
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"
    if (
        cursor.execute(
            f"select count(*) from {tableName} where rowid = {id}"
        ).fetchone()[0]
        == 0
    ):  # row does not exist
        return await make_response(
            "game not found !",
            404,
        )
    else:
        game_state = cursor.execute(
            f"select won from {tableName} where rowid = {id}"
        ).fetchone()[0]
        if game_state == 1:  # game is finished and won
            return {
                "game status": "won",
                "tries": cursor.execute(
                    f"select tries from {tableName} where rowid = {id}"
                ).fetchone()[0],
            }, 200
        elif game_state == 0:  # game is finished and lost
            return {
                "game status": "lost",
                "tries": cursor.execute(
                    f"select tries from {tableName} where rowid = {id}"
                ).fetchone()[0],
            }, 200
        else:  # game is in progress
            tries, history = cursor.execute(
                f"select tries, history from {tableName} where rowid = {id}"
            ).fetchone()
            return {"rowid": id, "tries": tries, "history": history}, 200
