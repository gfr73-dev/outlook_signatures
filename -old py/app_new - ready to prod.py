from flask import (
    Flask, render_template, request,
    send_file, Response, redirect, url_for
)
from PIL import Image, ImageDraw, ImageFont
import io
import mysql.connector
import base64

app = Flask(__name__)

# -----------------------------
# MYSQL CONFIG
# -----------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "DPDpt12345!",
    "database": "dpd"
}

# -----------------------------
# IMAGE / BRAND CONFIG
# -----------------------------
IMAGE_WIDTH = 600
IMAGE_HEIGHT = 430
FONT_PATH = "arial.ttf"

COMPANY_NAME = "DPD Portugal"

LOGO_DPD = "static/logos/dpd_logo_50.png"
LOGO_GEOPOST = "static/logos/geopost_logo_50.png"
LOGO_LINKEDIN = "static/logos/linkedin.png"
LOGO_INSTAGRAM = "static/logos/instagram.png"

LINKEDIN_URL = "https://www.linkedin.com/company/dpdgroup"
INSTAGRAM_URL = "https://www.instagram.com/dpdgroup"
DPD_URL = "https://www.dpd.pt"

ADDRESS_TEXT = (
    "Av Alvaro Cunhal, Lote 2, 2660-341 Santo Antonio Cavaleiros, Portugal"
)

# =========================================================
# HELPERS
# =========================================================
def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

DPD_LOGO_B64 = img_to_base64(LOGO_DPD)
GEOPOST_LOGO_B64 = img_to_base64(LOGO_GEOPOST)
LINKEDIN_B64 = img_to_base64(LOGO_LINKEDIN)
INSTAGRAM_B64 = img_to_base64(LOGO_INSTAGRAM)

# =========================================================
# INDEX + SEARCH
# =========================================================
@app.route("/", methods=["GET"])
def index():
    search_query = request.args.get("q", "")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    if search_query:
        cursor.execute(
            """
            SELECT id, name, job
            FROM employees
            WHERE name LIKE %s OR job LIKE %s
            ORDER BY name
            """,
            (f"%{search_query}%", f"%{search_query}%")
        )
    else:
        cursor.execute("SELECT id, name, job FROM employees ORDER BY name")

    employees = cursor.fetchall()
    conn.close()

    return render_template("index.html", employees=employees, q=search_query)

