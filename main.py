from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import requests
import csv
from decouple import config
from pylast import LastFMNetwork, md5

app = FastAPI()

client_id = config('SPOTIFY_CLIENT_ID')
client_secret = config('SPOTIFY_CLIENT_SECRET')
redirect_uri = config('REDIRECT_URI')
scope = "user-read-private user-read-email playlist-read-private"

# Initialize SpotifyOAuth with environment variables
sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)

lastfm_api_key = config("LASTFM_API_KEY")
lastfm_api_secret = config("LASTFM_SHARED_SECRET")
lastfm_username = config("LASTFM_USERNAME")
lastfm_password_hash = md5(config("LASTFM_PASSWORD"))
lastfm_network = LastFMNetwork(api_key=lastfm_api_key, api_secret=lastfm_api_secret, username=lastfm_username, password_hash=lastfm_password_hash)

@app.get("/fetch-top-playlist")

@app.get("/login")
def login():
    # Generate the authorization URL
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str, state: str = None):
    # Exchange code for an access token
    token_info = sp_oauth.get_access_token(code)
    if not token_info:
        raise HTTPException(status_code=400, detail="Failed to fetch access token")
    access_token = token_info['access_token']
    # Optionally store the token in some form of persistent storage (e.g., database, file)

    return {"message": "Authorization successful", "access_token": access_token}

@app.get("/fetch-playlists")
def fetch_playlists(access_token: str = Depends(sp_oauth.get_cached_token)):
    spotify = Spotify(auth=access_token)
    playlists = spotify.current_user_playlists()
    return playlists

@app.get("/fetch-top-playlist")
def fetch_top_playlist():
    spotify = Spotify(auth_manager=sp_oauth)
    # Search for 'Today's Top Hits' as an example of a popular playlist
    result = spotify.search(q="Today's Top Hits", type="playlist", limit=1, market="US")
    if not result['playlists']['items']:
        raise HTTPException(status_code=404, detail="No playlists found")
    playlist_id = result['playlists']['items'][0]['id']
    playlist = spotify.playlist(playlist_id, fields="tracks,next,name")
    tracks_info = []

    for item in playlist['tracks']['items']:
        track = item['track']
        track_name = track['name']
        artist_name = track['artists'][0]['name']  # assuming the first artist
        # Fetch tags from Last.fm
        track_tags = lastfm_network.get_track(artist_name, track_name).get_top_tags(limit=5)
        tags = [tag.item.name for tag in track_tags if tag.weight > 10]  # Example threshold for tag relevance
        tracks_info.append({
            'track_name': track_name,
            'artist_name': artist_name,
            'tags': tags
        })

    return {'playlist_name': playlist['name'], 'tracks': tracks_info}