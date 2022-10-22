# from quart import Quart, request, make_response, render_template_string
# from functools import wraps
# import sqlite3
# import base64
# import hashlib
# import secrets
# import uuid
# import json

# app = Quart(__name__)
# connect = sqlite3.connect("data.db")
# cursor = connect.cursor()

# ALGORITHM = "pbkdf2_sha256"


# def auth(fcn):
#     # code by mike
#     @wraps(fcn)
#     async def wrapper(*args, **kwargs):
#         cursor.execute(
#             "create table if not exists accounts (id text, username text not null, password text not null)"
#         )

#         auth = request.authorization
#         if auth and auth.type == "basic" and auth.username and auth.password:
#             user = str(auth.username)
#             reformattedUser = user.replace(" ", "_")

#             data = cursor.execute(
#                 f"select * from accounts where username='{reformattedUser}'"
#             ).fetchone()

#             if data:
#                 if verifyPass(f"{auth.password}", f"{data[2]}"):
#                     return await fcn(*args, **kwargs)
#             else:
#                 register(reformattedUser, auth.password)
#                 return await fcn(*args, **kwargs)

#         return await make_response(
#             "Couldn not verify!",
#             401,
#             {"WWW-Authenticate": 'Basic realm="Login required"'},
#         )

#     return wrapper


# def verifyPass(pwd, pwdHash):
#     if (pwdHash or "").count("$") != 3:
#         return False
#     algo, iter, salt, hash = pwdHash.split("$", 3)
#     iter = int(iter, base=10)
#     assert algo == ALGORITHM
#     compare = hashPass(pwd, salt, iter)
#     return secrets.compare_digest(pwdHash, compare)


# def hashPass(pwd, salt=None, iter=260000):
#     if salt is None:
#         salt = secrets.token_hex(16)
#     assert salt and isinstance(salt, str) and "$" not in salt
#     assert isinstance(pwd, str)
#     pwHash = hashlib.pbkdf2_hmac(
#         "sha256", pwd.encode("utf-8"), salt.encode("utf-8"), iter
#     )
#     hash = base64.b64encode(pwHash).decode("ascii").strip()
#     return "{}${}${}${}".format(ALGORITHM, iter, salt, hash)


# def register(user, pwd):
#     encryptedPwd = hashPass(pwd)
#     cursor.execute(
#         f"insert into accounts values ('{uuid.uuid4()}', '{user}', '{encryptedPwd}')"
#     )
#     connect.commit()


# @app.route("/")
# @auth
# async def index():
#     return {"authenticated": True}, 200


# @app.route("/data")
# @auth
# async def data():
#     data = cursor.execute("select * from accounts").fetchall()

#     return await render_template_string(f"{data}")


# @app.route("/game")
# @auth
# async def game():
#     # code by yahya
#     createWordTables()
#     data = cursor.execute(
#         "select word from correctWords order by Random() limit 1"
#     ).fetchone()

#     return await createGameTable(data[0])


# def createWordTables():
#     # code by yahya
#     correct = cursor.execute("create table if not exists correctWords (word text)")
#     valid = cursor.execute("create table if not exists validWords (word text)")

#     if not correct.fetchone():
#         jsonFile = open("data/correct.json")
#         file = json.load(jsonFile)
#         for i in file:
#             cursor.execute(f"insert into correctWords values ('{i}')")

#     if not valid.fetchone():
#         jsonFile = open("data/valid.json")
#         file = json.load(jsonFile)
#         for i in file:
#             cursor.execute(f"insert into validWords values ('{i}')")


# async def createGameTable(word):
#     # code by juan
#     auth = request.authorization
#     user = str(auth.username).replace(" ", "_")
#     tableName = f"game_{user}"

#     cursor.execute(
#         f"create table if not exists {tableName} (word text, tries numeric, history text)"
#     )
#     cursor.execute(f"insert into {tableName} values ('{word}', 5, '')")
#     connect.commit()

#     actualGame(word, tableName)

#     # for debugging purposes
#     # print the latest word and the tries and the history
#     return {"NewGameStarted": True}, 200


# async def actualGame(word, tableName):
#     validJson = cursor.execute("select word from validWords").fetchall()
#     correctJson = cursor.execute("select word from correctWords").fetchall()
#     won = False
#     guess_result = {}
#     guessed_words = [guess_result]

#     for m in range(0, 6):
#         return "test"


# # @app.route("/word-Guess")
# # @auth
# # async def wordGuess():
# # 	tableName = f"game_{user}"
# # 	words = cursor.execute(f'select word from {tableName}').fetchone()
# # 	validJson = f"{validWords}"
# # 	correctJson = f"{correctWords}"
# # 	won = 0
# # 	guess_result = {}
# # 	guessed_words = [guess_result]

