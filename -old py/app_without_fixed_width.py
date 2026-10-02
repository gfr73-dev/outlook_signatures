from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

# Make sure output folder exists
os.makedirs('output', exist_ok=True)

# COMPANY_WEB = "https://www.dpd.pt"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form inputs
        name = request.form.get('name', '').strip()
        job = request.form.get('job', '').strip()
        dept = request.form.get('dept', '').strip()
        # company = request.form.get('company', '').strip()
        company = "DPD Portugal"
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()

        # Load logo
        logo_path = 'static/dpd_logo_50.png'
        logo = Image.open(logo_path).convert("RGBA")
        logo_width, logo_height = logo.size

        # Prepare text lines (only non-empty)
        # lines = [line for line in [name, job, dept, company, email, mobile, COMPANY_WEB] if line]
        lines = [line for line in [name, job, dept, company, '\n', email, mobile] if line]

        # Font settings
        font_path = "arial.ttf"  # adjust font path
        font_size = 14
        font = ImageFont.truetype(font_path, font_size)
        line_spacing = 3

        # Calculate text block size using Pillow 12 compatible methods
        text_width = 0
        text_height = 0
        line_heights = []
        for line in lines:
            bbox = font.getbbox(line)  # returns (x0, y0, x1, y1)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            text_width = max(text_width, w)
            text_height += h + line_spacing
            line_heights.append(h)

        text_height -= line_spacing  # remove last extra spacing

        # Define padding and spacing
        padding = 20
        padding2 = 5
        line_gap = 10
        total_width = logo_width + 2 + padding + text_width + padding
        total_height = max(logo_height, text_height + 2*padding)

        # Create output image
        img = Image.new('RGBA', (total_width, total_height), (255,255,255))
        draw = ImageDraw.Draw(img)

        # Paste logo vertically centered
        logo_y = (total_height - logo_height) // 2
        img.paste(logo, (padding2, logo_y), mask=logo)

        # Draw vertical red line
        line_x = padding + logo_width + line_gap
        draw.line([(line_x, padding2), (line_x, total_height - padding2)], fill="red", width=2)

        # Draw text vertically centered
        text_x = line_x + 10
        current_y = (total_height - text_height) // 2
        for i, line in enumerate(lines):
            draw.text((text_x, current_y), line, font=font, fill="black")
            current_y += line_heights[i] + line_spacing

        # Save to BytesIO
        output = io.BytesIO()
        img.save(output, format="PNG")
        output.seek(0)

        return send_file(output, download_name="signature.png", as_attachment=True)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
