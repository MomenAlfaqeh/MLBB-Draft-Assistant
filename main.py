import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mlbb-draft-assistant'))
os.chdir(os.path.join(os.path.dirname(__file__), 'mlbb-draft-assistant'))

from api_server.main import app
