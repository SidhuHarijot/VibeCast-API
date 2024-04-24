from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import dotenv
from pydantic import BaseModel
import csv
import pylast

# This will hold all city data from the CSV file
all_cities = {}


app = FastAPI()

@app.on_event("startup")
def load_city_data():
    with open('data/worldcities.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            all_cities.append(Cities(
                name=row['city_ascii'],
                country=row['country'],
                iso2=row['iso2'],
                lat=float(row['lat']),
                lon=float(row['lng'])
            )
            )
            all_cities[row['city_ascii']] = {"country": row['country'], "iso2": row['iso2'], "lat": float(row['lat']), "lon": float(row['lng'])}

envFile = dotenv.find_dotenv()
dotenv.load_dotenv(envFile)

pylastNetwork = pylast.LastFMNetwork(api_key=dotenv.get_key(envFile, 'LASTFM_API_KEY'), api_secret=dotenv.get_key(envFile, 'LASTFM_SHARED_SECRET'))

client_id = dotenv.get_key(envFile, 'SPOTIFY_CLIENT_ID')
client_secret = dotenv.get_key(envFile, 'SPOTIFY_CLIENT_SECRET')
redirect_uri = dotenv.get_key(envFile, 'REDIRECT_URI')  # Ensure this is set to your server/callback endpoint
scope = "playlist-read-private playlist-modify-public playlist-modify-private"
openweather_api_key = dotenv.get_key(envFile, "WEATHER_API")

sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)

class Track(BaseModel):
    name: str
    genre: list[str]
    id: str

class Cities(BaseModel):
    name: str
    country: str
    iso2: str
    lat: float
    lon: float


class PlayList(BaseModel):
    name: str
    id: str
    tracks: list[Track]


class CompleteResponse(BaseModel):
    weatherCode: int
    weatherDescription: str
    playlist: PlayList

@app.get("/cities", response_model=list[Cities])
def get_cities():
    return all_cities

@app.get("/login")
def login():
    """ Redirect to Spotify to authorize and get the initial refresh token """
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/moodFiltered", response_model=CompleteResponse)
async def get_mood_filtered(city: str):
    """ Get the mood-filtered playlist for a city """
    # Find the city in the list of cities
    cityData = all_cities.get(city)
    lat, lon = cityData.get('lat'), cityData.get('lon')
    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid={openweather_api_key}&units=metric"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(weather_url)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Error fetching weather data")

    weather_data = resp.json()
    weather_condition = weather_data["current"]["weather"][0]["main"]
    
    # Map the weather condition to a mood
    mood = WEATHER_TO_MOOD.get(weather_condition, "Neutral")

    # Use mood to filter Spotify playlists (Placeholder: Implement Spotify API call to fetch playlists by mood)
    # playlists = ...

    # Construct and return the complete response
    return CompleteResponse(
        weatherCode=weather_data["current"]["weather"][0]["id"],
        weatherDescription=weather_data["current"]["weather"][0]["description"],
        playlist=PlayList(
            name="Playlist for " + mood,
            id="spotify_playlist_id",  # Placeholder
            tracks=[]  # Placeholder: This should be a list of Track objects
        )
    )

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
    tracks = spotify.playlist_tracks(results['playlists']['items'][0]['id'], fields='items(track(name, id, artists(id,name)))')
    tracksList = []
    for track in tracks["items"]:
        lastfmTrack = pylastNetwork.get_track(track['track']['artists'][0]['name'], track['track']['name'])
        tags = lastfmTrack.get_top_tags()
        taglist = []
        for tag in tags:
            taglist.append(tag.item.get_name())
        if tags:
            tracksList.append(Track(name=track['track']['name'], id=track['track']['id'], genre=taglist))
        else:
            tracksList.append(Track(name=track['track']['name'], id=track['track']['id'], genre=[""]))
    return PlayList(name="Top 50 ", id=results['playlists']['items'][0]['id'], tracks=tracksList)

@app.get("/spotify-playlist/")
def create_playlist(playlist: PlayList):
    spotify = get_spotify_client()
    tracks = playlist.tracks
    track_ids = [track.id for track in tracks]
    username = spotify.current_user()['id']
    playlist_created = spotify.user_playlist_create(user=username, name=playlist.name, public=True)
    playlist_id = playlist_created['id']
    spotify.user_playlist_add_tracks(user=username, playlist_id=playlist_id, tracks=track_ids)
    return playlist_created["external_urls"]["spotify"]

if __name__ == "__main__":
    playlist = get_top_50("US")
    create_playlist(playlist)
    print("Playlist created successfully")
    print(playlist)
