from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
import requests
import os
import base64
import csv

app = FastAPI()

client_id = "4dc46910d266416eade1b06efd289a82"
client_secret = "abf0bf2fb6944d5a8f351e40c25ee017"

# Helper function to encode the client credentials
def get_client_credentials():
    return base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

# Step 1: Login Endpoint to Redirect User for Authorization
@app.get("/login")
def login():
    # client_id = os.getenv("SPOTIFY_CLIENT_ID")
    # print("[LOGIN]: " + ", ".join(os.environ))
    # client_id = os.environ["SPOTIFY_CLIENT_ID"]
    # print("[LOGIN]: " + os.environ)
    redirect_uri = "http://localhost:8000/callback"
    scope = "user-read-private user-read-email"
    # Direct user to Spotify authorization URL
    return RedirectResponse(
        url=f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&scope={scope}&redirect_uri={redirect_uri}"
    )

# Step 2: Callback Endpoint to Handle the Redirect from Spotify
@app.get("/callback")
def callback(code: str, state: str = None):
    print("[]")
    client_credentials = get_client_credentials()
    token_url = "https://accounts.spotify.com/api/token"
    redirect_uri = "http://vibecast-api.onrender.com//callback"
    headers = {
        "Authorization": f"Basic {client_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    response = requests.post(token_url, headers=headers, data=body)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch access token")
    
    token_data = response.json()
    access_token = token_data.get("access_token")

    # Store the token in a temporary file
    with open('temp_file/token.txt', 'w') as f:
        f.write(access_token)
    
    return {"message": "Authorization successful, token stored."}

# Helper function to retrieve the access token from a file
def get_access_token():
    try:
        with open('temp_file/token.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Token file not found")

# Step 3: Fetch Genres using the stored access token
@app.get("/fetch-genres")
def fetch_genres(access_token: str = Depends(get_access_token)):
    url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not fetch genres")
    
    genres = response.json().get('genres', [])
    if genres:
        # Save genres to a CSV file
        with open('temp_file/genres.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Genre'])
            for genre in genres:
                writer.writerow([genre])
    
    return {"message": "Genres fetched and saved successfully", "file": "temp_file/genres.csv"}

# Ensure environmental variables and temp_file directory are properly set up.
