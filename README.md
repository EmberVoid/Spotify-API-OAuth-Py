# Basic Web App using Spotify API 
This is a work in progress for learning python and API usage

Start app:
pipenv run python main.py

Work-in-progress
ToDo:
On current implementation it seems that playlists.html and style.css may no longer be needed, review for deletion.
Currently on dashboard.html I have the ajax call added directly into the file, want to check if it is possible and if it would be better to have it on it separate js file.
Research to a way to better create the jsonify({'playlists': combined_list}) to be able to utilize it in the ajax call, in a more friendly name, for example instead of ${playlist[0]}, use ${playlist.name}
Add Searcher functionality

--Footer
Vinyl icons created by Freepik - Flaticon
Spotify sketch icons created by Fathema Khanom - Flaticon