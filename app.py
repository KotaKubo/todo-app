from flask import Flask, jsonify, render_template, request, g
import sqlite3

app = Flask(__name__)
DATABASE = "todos.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        get_db().execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT    NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        get_db().commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/todos", methods=["GET"])
def get_todos():
    rows = get_db().execute("SELECT * FROM todos ORDER BY created_at ASC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/todos", methods=["POST"])
def create_todo():
    title = (request.get_json() or {}).get("title", "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    db = get_db()
    cur = db.execute("INSERT INTO todos (title) VALUES (?)", (title,))
    db.commit()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/todos/<int:tid>", methods=["PUT"])
def update_todo(tid):
    db = get_db()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (tid,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    data = request.get_json() or {}
    title = data.get("title", row["title"])
    if isinstance(title, str):
        title = title.strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    completed = int(data.get("completed", row["completed"]))
    db.execute(
        "UPDATE todos SET title = ?, completed = ? WHERE id = ?",
        (title, completed, tid),
    )
    db.commit()
    return jsonify(dict(db.execute("SELECT * FROM todos WHERE id = ?", (tid,)).fetchone()))


@app.route("/api/todos/<int:tid>", methods=["DELETE"])
def delete_todo(tid):
    get_db().execute("DELETE FROM todos WHERE id = ?", (tid,))
    get_db().commit()
    return "", 204


@app.route("/api/todos/completed", methods=["DELETE"])
def clear_completed():
    get_db().execute("DELETE FROM todos WHERE completed = 1")
    get_db().commit()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