# =========================================================
# GENERATE SIGNATURE
# =========================================================
@app.route("/generate", methods=["POST"])
def generate_signature():
    employee_id = request.form.get("employee_id")
    format_type = request.args.get("format", "png")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT name, job, dept, email, mobile
        FROM employees
        WHERE id = %s
        """,
        (employee_id,)
    )

    emp = cursor.fetchone()
    conn.close()

    endpoint = "signature_html" if format_type == "html" else "signature_png"

    return redirect(url_for(
        endpoint,
        name=emp["name"],
        job=emp["job"],
        dept=emp["dept"],
        email=emp["email"],
        mobile=emp["mobile"],
    ))

# =========================================================
# PNG SIGNATURE
# =========================================================
@app.route("/signature/png")
def signature_png():
    name = request.args.get("name", "")
    job = request.args.get("job", "")
    dept = request.args.get("dept", "")
    email = request.args.get("email", "")
    mobile = request.args.get("mobile", "")

    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    font_main = ImageFont.truetype(FONT_PATH, 16)
    font_small = ImageFont.truetype(FONT_PATH, 13)
    font_tiny = ImageFont.truetype(FONT_PATH, 11)

    x = 20
    y = 20
    line = 22

    draw.text((x, y), name, fill="black", font=font_main)
    y += line * 2
    draw.text((x, y), f"{job} | {dept}", fill="black", font=font_small)
    y += line
    draw.text((x, y), COMPANY_NAME, fill="black", font=font_small)
    y += line
    draw.text((x, y), email, fill="black", font=font_small)
    y += line
    draw.text((x, y), f"M: {mobile}", fill="black", font=font_small)

    divider_y = y + line * 3
    draw.line([(x, divider_y), (IMAGE_WIDTH - 20, divider_y)], fill="red", width=2)

    logo_y = divider_y + 14

    dpd = Image.open(LOGO_DPD).convert("RGBA")
    geopost = Image.open(LOGO_GEOPOST).convert("RGBA")

    img.paste(dpd, (x, logo_y), dpd)
    img.paste(geopost, (IMAGE_WIDTH - 20 - geopost.width, logo_y), geopost)

    follow_y = logo_y + dpd.height + 8
    draw.text((x, follow_y), "Follow us on", fill="black", font=font_tiny)

    li = Image.open(LOGO_LINKEDIN).resize((16, 16))
    ig = Image.open(LOGO_INSTAGRAM).resize((16, 16))

    img.paste(li, (x + 80, follow_y - 2), li)
    img.paste(ig, (x + 102, follow_y - 2), ig)

    address_y = follow_y + 22
    draw.text((x, address_y), ADDRESS_TEXT + " | dpd.pt", fill="black", font=font_tiny)

    img_io = io.BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)

    return send_file(img_io, mimetype="image/png")

# =========================================================
# HTML SIGNATURE (BASE64 + MATCHED)
# =========================================================
@app.route("/signature/html")
def signature_html():
    name = request.args.get("name", "")
    job = request.args.get("job", "")
    dept = request.args.get("dept", "")
    email = request.args.get("email", "")
    mobile = request.args.get("mobile", "")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Signature</title>
</head>

<body style="margin:0;padding:0;">

<!-- COPY BUTTON (not part of signature) -->
<div style="margin-bottom:12px;">
    <button onclick="copySignature()" style="
        padding:8px 14px;
        font-size:14px;
        cursor:pointer;
    ">
        Copy signature
    </button>
</div>

<!-- SIGNATURE START -->
<table id="signature" cellpadding="0" cellspacing="0" width="600"
       style="font-family:Arial,sans-serif;font-size:13px;color:#000;">

    <!-- NAME -->
    <tr>
        <td style="font-size:16px;font-weight:bold;padding-bottom:10px;">
            {name}
        </td>
    </tr>

    <!-- DETAILS -->
    <tr>
        <td style="padding-bottom:18px;">
            {job} | {dept}<br>
            {COMPANY_NAME}<br>
            <a href="mailto:{email}" style="color:#000;text-decoration:none;">
                {email}
            </a><br>
            M: {mobile}
        </td>
    </tr>

    <!-- RED LINE -->
    <tr>
        <td style="border-top:2px solid red;height:20px;"></td>
    </tr>

    <!-- LOGOS -->
    <tr>
        <td>
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <!-- LEFT LOGO -->
                    <td align="left" valign="top">
                        <!--[if gte mso 9]>
                        <v:image xmlns:v="urn:schemas-microsoft-com:vml"
                            src="data:image/png;base64,{DPD_LOGO_B64}"
                            style="width:50px;height:50px;" />
                        <![endif]-->
                        <![if !mso]>
                        <img src="data:image/png;base64,{DPD_LOGO_B64}">
                        <![endif]>
                    </td>

                    <!-- RIGHT LOGO -->
                    <td align="right" valign="top">
                        <!--[if gte mso 9]>
                        <v:image xmlns:v="urn:schemas-microsoft-com:vml"
                            src="data:image/png;base64,{GEOPOST_LOGO_B64}"
                            style="width:50px;height:50px;" />
                        <![endif]-->
                        <![if !mso]>
                        <img src="data:image/png;base64,{GEOPOST_LOGO_B64}">
                        <![endif]>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- FOLLOW US -->
    <tr>
        <td style="font-size:11px;padding-top:8px;">
            Follow us on
            <a href="{LINKEDIN_URL}">
                <img src="data:image/png;base64,{LINKEDIN_B64}"
                     width="16" height="16" style="vertical-align:middle;">
            </a>
            <a href="{INSTAGRAM_URL}">
                <img src="data:image/png;base64,{INSTAGRAM_B64}"
                     width="16" height="16" style="vertical-align:middle;">
            </a>
        </td>
    </tr>

    <!-- ADDRESS -->
    <tr>
        <td style="font-size:11px;padding-top:6px;">
            {ADDRESS_TEXT} |
            <a href="{DPD_URL}" style="color:#000;text-decoration:none;">
                dpd.pt
            </a>
        </td>
    </tr>

</table>
<!-- SIGNATURE END -->

<script>
function copySignature() {{
    const range = document.createRange();
    range.selectNode(document.getElementById("signature"));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    document.execCommand("copy");
    window.getSelection().removeAllRanges();
    alert("Signature copied. Paste it into Outlook.");
}}
</script>

</body>
</html>
"""

    return Response(html, mimetype="text/html")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
