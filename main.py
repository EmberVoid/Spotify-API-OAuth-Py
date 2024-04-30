import urllib
import secrets
import requests
import os

from datetime import datetime
from functools import wraps
from werkzeug.wrappers import Response
from flask import Flask, redirect, jsonify, render_template, url_for,session, request
from dotenv import load_dotenv

#
### Flask setup ###
#

app = Flask(__name__)
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
        return redirect(url_for('go_to_root_page'))
    
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
    #Zip is used to combine lists into a zip object, however in the Jinja engine, it seems I was unable to sort or go
    #throught the lists in any capacity to display them, seems like zip function returns an iterator, which can only be iterated over once.
    #Converting the zip object back to a list allowed to be iterated on Jinja 
    combined_list = list(zip(playlist_names, playlist_urls, playlist_images))

    return combined_list

#
### App Routes ###
#

@app.route('/')
def go_to_root_page():
    return render_template('login.html')

@app.route('/home')
@verify_user_session
def home():
    user = get_user()
    user_id = user.get("id")
    user_image = user.get('images', [{}])[1].get('url', None)
        
    return render_template('home.html', username=user_id, userimage=user_image)

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
    return render_template('playlists.html', combinedlist=combined_list)


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

        return redirect(url_for('home'))

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

        return redirect(url_for('home'))

#
### Logout ###
#

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect to the login page or home page
    return redirect(url_for('go_to_root_page'))
    
if __name__ == '__main__':
    debug_mode = app.config.get('DEBUG', False)

    app.run(debug=debug_mode)
