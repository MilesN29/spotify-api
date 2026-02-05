"""
Spotify Now Playing - Flask Server
Returns my currently playing track, recently played, and top artists.

Run locally: python main.py 
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
import base64
import os

app = Flask(__name__)

# allow requests from website (including www and http variants)
CORS(app, origins=[
    'https://milesnewland.com',
    'https://www.milesnewland.com',
    'http://milesnewland.com',
    'http://www.milesnewland.com',
    'http://localhost:3000',
])

# these will be set as environment variables (or you can hardcode for testing)
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', 'your_client_id_here')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', 'your_client_secret_here')
REFRESH_TOKEN = os.environ.get('SPOTIFY_REFRESH_TOKEN', 'your_refresh_token_here')


def get_access_token():
    """use the refresh token to get a fresh access token"""
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers={
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data={
            'grant_type': 'refresh_token',
            'refresh_token': REFRESH_TOKEN
        }
    )
    
    return response.json().get('access_token')


def get_currently_playing(access_token):
    """get the currently playing track"""
    response = requests.get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if response.status_code == 204 or response.status_code == 202:
        print("Nothing currently playing (204/202)")
        return None  # nothing playing
    
    if response.status_code != 200:
        print(f"Currently playing error: {response.text}")
        return None
        
    data = response.json()
    
    if not data or not data.get('item'):
        print("No item in response")
        return None
    
    item = data['item']
    return {
        'isPlaying': data.get('is_playing', False),
        'name': item.get('name'),
        'artist': ', '.join([artist['name'] for artist in item.get('artists', [])]),
        'album': item.get('album', {}).get('name'),
        'albumArt': item.get('album', {}).get('images', [{}])[0].get('url'),
        'trackUrl': item.get('external_urls', {}).get('spotify')
    }


def get_recently_played(access_token, limit=5):
    """get recently played tracks"""
    response = requests.get(
        f'https://api.spotify.com/v1/me/player/recently-played?limit={limit}',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    print(f"Recently played status: {response.status_code}")
    if response.status_code != 200:
        return []
    
    data = response.json()
    tracks = []
    
    for item in data.get('items', []):
        track = item.get('track', {})
        tracks.append({
            'name': track.get('name'),
            'artist': ', '.join([artist['name'] for artist in track.get('artists', [])]),
            'album': track.get('album', {}).get('name'),
            'albumArt': track.get('album', {}).get('images', [{}])[0].get('url'),
            'trackUrl': track.get('external_urls', {}).get('spotify'),
            'playedAt': item.get('played_at')
        })
    
    return tracks


def get_top_artists(access_token, limit=5, time_range='short_term'):
    """get top artists (short_term = last 4 weeks)"""
    response = requests.get(
        f'https://api.spotify.com/v1/me/top/artists?limit={limit}&time_range={time_range}',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    artists = []
    
    for artist in data.get('items', []):
        artists.append({
            'name': artist.get('name'),
            'image': artist.get('images', [{}])[0].get('url') if artist.get('images') else None,
            'genres': artist.get('genres', [])[:3],
            'url': artist.get('external_urls', {}).get('spotify')
        })
    
    return artists


def get_top_tracks(access_token, limit=5, time_range='short_term'):
    """get top tracks (short_term = last 4 weeks)"""
    response = requests.get(
        f'https://api.spotify.com/v1/me/top/tracks?limit={limit}&time_range={time_range}',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    tracks = []
    
    for track in data.get('items', []):
        tracks.append({
            'name': track.get('name'),
            'artist': ', '.join([artist['name'] for artist in track.get('artists', [])]),
            'album': track.get('album', {}).get('name'),
            'albumArt': track.get('album', {}).get('images', [{}])[0].get('url'),
            'trackUrl': track.get('external_urls', {}).get('spotify')
        })
    
    return tracks


@app.route('/')
def home():
    """health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Spotify API server is running'})


@app.route('/now-playing')
def now_playing():
    """get currently playing track"""
    try:
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token'}), 500
        
        data = get_currently_playing(access_token)
        return jsonify({'currentlyPlaying': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/recently-played')
def recently_played():
    """get recently played tracks"""
    try:
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token'}), 500
        
        data = get_recently_played(access_token, limit=5)
        return jsonify({'recentlyPlayed': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/top-artists')
def top_artists():
    """get top artists (last 4 weeks)"""
    try:
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token'}), 500
        
        data = get_top_artists(access_token, limit=5)
        return jsonify({'topArtists': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/top-tracks')
def top_tracks():
    """get top tracks (last 4 weeks)"""
    try:
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token'}), 500
        
        data = get_top_tracks(access_token, limit=5)
        return jsonify({'topTracks': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/all')
def all_data():
    """get all spotify data in one request"""
    try:
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get access token'}), 500
        
        response_data = {
            'currentlyPlaying': get_currently_playing(access_token),
            'recentlyPlayed': get_recently_played(access_token, limit=5),
            'topArtists': get_top_artists(access_token, limit=5),
            'topTracks': get_top_tracks(access_token, limit=5)
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # run locally on port 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
