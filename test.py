import requests

result = requests.get('http://localhost:8000/cities')


print(result.json())
