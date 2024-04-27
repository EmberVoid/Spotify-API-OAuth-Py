import urllib
import secrets
import requests
import os

from datetime import datetime
from flask import Flask, redirect, jsonify, render_template, session, request
from dotenv import load_dotenv



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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    state = secrets.token_hex(16)
    scope = 'user-read-private user-read-email'

    params ={
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'state': state
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

        return redirect('/home')

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
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

        return redirect('/home')

@app.route('/home')
def get_user():
    headers = verify_user_session()    

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    user = response.json()

    #return render_template('home.html')
    return jsonify(user)

@app.route('/playlists')
def get_playlists():
    headers = verify_user_session()

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    return jsonify(playlists)

def verify_user_session():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session ['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }   

    return headers
    
if __name__ == '__main__':
    debug_mode = app.config.get('DEBUG', False)

    app.run(debug=debug_mode)
