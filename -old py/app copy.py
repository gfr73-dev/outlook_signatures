from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

os.makedirs('output', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        job = request.form.get('job', '').strip()
        dept = request.form.get('dept', '').strip()
        company = "DPD Portugal"
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()

        logo_path = 'static/dpd_logo_50.png'
        logo = Image.open(logo_path).convert("RGBA")
        logo_width, logo_height = logo.size

        lines = [line for line in [name, job, dept, company, "", email, mobile] if line is not None]

        font_path = "./static/PlutoSansDPDRegular.ttf"
        font_size = 12
        font = ImageFont.truetype(font_path, font_size)
        line_spacing = 3

        # ----------------------------
        # FIXED IMAGE SIZE (KEY CHANGE)
        # ----------------------------
        IMG_WIDTH = 600
        IMG_HEIGHT = 120

        img = Image.new('RGBA', (IMG_WIDTH, IMG_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        padding_left = 15
        line_gap = 15
        text_start_x = padding_left + logo_width + line_gap + 5

        # Center logo vertically
        logo_y = (IMG_HEIGHT - logo_height) // 2
        img.paste(logo, (padding_left, logo_y), mask=logo)

        # Red vertical separator
        line_x = padding_left + logo_width + line_gap
        draw.line(
           [(line_x, 2), (line_x, IMG_HEIGHT - 2)],
            fill="red",
            width=2
        )

        # Calculate text block height ONLY for vertical centering
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

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
