import sys
import os
import uvicorn

print("=== RAILWAY START ===")
print("CWD:", os.getcwd())
print("Files:", os.listdir('.'))

root_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(root_dir, 'mlbb-draft-assistant')

if os.path.exists(app_dir):
    print("Found app_dir:", app_dir)
    sys.path.insert(0, app_dir)
    os.chdir(app_dir)
else:
    print("app_dir not found, files:", os.listdir(root_dir))

sys.path.insert(0, root_dir)

port = int(os.getenv("PORT", 8080))

if __name__ == "__main__":
    from api_server.main import app
    uvicorn.run(app, host="0.0.0.0", port=port)
