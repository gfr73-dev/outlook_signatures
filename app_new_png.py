from flask import (
    Flask,
    render_template,
    request,
    send_file,
)
from PIL import Image, ImageDraw, ImageFont
import io
import mysql.connector
import os

app = Flask(__name__)

# --------------------------------------------------
# DATABASE CONFIG
# --------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "dpd",
}

# --------------------------------------------------
# BRAND / LAYOUT CONFIG
# --------------------------------------------------
IMAGE_WIDTH = 600
IMAGE_HEIGHT = 430
FONT_PATH = "arial.ttf"

COMPANY_NAME = "DPD Portugal SA"
ADDRESS_TEXT = "Avenida Alvaro Cunhal, Lote 2 | 2660-341 Santo Antonio Cavaleiros | Portugal"
DPD_URL = "https://www.dpd.pt"

# --------------------------------------------------
# LOGOS
# --------------------------------------------------
LOGO_DPD = "static/logos/dpd_logo_50.png"
LOGO_GEOPOST = "static/logos/geopost_logo_50.png"

# ==================================================
# INDEX + SEARCH
# ==================================================
@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "")
    employees = []

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        if q:
            cur.execute(
                """
                SELECT id, name, job
                FROM employees
                WHERE name LIKE %s OR job LIKE %s
                ORDER BY name
                """,
                (f"%{q}%", f"%{q}%"),
            )
        else:
            cur.execute(
                "SELECT id, name, job FROM employees ORDER BY name"
            )

        employees = cur.fetchall()
        conn.close()

    except Exception as e:
        print("Database error:", e)

    return render_template("index_png.html", employees=employees, q=q)


# ==================================================
# GENERATE PNG SIGNATURE (LOCKED)
# ==================================================
@app.route("/generate", methods=["POST"])
def generate():
    employee_id = request.form.get("employee_id")

    if not employee_id:
        return "Invalid request", 400

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT name, job, dept, email, mobile, phone
        FROM employees
        WHERE id = %s
        """,
        (employee_id,),
    )
    emp = cur.fetchone()
    conn.close()

    if not emp:
        return "Employee not found", 404

    # --------------------------------------------------
    # CREATE IMAGE (Outlook Safe)
    # --------------------------------------------------
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_main = ImageFont.truetype(FONT_PATH, 18)
    font_regular = ImageFont.truetype(FONT_PATH, 14)
    font_small = ImageFont.truetype(FONT_PATH, 11)

    x = 20
    y = 40
    line = 24

    # -------------------------
    # NAME
    # -------------------------
    if emp["name"]:
        draw.text((x, y), emp["name"], fill="black", font=font_main)
        y += line * 2

    # -------------------------
    # JOB + DEPT
    # -------------------------
    job_line = " | ".join(
        filter(None, [emp.get("job"), emp.get("dept")])
    )

    if job_line:
        draw.text((x, y), job_line, fill="black", font=font_regular)
        y += line * 2

    # -------------------------
    # PHONE + MOBILE (same line)
    # -------------------------
    contacts = " | ".join(
        filter(
            None,
            [
                f"T: {emp['phone']}" if emp.get("phone") else None,
                f"M: {emp['mobile']}" if emp.get("mobile") else None,
            ],
        )
    )

    if contacts:
        draw.text((x, y), contacts, fill="black", font=font_regular)
        y += line

    # -------------------------
    # EMAIL
    # -------------------------
    if emp.get("email"):
        draw.text((x, y), emp["email"], fill="black", font=font_regular)
        y += line * 2

    # -------------------------
    # DIVIDER
    # -------------------------
    divider_y = y + 10
    draw.line(
        [(x, divider_y), (IMAGE_WIDTH - 20, divider_y)],
        fill=(220, 0, 0),
        width=2,
    )

    # -------------------------
    # LOGOS
    # -------------------------
    logo_y = divider_y + 20

    if os.path.exists(LOGO_DPD):
        dpd = Image.open(LOGO_DPD).convert("RGBA")
        img.paste(dpd, (x, logo_y), dpd)

    if os.path.exists(LOGO_GEOPOST):
        geopost = Image.open(LOGO_GEOPOST).convert("RGBA")
        img.paste(
            geopost,
            (IMAGE_WIDTH - 20 - geopost.width, logo_y),
            geopost,
        )

    # -------------------------
    # FOOTER
    # -------------------------
    footer_y = logo_y + 70

    draw.text(
        (x, footer_y),
        COMPANY_NAME,
        fill="black",
        font=font_small,
    )

    draw.text(
        (x, footer_y + 15),
        ADDRESS_TEXT + " | dpd.pt",
        fill="black",
        font=font_small,
    )

    # --------------------------------------------------
    # SAVE PNG (96 DPI - Outlook Correct Scaling)
    # --------------------------------------------------
    buf = io.BytesIO()
    img.save(
        buf,
        format="PNG",
        dpi=(96, 96),
        optimize=True,
    )
    buf.seek(0)

    filename = emp["name"].replace(" ", "_") + "_signature.png"

    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name=filename,
    )


# ==================================================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
