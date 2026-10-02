from flask import (
    Flask,
    render_template,
    request,
    send_file,
    Response,
    redirect,
    url_for,
)
from PIL import Image, ImageDraw, ImageFont
import io
import mysql.connector
import base64
import urllib.parse
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1,
)

# --------------------------------------------------
# DATABASE CONFIG
# --------------------------------------------------
DB_CONFIG = {"host": "localhost", "user": "root", "password": "", "database": "dpd"}

# --------------------------------------------------
# BRAND / LAYOUT CONFIG
# --------------------------------------------------
IMAGE_WIDTH = 600
IMAGE_HEIGHT = 430
FONT_PATH = "arial.ttf"

COMPANY_NAME = "DPD Portugal SA"

ADDRESS_TEXT = (
    "Avenida Alvaro Cunhal, Lote 2 | 2660-341 Santo Antonio Cavaleiros | Portugal"
)

DPD_URL = "https://www.dpd.pt"
LINKEDIN_URL = "https://www.linkedin.com/company/dpd-portugal"
INSTAGRAM_URL = "https://www.instagram.com/dpd_portugal"

# --------------------------------------------------
# LOGOS
# --------------------------------------------------
LOGO_DPD = "static/logos/dpd_logo_50.png"
LOGO_GEOPOST = "static/logos/geopost_logo_50.png"
LOGO_LINKEDIN = "static/logos/linkedin.png"
LOGO_INSTAGRAM = "static/logos/instagram.png"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


DPD_LOGO_B64 = img_to_base64(LOGO_DPD)
GEOPOST_LOGO_B64 = img_to_base64(LOGO_GEOPOST)
LINKEDIN_B64 = img_to_base64(LOGO_LINKEDIN)
INSTAGRAM_B64 = img_to_base64(LOGO_INSTAGRAM)


# ==================================================
# INDEX + SEARCH
# ==================================================
@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "")

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
        cur.execute("SELECT id, name, job FROM employees ORDER BY name")

    employees = cur.fetchall()
    conn.close()

    return render_template("index.html", employees=employees, q=q)


# ==================================================
# GENERATE ROUTE
# ==================================================
@app.route("/generate", methods=["POST"])
def generate():
    employee_id = request.form["employee_id"]
    format_type = request.args.get("format", "html")

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

    endpoint = "signature_html" if format_type == "html" else "signature_png"

    return redirect(url_for(endpoint, **emp))


# ==================================================
# PNG SIGNATURE
# ==================================================
@app.route("/signature/png")
def signature_png():
    name = request.args.get("name", "")
    job = request.args.get("job", "")
    dept = request.args.get("dept", "")
    email = request.args.get("email", "")
    mobile = request.args.get("mobile", "")
    phone = request.args.get("phone", "")

    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    font_main = ImageFont.truetype(FONT_PATH, 16)
    font_small = ImageFont.truetype(FONT_PATH, 13)
    font_tiny = ImageFont.truetype(FONT_PATH, 11)

    x, y = 20, 20
    line = 22

    draw.text((x, y), name, fill="black", font=font_main)
    y += line * 2
    draw.text((x, y), f"{job} | {dept}", fill="black", font=font_small)
    y += line
    y += line
    draw.text((x, y), f"T: {phone}", fill="black", font=font_small)
    y += line
    draw.text((x, y), f"M: {mobile}", fill="black", font=font_small)
    y += line
    draw.text((x, y), email, fill="black", font=font_small)

    divider_y = y + line * 2
    draw.line([(x, divider_y), (IMAGE_WIDTH - 20, divider_y)], fill="red", width=2)

    logo_y = divider_y + 14

    dpd = Image.open(LOGO_DPD).convert("RGBA")
    geopost = Image.open(LOGO_GEOPOST).convert("RGBA")

    img.paste(dpd, (x, logo_y), dpd)
    img.paste(geopost, (IMAGE_WIDTH - 20 - geopost.width, logo_y), geopost)

    follow_y = logo_y + dpd.height + 8
    draw.text((x, follow_y), "Follow us on ", fill="black", font=font_tiny)

    li = Image.open(LOGO_LINKEDIN).resize((16, 16))
    ig = Image.open(LOGO_INSTAGRAM).resize((16, 16))

    img.paste(li, (x + 80, follow_y - 2), li)
    img.paste(ig, (x + 102, follow_y - 2), ig)

    address_y = follow_y + 22
    draw.text(
        (x, address_y),
        COMPANY_NAME + "\n" + ADDRESS_TEXT + " | dpd.pt",
        fill="black",
        font=font_tiny,
    )

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ==================================================
# HTML SIGNATURE (UPDATED – TEXT LINKS ONLY)
# ==================================================
@app.route("/signature/html")
def signature_html():
    params = {
        k: request.args.get(k, "")
        for k in ["name", "job", "dept", "email", "mobile", "phone"]
    }

    png_query = urllib.parse.urlencode(params)

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>

<div style="margin-bottom:12px;">
    <button onclick="copySignature()" style="padding:8px 14px;font-size:14px;">
        Copiar Assinatura
    </button>
</div>

<table id="signature" width="600" cellpadding="0" cellspacing="0"
style="font-family:Arial,sans-serif;font-size:13px;color:#000;">

<tr><td style="height:24px;line-height:24px;">&nbsp;</td></tr>

<tr>
    <td style="font-size:14px;font-weight:bold;padding-bottom:10px;">
        {params["name"]}
    </td>
</tr>

<tr><td style="padding-bottom:18px;">
{" | ".join(filter(None, [
    f"{params['job']}" if params.get("job") else None,
    f"{params['dept']}" if params.get("dept") else None
]))}<br><br>
{" | ".join(filter(None, [
    f"T: {params['phone']}" if params.get("phone") else None,
    f"M: {params['mobile']}" if params.get("mobile") else None
]))}<br>
<a href="mailto:{params["email"]}" style="color:#000;text-decoration:none;">
{params["email"]}<br>
</td></tr>

<tr><td style="border-top:2px solid red;height:20px;"></td></tr>

<tr><td>
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="left">
<img src="data:image/png;base64,{DPD_LOGO_B64}">
</td>
<td align="right">
<img src="data:image/png;base64,{GEOPOST_LOGO_B64}">
</td>
</tr>
</table>
</td></tr>

<tr><td style="font-size:11px;padding-top:8px;">
Follow us on
    <a href="{LINKEDIN_URL}" style="color:#000;text-decoration:none;">LinkedIn</a>
    &nbsp;|&nbsp;
    <a href="{INSTAGRAM_URL}" style="color:#000;text-decoration:none;">Instagram</a>
</td></tr>

<tr><td style="font-size:11px;padding-top:6px;">
{COMPANY_NAME}
</td></tr>

<tr><td style="font-size:11px;padding-top:6px;">
{ADDRESS_TEXT} |
<a href="{DPD_URL}" style="color:#000;text-decoration:none;">dpd.pt</a>
</td></tr>

</table>

<script>
function copySignature() {{
    const r = document.createRange();
    r.selectNode(document.getElementById("signature"));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(r);
    document.execCommand("copy");
    window.getSelection().removeAllRanges();
    alert("Signature copied. Paste it into Outlook.");
}}
</script>

</body>
</html>
"""
    return Response(html, mimetype="text/html")


# ==================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