# # 	for m in range(6):
# # 		entered_word = input()
# # 		if entered_word in validJson:
# # 			for i in range(5):
# # 				if entered_word[i] in words:
# # 					if words[i] == entered_word[i]:
# # 						if entered_word[i] in guess_result:
# # 							guess_result[entered_word[i]+f'{i}'] = "Correct"
# # 						else:
# # 							guess_result[entered_word[i]] = "Correct"
# # 					else:
# # 						if entered_word[i] in guess_result:
# # 							guess_result[entered_word[i]+f'{i}'] = "Wrong Position"
# # 						else:
# # 							guess_result[entered_word[i]] = "Wrong Position"
# # 				else:
# # 					if entered_word[i] in guess_result:
# # 							guess_result[entered_word[i]+f'{i}'] = "Wrong"
# # 					else:
# # 						guess_result[entered_word[i]] = "Wrong"

# # 			if entered_word == words:
# # 				won = 1
# # 				print("You win")
# # 				print(guess_result)
# # 				break
# # 		else:
# # 			print("Invalid word. Try again!!")
# # 			print(guess_result)
# # 			m=m+1
# # 			continue

# # 		guessed_words.append(guess_result)
# # 	cursor.execute(f"insert history into {tableName} values ({guessed_words})")
# # 	cursor.execute(f"insert won into {tableName} values ({won})")
# #     connect.commit()

# #     return await render_template_string(f"{tableName}")


# @app.route("/prev-game")
# @auth
# async def prevGame():
#     auth = request.authorization
#     user = str(auth.username).replace(" ", "_")
#     tableName = f"game_{user}"

#     # for debugging purposes
#     # print the word from the last game
#     return await render_template_string(
#         f"{cursor.execute(f'select rowid, * from {tableName} order by rowid desc limit 1, 1').fetchall()}"
#     )


# if __name__ == "__main__":
#     app.run()

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


@app.route("/game", methods=["POST"])
@auth
async def game():
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"
    word = cursor.execute(
        f"select word from {tableName} order by rowid desc limit 1"
    ).fetchone()[0]

    input = await request.get_json()
    history = {}
    order = 1
    if input["word"] == word:
        return await render_template_string(f"True. {input['word']} = {word}.")
    else:
        # convert json to string
        # store string into db
        # retrieve string from db
        # convert string to json
        history[order] = input["word"]
        return json.dumps(history)


@app.route("/game/prev", methods=["POST"])
@auth
async def prevGame():
    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"

    return await render_template_string(
        f"{cursor.execute(f'select word from {tableName} order by rowid desc limit 1, 1').fetchone()[0]}"
    )


@app.route("/game/new", methods=["POST"])
@auth
async def newGame():
    createWordTables()
    randomWord = cursor.execute(
        "select word from correctWords order by Random() limit 1"
    ).fetchone()
    await createGameTable(randomWord[0])

    auth = request.authorization
    user = str(auth.username).replace(" ", "_")
    tableName = f"game_{user}"

    return await render_template_string(
        f"{cursor.execute(f'select word from {tableName} order by rowid desc limit 1').fetchone()[0]}"
    )


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
        f"create table if not exists {tableName} (word text, tries numeric, history text)"
    )
    cursor.execute(f"insert into {tableName} values ('{word}', 5, '')")
    connect.commit()


if __name__ == "__main__":
    app.run()

# @app.route("/game/new", methods=["POST"])
# @auth
# async def newGame():
#     createWordTables()
#     randomWord = cursor.execute(
#         "select word from correctWords order by Random() limit 1"
#     ).fetchone()

#     auth = request.authorization
#     user = str(auth.username).replace(" ", "_")
#     tableName = f"game_{user}"
#     createGameTable(randomWord[0], tableName)

#     return await render_template_string(
#         f"{cursor.execute(f'select word from {tableName} order by rowid desc limit 1').fetchone()[0]}"
#     )

#     # data = await request.get_data()


# def createWordTables():
#     # code by yahya
#     correct = cursor.execute("create table if not exists correctWords (word text)")
#     valid = cursor.execute("create table if not exists validWords (word text)")

#     if not correct.fetchone():
#         jsonFile = open("data/correct.json")
#         file = json.load(jsonFile)
#         for i in file:
#             cursor.execute(f"insert into correctWords values ('{i}')")

#     if not valid.fetchone():
#         jsonFile = open("data/valid.json")
#         file = json.load(jsonFile)
#         for i in file:
#             cursor.execute(f"insert into validWords values ('{i}')")


# async def createGameTable(word, tableName):
#     # code by juan
#     cursor.execute(
#         f"create table if not exists {tableName} (word text, tries numeric, history text)"
#     )
#     cursor.execute(f"insert into {tableName} values ('{word}', 5, '')")
#     connect.commit()

#     # return {"NewGameStarted": True}, 200
