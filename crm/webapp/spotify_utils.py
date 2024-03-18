import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

def get_spotify_client():
    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp

def get_artist_info(artist_name):
    sp = get_spotify_client()
    
    results = sp.search(q='artist:' + artist_name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]  # Returns the first matching artist
    else:
        return None
