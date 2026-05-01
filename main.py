import sys
import os

print("=== RAILWAY DEBUG ===")
print("Current working directory:", os.getcwd())
print("Files in current dir:", os.listdir('.'))
print("Python path:", sys.path[:3])

# Try to find the app
root_dir = os.path.dirname(os.path.abspath(__file__))
print("Root dir:", root_dir)
print("Root dir files:", os.listdir(root_dir))

app_dir = os.path.join(root_dir, 'mlbb-draft-assistant')
if os.path.exists(app_dir):
    print("App dir found:", os.listdir(app_dir))
    sys.path.insert(0, app_dir)
    os.chdir(app_dir)
else:
    print("ERROR: mlbb-draft-assistant not found!")
    print("Trying subdirs:", [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])

sys.path.insert(0, root_dir)

from api_server.main import app
