## Setup on Android via Termux

### Step-by-step Instructions:

1. **Install Termux from F-Droid**
   - Download and install Termux from [F-Droid](https://f-droid.org/en/packages/com.termux/)
   - *Do not install from Google Play Store as it's outdated*

2. **Install Python and Dependencies**
   ```bash
   # Update package repositories
   pkg update && pkg upgrade
   
   # Install Python and pip
   pkg install python
   
   # Install required Python packages
   pip install fastapi uvicorn opencv-python numpy requests
   ```

3. **Clone or Copy Project**
   ```bash
   # Clone the repository (if you have git)
   pkg install git
   git clone https://github.com/yourusername/mlbb-draft-assistant.git
   
   # Or copy files manually using a file manager or termux-tools
   ```

4. **Run the Server**
   ```bash
   cd mlbb-draft-assistant
   python -m uvicorn api_server.main:app --host 127.0.0.1 --port 8080
   ```

5. **Keep Termux Running in Background**
   ```bash
   # Install tmux for persistent sessions
   pkg install tmux
   
   # Start a tmux session
   tmux new -s mlbb-server
   
   # Inside tmux, run the server
   python -m uvicorn api_server.main:app --host 127.0.0.1 --port 8080
   
   # Detach from tmux session with: Ctrl+b then d
   # Reattach later with: tmux attach -t mlbb-server
   ```

## Android Overlay App (Future)

The Android overlay app will be developed in a separate phase using:

### Technologies:
- **Language**: Kotlin
- **UI Framework**: Android Jetpack Compose or XML layouts
- **Screen Capture**: MediaProjection API
- **Window System**: WindowManager API (for overlay)
- **Networking**: Retrofit or OkHttp for HTTP requests to the FastAPI server

### Features:
- Capture screen during Mobile Legends draft phase
- Extract hero icons from screen using template matching (same as Python vision engine)
- Send screenshot to local FastAPI server for analysis
- Display top 5 hero recommendations as overlay
- Only active during draft phase (detected via package name or screen recognition)

### Connection to Server:
- The overlay app will connect to `http://127.0.0.1:8080` (localhost)
- Uses POST `/analyze` endpoint with base64-encoded screenshot
- Receives JSON response with recommended heroes and scores
- Displays recommendations in a non-intrusive overlay

### Development Timeline:
1. Phase 1: Basic screen capture and image sending
2. Phase 2: Template matching for hero detection (reuse Python logic)
3. Phase 3: Integration with FastAPI backend
4. Phase 4: UI/UX optimization for gaming overlay
5. Phase 5: Battery optimization and performance tuning

### Note:
For development, you can test the server functionality directly in Termux before building the Android overlay app.