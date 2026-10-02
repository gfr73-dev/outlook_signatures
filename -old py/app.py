from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import mysql.connector

app = Flask(__name__)

# Ensure output folder exists
os.makedirs('output', exist_ok=True)

# ---------- MySQL Configuration ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',         # change if needed
    'password': 'DPDpt12345!',         # your MySQL password
    'database': 'dpd',      # your database name
    'port': 3306
}

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)  # return rows as dict
    return conn, cursor

# ---------- Pillow signature generator ----------
def generate_signature(employee):
    name = employee['name']
    job = employee['job']
    dept = employee['dept']
    email = employee['email']
    mobile = employee['mobile']
    company = "DPD Portugal"

    logo_path = 'static/dpd_logo_50.png'
    logo = Image.open(logo_path).convert("RGBA")
    logo_width, logo_height = logo.size

    lines = [name, job, dept, company, "", email, mobile]

    font_path = "./static/PlutoSansDPDRegular.ttf"
    font_size = 14
    font = ImageFont.truetype(font_path, font_size)
    line_spacing = 3

    IMG_WIDTH = 600
    IMG_HEIGHT = 120
    img = Image.new('RGBA', (IMG_WIDTH, IMG_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    padding_left = 15
    line_gap = 15
    text_start_x = padding_left + logo_width + line_gap + 5

    logo_y = (IMG_HEIGHT - logo_height) // 2
    img.paste(logo, (padding_left, logo_y), mask=logo)

    line_x = padding_left + logo_width + line_gap
    draw.line([(line_x, 2), (line_x, IMG_HEIGHT - 2)], fill="red", width=2)

    line_heights = []
    text_height = 0
    for line in lines:
        bbox = font.getbbox(line if line else "A")
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        text_height += h + line_spacing
    text_height -= line_spacing

    current_y = (IMG_HEIGHT - text_height) // 2
    for i, line in enumerate(lines):
        draw.text((text_start_x, current_y), line, font=font, fill="black")
        current_y += line_heights[i] + line_spacing

    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return send_file(output, download_name=f"{name}.png", as_attachment=True)

# ---------- Flask routes ----------
@app.route('/', methods=['GET', 'POST'])
def index():
    conn, cursor = get_db_connection()

    # Handle POST: generate signature
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        cursor.execute(
            "SELECT name, job, dept, email, mobile FROM employees WHERE id = %s",
            (employee_id,)
        )
        employee = cursor.fetchone()
        conn.close()
        return generate_signature(employee)

    # Handle GET: optional search
    search_query = request.args.get('q', '').strip()
    if search_query:
        cursor.execute(
            """
            SELECT id, name, job FROM employees
            WHERE name LIKE %s OR job LIKE %s
            ORDER BY name
            """,
            (f"%{search_query}%", f"%{search_query}%")
        )
    else:
        cursor.execute("SELECT id, name, job FROM employees ORDER BY name")

    employees = cursor.fetchall()
    conn.close()
    return render_template('index.html', employees=employees, q=search_query)

# ---------- Run Flask ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
