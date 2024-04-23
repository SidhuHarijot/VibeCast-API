import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pylast
from decouple import config


spotify_id = config("SPOTIFY_CLIENT_ID")
spotify_secret = config("SPOTIFY_CLIENT_SECRET")

lastfm_api_key = config("LASTFM_API")
lastfm_api_secret = config("LASTFM_SHARED_SECRET")
lastfm_username = config("LASTFM_USERNAME")
lastfm_password = pylast.md5(config("LASTFM_PASSWORD"))

client_credentials_manager = SpotifyClientCredentials(client_id=spotify_id, client_secret=spotify_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

result = sp.search(q="top50", type="playlist", limit=1, market="US")
playlistId = result["playlists"]["items"][0]["id"]
print(playlistId)

result = sp.playlist(playlistId, fields="tracks")

print(result["tracks"]["items"][0]["track"]["name"])

username = "your_user_name"
password_hash = pylast.md5("your_password")

network = pylast.LastFMNetwork(
    api_key=lastfm_api_key,
    api_secret=lastfm_api_secret,
    username=lastfm_username,
    password_hash=lastfm_password,
)

