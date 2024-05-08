import urllib
import secrets
import requests
import os

from datetime import datetime
from functools import wraps
from werkzeug.wrappers import Response
from flask_bootstrap import Bootstrap5
from flask import Flask, redirect, jsonify, render_template, url_for,session, request
from dotenv import load_dotenv

#
### Flask setup ###
#

app = Flask(__name__, static_folder='static', static_url_path='/')

#start boostrap
bootstrap = Bootstrap5(app)
#config.py loads secret key
app.config.from_object('config')
secret_key = app.config['SECRET_KEY']

#.env loads various api details  
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
API_BASE_URL = os.getenv('API_BASE_URL')

#
### Functions ###
#

# Function to get headers or redirect if the session is invalid
def get_headers_or_redirect():
    if 'access_token' not in session:
        return redirect(url_for('go_to_homepage'))
    
    elif datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    return {'Authorization': f"Bearer {session['access_token']}"}

# Decorator to verify user session
def verify_user_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = get_headers_or_redirect()
        if isinstance(response, Response):
            return response
        return f(*args, **kwargs)
    return decorated_function

def get_user():
    headers = get_headers_or_redirect()
    # Check if headers is a redirect response
    if isinstance(headers, Response):
        return headers

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    user = response.json()
    return user


#Gets all the playlists of the user in a single json variable
def get_playlist_list_json():
    headers = get_headers_or_redirect()
    # Check if headers is a redirect response

    if isinstance(headers, Response):
        return headers
    
    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    return playlists

#Divide the single json from (get_playlist_list_json) into multiple lists
##list with all the playlist names
def get_playlist_names(playlist_list):
    playlist_names = []
    
     # Iterate over each item in the 'items' list
    for item in playlist_list.get('items', []):
        # Add the 'name' to the names list
        playlist_names.append(item.get('name'))

    return playlist_names

##list with all the playlist urls to spotify
def get_playlist_urls(playlist_list):
    playlist_urls = []

    # Iterate over each item in the 'items' list
    for item in playlist_list.get('items', []):
        # Add the 'urls' to the url list
        playlist_urls.append(item.get('external_urls', {}).get('spotify'))
    
    return playlist_urls

##list with all the playlist images
def get_playlist_images(playlist_list):
    playlist_images = []

    # Iterate over each item in the 'items' list
    for item in playlist_list.get('items', []):
        # Add the 'image' to the image url list
        playlist_images.append(item['images'][0].get('url'))

    return playlist_images

#Gets all the previous lists, merges them into a single zip file then into a single interable list
def get_combine_playlist(playlist_names, playlist_urls, playlist_images):
    track_list = []
    
    # Combine the lists into a single list of dictionaries
    for name, url, img_url in zip(playlist_names, playlist_urls, playlist_images):
        track_info = {
            "Playlist Name": name,
            "Playlist URL": url,
            "Image URL": img_url
        }
        track_list.append(track_info)

    return track_list

#Try to get an artist from the search
def get_artist_list_json(artist_name):
    headers = get_headers_or_redirect()
    # Check if headers is a redirect response

    if isinstance(headers, Response):
        return headers
    
    #"Search for Item" Spotify API, limited to 3 items
    url = f"{API_BASE_URL}search?q={artist_name}&type=artist&limit=3" #https: //api.spotify.com/v1/search?q={USERINPUT}&type=artist&limit=3
    response = requests.get(url, headers=headers)
    artist_list_json = response.json() #This returns a big JSON with a lot of information

    return artist_list_json

def get_artist_ids_json(artist_search_result):
    #For this specific scenario we don't require most of the JSON from artist_list_json, only the IDs
    artist_ids = [artist["id"] for artist in artist_search_result["artists"]["items"]]
    #For example this returns similar to:
    #['4zjO8Jhi2pciJJzd8Q6rga', '5d649pWJhCaGTei93Ez0jZ', '6yUy3tj1ySuBdAl6W7ECAl']

    return artist_ids

def get_artist_top_songs_json(artist_ids):
    headers = get_headers_or_redirect()
    # Check if headers is a redirect response

    if isinstance(headers, Response):
        return headers
    
    #Get Artist's Top Tracks Spotify API, this case the first artist is the only one retrieve
    #As it is most likely the best match for the search 
    url = f"{API_BASE_URL}artists/{artist_ids[0]}/top-tracks"
    response = requests.get(url, headers=headers)
    artist_top_songs_json = response.json()

    return artist_top_songs_json

def get_format_track_info_list(artist_top_songs):
    #Similarly the top 10 tracks also gather a lot of information.
    #But for this example we only require a handful of details to create the UI cards
    track_info_list = []
    
    #We create an empty list and then
    #iterate through each track in the JSON data to get the data needed for the UI cards.
    for track in artist_top_songs["tracks"]:
        track_info = {
            "Track Name": track["name"],
            "Album Artist Name": track["album"]["artists"][0]["name"],
            "Album URL": track["album"]["external_urls"]["spotify"],
            "Album Image URL": track["album"]["images"][0]["url"],
            "Track Preview URL": track["preview_url"]
        }
        track_info_list.append(track_info)

    return track_info_list

    

#
### App Routes ###
#

@app.route('/')
def go_to_homepage():
    return render_template('homepage.html')

@app.route('/dashboard')
@verify_user_session
def user_dashboard():
    user = get_user()
    user_id = user.get("id")
    user_image = user.get('images', [{}])[1].get('url', None)
        
    return render_template('dashboard.html', username=user_id, userimage=user_image)

@app.route('/playlists')
@verify_user_session
def get_playlists():
    #Gets the playlists of the account (gets all playlists)
    playlist_list = get_playlist_list_json()

    #Separate the playlists in multiple lists
    playlist_names = get_playlist_names(playlist_list)
    playlist_urls = get_playlist_urls(playlist_list)
    playlist_images = get_playlist_images(playlist_list)

    #Merges the lists in a single list 
    combined_list = get_combine_playlist(playlist_names, playlist_urls, playlist_images)

    #Sends list to html engine to be processed
    #return combined_list
    return jsonify({'playlists': combined_list})

@app.route('/search_any_artist_match', methods=['POST'])
@verify_user_session
def search_any_artist_match():
    try:
        data = request.get_json()
        artist_name = data.get('artistName')

        #Perform the search based on artist_name
        artist_search_result = get_artist_list_json(artist_name)
        #Gets the ID of the artists
        artist_ids = get_artist_ids_json(artist_search_result)
        #Uses the first ID to get the top 10 songs
        artist_top_songs = get_artist_top_songs_json(artist_ids)
        #Gets only the necesary data from the 10 songs
        format_track_info_list = get_format_track_info_list(artist_top_songs)

        return jsonify({'tracks': format_track_info_list})
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/searcher')
@verify_user_session
def go_to_searcher():
    return render_template('searcher.html')

#
### Login ###
#

@app.route('/login')
def login():
    state = secrets.token_hex(16)
    scope = 'user-read-private user-read-email'

    params ={
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'state': state,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}{urllib.parse.urlencode(params)}"

    return redirect(auth_url)


@app.route('/callback/spotify')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri' : REDIRECT_URI,
            'client_id' : CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect(url_for('user_dashboard'))

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect(url_for('/'))
    
    if datetime.now().timestamp() > session ['expires_at']:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id' : CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect(url_for('user_dashboard'))

#
### Logout ###
#

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect to the login page or home page
    return redirect(url_for('go_to_homepage'))

#
### Error Handling ###
#
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404
    
if __name__ == '__main__':
    from waitress import serve
    serve(app, host="127.0.0.1", port=8080)
