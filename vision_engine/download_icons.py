import requests
import os
import json
from PIL import Image, ImageDraw, ImageFont

# Define paths
HEROES_BACKUP_PATH = 'data_pipeline/heroes_backup.json'
OUTPUT_DIR = 'vision_engine/hero_icons'

# Role-based color map (RGB tuples)
ROLE_COLORS = {
    "Tanks": (0, 0, 255),       # Blue
    "Fighters": (255, 0, 0),    # Red
    "Assassins": (128, 0, 128), # Purple
    "Mages": (0, 255, 255),     # Cyan
    "Marksmen": (255, 255, 0),  # Yellow
    "Supports": (0, 128, 0)     # Green
}

def download_or_create_hero_icons():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load hero data
    with open(HEROES_BACKUP_PATH, 'r') as f:
        heroes_data = json.load(f)
    
    downloaded_count = 0
    placeholder_count = 0

    # Prepare a font for drawing hero names on placeholders
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 10) # Common font on Linux
    except IOError:
        font = ImageFont.load_default()

    for hero_info in heroes_data:
        hero_name = hero_info['hero_name']
        hero_role = hero_info['role']
        filepath = os.path.join(OUTPUT_DIR, f'{hero_name}.png')
        
        # Standardize hero name for URL (remove spaces, special chars, lowercase, etc.)
        # For these specific URLs, direct hero name might not always work, 
        # but we'll try as per instruction.
        hero_name_for_url = hero_name.replace(" ", "_").replace("'", "").lower()
        
        # Attempt download from URL 1
        url1 = f"https://static.wikia.nocookie.net/mobile-legends/images/search?query={hero_name_for_url}"
        # Attempt download from URL 2 (this is a wiki page, likely won't directly download an image)
        url2 = f"https://mlbb.fandom.com/wiki/{hero_name_for_url}"

        image_downloaded = False
        for url_to_try in [url1, url2]:
            try:
                response = requests.get(url_to_try, stream=True, timeout=5) # 5-second timeout
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                
                # Check if content type is an image
                if 'image' in response.headers.get('Content-Type', ''):
                    with open(filepath, 'wb') as out_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            out_file.write(chunk)
                    print(f"Downloaded {hero_name} icon from {url_to_try} successfully.")
                    image_downloaded = True
                    downloaded_count += 1
                    break # Stop trying URLs if successful
                else:
                    print(f"Skipping {url_to_try} for {hero_name}: Content-Type is not an image.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {hero_name} icon from {url_to_try}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {url_to_try} for {hero_name}: {e}")

        if not image_downloaded:
            # Create placeholder image
            img = Image.new('RGB', (64, 64), color=ROLE_COLORS.get(hero_role, (100, 100, 100))) # Default gray
            draw = ImageDraw.Draw(img)
            
            # Draw hero name text
            text_width, text_height = draw.textsize(hero_name, font=font)
            text_x = (64 - text_width) / 2
            text_y = (64 - text_height) / 2
            draw.text((text_x, text_y), hero_name, font=font, fill=(255, 255, 255)) # White text
            
            img.save(filepath)
            print(f"Created placeholder for {hero_name} (Role: {hero_role}).")
            placeholder_count += 1
            
    print(f"\nTotal: {downloaded_count} icons downloaded, {placeholder_count} placeholders created.")

if __name__ == '__main__':
    download_or_create_hero_icons()
