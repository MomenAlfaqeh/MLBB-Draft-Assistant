from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    background_color = (10, 10, 10)
    text_color = (0, 255, 65)
    
    img = Image.new('RGB', (size, size), background_color)
    draw = ImageDraw.Draw(img)
    
    text = "ML"
    font_size = int(size * 0.4)
    try:
        font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("Courier New.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) / 2
    y = (size - text_height) / 2
    
    draw.text((x, y), text, fill=text_color, font=font)
    img.save(output_path)
    print(f"Created {output_path}")

if __name__ == "__main__":
    static_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "mlbb-draft-assistant",
        "api_server",
        "static"
    )
    os.makedirs(static_dir, exist_ok=True)
    
    create_icon(192, os.path.join(static_dir, "icon-192.png"))
    create_icon(512, os.path.join(static_dir, "icon-512.png"))
    print("Icons generated successfully")
