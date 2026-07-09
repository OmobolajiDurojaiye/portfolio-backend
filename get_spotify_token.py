import sys
import os
import webbrowser
import requests
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}/callback"
SCOPE = "user-read-currently-playing user-read-recently-played"

captured_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global captured_code
        if self.path.startswith("/callback"):
            query = self.path.split("?")[1] if "?" in self.path else ""
            params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
            captured_code = params.get("code")
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization Successful!</h1><p>You can close this tab and return to the terminal.</p>")
        else:
            self.send_response(404)
            self.end_headers()

def main():
    print("=========================================")
    print("   SPOTIFY CREDENTIALS GENERATOR TOOL   ")
    print("=========================================")
    print("\nStep 1: Go to: https://developer.spotify.com/dashboard")
    print("Step 2: Log in and click 'Create App'")
    print("Step 3: App Name: My Portfolio, Description: Spotify Integration")
    print(f"Step 4: Set Redirect URI to: {REDIRECT_URI}")
    print("Step 5: Check 'Web API' option under APIs/SDKs.")
    print("Step 6: Save the app, click 'Settings', and copy your Client ID and Client Secret.")
    
    try:
        client_id = input("\nEnter your SPOTIFY_CLIENT_ID: ").strip()
        client_secret = input("Enter your SPOTIFY_CLIENT_SECRET: ").strip()
    except KeyboardInterrupt:
        print("\nExiting tool.")
        return
    
    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required.")
        return

    # Generate auth URL
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "show_dialog": "true"
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    
    print("\nOpening your browser to authorize Spotify access...")
    webbrowser.open(auth_url)
    
    # Start temporary local HTTP server to receive the authorization code
    server = HTTPServer(("localhost", PORT), CallbackHandler)
    print("Waiting for authorization callback on port 8080...")
    while captured_code is None:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            print("\nExiting tool.")
            return
        
    print("\nAuthorization code captured successfully!")
    
    # Exchange code for token
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": captured_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    res = requests.post(token_url, data=payload)
    if res.status_code != 200:
        print("Error exchanging authorization code:", res.text)
        return
        
    res_data = res.json()
    refresh_token = res_data.get("refresh_token")
    
    print("\n================ SUCCESS ================")
    print(f"SPOTIFY_CLIENT_ID = {client_id}")
    print(f"SPOTIFY_CLIENT_SECRET = {client_secret}")
    print(f"SPOTIFY_REFRESH_TOKEN = {refresh_token}")
    print("=========================================")
    
    try:
        write_env = input("\nWould you like to write these credentials directly to your backend .env file? (y/n): ").strip().lower()
    except KeyboardInterrupt:
        print("\nExiting tool.")
        return
        
    if write_env == 'y':
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
                
        # Filter out existing Spotify vars
        lines = [l for l in lines if not l.strip().startswith("SPOTIFY_")]
        
        # Append new values
        lines.append(f"\nSPOTIFY_CLIENT_ID=\"{client_id}\"\n")
        lines.append(f"SPOTIFY_CLIENT_SECRET=\"{client_secret}\"\n")
        lines.append(f"SPOTIFY_REFRESH_TOKEN=\"{refresh_token}\"\n")
        
        with open(env_path, "w") as f:
            f.writelines(lines)
            
        print("Updated backend .env file successfully!")
        print("Remember to restart your Flask backend server to load the new environment variables.")

if __name__ == "__main__":
    main()
