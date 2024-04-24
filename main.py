from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import dotenv
import os

app = FastAPI()

envFile = dotenv.find_dotenv()
dotenv.load_dotenv(envFile)


client_id = dotenv.get_key(envFile, 'SPOTIFY_CLIENT_ID')
client_secret = dotenv.get_key(envFile, 'SPOTIFY_CLIENT_SECRET')
redirect_uri = dotenv.get_key(envFile, 'REDIRECT_URI')  # Ensure this is set to your server/callback endpoint
scope = "playlist-read-private"

sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)

@app.get("/login")
def login():
    """ Redirect to Spotify to authorize and get the initial refresh token """
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str):
    """ Handle callback from Spotify, store refresh token """
    token_info = sp_oauth.get_access_token(code)
    if 'refresh_token' in token_info:
        dotenv.set_key(envFile, "SPOTIFY_REFRESH_TOKEN", token_info['refresh_token'])
        return {"message": "Authentication successful", "refresh_token": token_info['refresh_token']}
    else:
        raise HTTPException(status_code=500, detail="Failed to obtain refresh token")

def get_spotify_client():
    """ Returns a Spotify client using the refresh token for automated access token renewal """
    refresh_token = dotenv.get_key(envFile, 'SPOTIFY_REFRESH_TOKEN')
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found. Please log in.")
    
    token_info = sp_oauth.refresh_access_token(refresh_token)
    return Spotify(auth=token_info['access_token'])

@app.get("/top-50/{country_code}")
def get_top_50(country_code: str):
    spotify = get_spotify_client()
    results = spotify.search(q="top 50", type='playlist', limit=50, market=country_code)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)