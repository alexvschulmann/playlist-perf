from collections import namedtuple

# === S T R A V A === #
StravaUser = namedtuple("Strava_User","type username client_id client_secret access_token")


avonschulmann = StravaUser(type = "Strava",
                           username = "avonschulmann",
                           client_id = 22743,
                           client_secret = "ab1d9a0195e4cdeb9dac342fbc6409ebb1b9d60d",
                           access_token = "4ec9d3ad2ce4242826b6c44534e096715fe01e6a")

# === S P O T I F Y === #
SpotifyUser = namedtuple("Spotify_User","type username client_id client_secret access_token")

avonsch = SpotifyUser(type = "Spotify",
                      username = "avonsch",
                      client_id = "e397757afad14804bdee4798ca665f2d",
                      client_secret = "eb6aad57ff324038880c515756e03241",
                      access_token = "http://localhost/?code=AQBiUxGhSQmFpPcOQ2I_GvhJdW402Ezyviw_FmEugLYk4L7yicbfjPva4fnk_MLC6WATDXaifhK3CYMMES3HraDHIZNbm-3VF3bAj7D3L-nkBjd9I_ehjNaFPE90Z-V9eYvARSgihAv60OO2NLKMx9_dUvmAFl37OOALvERaOKWUazG_cFxxrrvH1bdxhR9itsokYOHfIQHmmQ")


