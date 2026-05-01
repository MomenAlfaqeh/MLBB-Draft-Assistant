import sys
import os

# Add the mlbb-draft-assistant directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(root_dir, 'mlbb-draft-assistant')
sys.path.insert(0, app_dir)
sys.path.insert(0, root_dir)

# Change working directory to app dir
os.chdir(app_dir)

# Now import the FastAPI app
from api_server.main import app
