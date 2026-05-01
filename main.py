import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(root_dir, 'mlbb-draft-assistant')
sys.path.insert(0, app_dir)
sys.path.insert(0, root_dir)
os.chdir(app_dir)

from api_server.main import app
