import requests

baseurl = "https://vibecast-api.onrender.com/"

# try to get the tracks from the playlist
response = requests.get(baseurl + "top-50/US")

# check if the request was successful
if response.status_code == 200:
    print(response.json())
elif response.status_code == 401:
    requests.get(baseurl + "login")
