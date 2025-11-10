import os
import sys
import threading
import time
import socket
from google.colab import userdata
from IPython.display import display, HTML
from pyngrok import ngrok, conf

# Import the main Flask app object
from app import app
from db_manager import init_db

# --- Colab/Ngrok Specific Setup ---
START_PORT = 5010
MAX_PORT_ATTEMPTS = 10

# Initialize DB (needed here to ensure it exists before Flask starts)
init_db()

try:
    # 1. Configuration (Retrieve Secrets from Colab)
    NGROK_AUTH_TOKEN = userdata.get('NGROK_AUTH_TOKEN')
    GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')

    if not NGROK_AUTH_TOKEN or not GEMINI_API_KEY:
        missing = []
        if not NGROK_AUTH_TOKEN: missing.append("NGROK_AUTH_TOKEN")
        if not GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
        raise ValueError(f"Missing Colab Secrets: {', '.join(missing)}")

    conf.get_default().auth_token = NGROK_AUTH_TOKEN

except Exception as e:
    display(HTML(f"""<h2 style="color: red;">❌ CONFIGURATION ERROR</h2><p>Failed to retrieve secrets: <strong>{e}</strong></p>"""))
    sys.exit(1)

# --- Server Start Logic ---
def run_flask_app_deployment(port):
    print(f"Starting Flask server on port {port} in background thread...")
    # Use 0.0.0.0 for compatibility, use_reloader=False is crucial for threading
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def find_available_port():
    CURRENT_PORT = START_PORT
    for _ in range(MAX_PORT_ATTEMPTS):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', CURRENT_PORT))
            s.close()
            return CURRENT_PORT
        except OSError:
            CURRENT_PORT += 1
    return None

# Find port and start server
ngrok.kill()
PORT_TO_USE = find_available_port()

if PORT_TO_USE is None:
    raise SystemExit("Could not find an available port after several attempts. Please restart Colab runtime.")

flask_thread = threading.Thread(target=run_flask_app_deployment, args=(PORT_TO_USE,))
flask_thread.daemon = True
flask_thread.start()

print(f"Waiting 3 seconds for Flask to initialize on port {PORT_TO_USE}...")
time.sleep(3)

try:
    print("Attempting to establish Ngrok tunnel...")
    for t in ngrok.get_tunnels(): ngrok.disconnect(t.public_url)
    public_url = ngrok.connect(PORT_TO_USE).public_url

    # Display Link
    display(HTML(f"""
    <h2>✅ AI Tech Tutor Running!</h2>
    <p>The application is live. Click the secure public link below to open the website:</p>
    <p><a href="{public_url}" target="_blank"><strong>{public_url}</strong></a></p>
    <p style="color:#dc2626"><b>Keep this cell running to keep the server alive.</b></p>
    """))
    print(f"\n>>>> PUBLIC NGROK URL: {public_url} <<<<\n")

    print("Server is now live. Keep this cell running to maintain the connection.")
    while True: time.sleep(1)

except Exception as e:
    print(f"\n❌ FATAL NGROK CONNECTION ERROR: {e}")
    print("Please check your Ngrok Auth Token or try restarting the Colab runtime.")

finally:
    ngrok.kill()
