import spotipy
import spotipy.util as util
import Configuration

def get_authorized_user(username):
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username,
                                       scope,
                                       client_id = getattr(Configuration, username).client_id,
                                       client_secret = getattr(Configuration, username).client_secret,
                                       redirect_uri = getattr(Configuration, username).access_token)

    if token:
        return spotipy.Spotify(auth = token)
    else:
        print "Can't get token for", username
        return -1
