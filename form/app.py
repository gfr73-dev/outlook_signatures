from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# MySQL connection
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",        # XAMPP default
        database="dpd"   # change if needed
    )

@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        job = request.form["job"]
        dept = request.form["dept"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        phone = request.form["phone"]

        cursor.execute(
            """
            INSERT INTO employees (name, job, dept, email, mobile, phone)
            VALUES (%s, %s, %s, %s, %s,%s)
            """,
            (name, job, dept, email, mobile, phone)
        )
        db.commit()
        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    db.close()

    return render_template("index.html", employees=employees)

@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("index"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        cursor.execute(
            """
            UPDATE employees
            SET name=%s, job=%s, dept=%s, email=%s, mobile=%s, phone=%s
            WHERE id=%s
            """,
            (
                request.form["name"],
                request.form["job"],
                request.form["dept"],
                request.form["email"],
                request.form["mobile"],
                request.form["phone"],
                id
            )
        )
        db.commit()
        db.close()
        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM employees WHERE id=%s", (id,))
    employee = cursor.fetchone()
    db.close()

    return render_template("index.html", employee=employee, edit_mode=True)

# ==================================================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)
