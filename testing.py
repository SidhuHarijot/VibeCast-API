from fycharts.SpotifyCharts import SpotifyCharts

api = SpotifyCharts()
api.top200Daily(output_file = "temp_file/top_200_daily.csv")