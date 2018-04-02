from stravalib.client import Client
import Configuration

def get_authorized_client(username):
    client = Client()
    token = get_access_token(username, client)
    client.access_token = token
    return client

def get_access_token(username, client):
    #Lookup Cached Result
    if hasattr(Configuration,username):
        return getattr(Configuration,username).access_token
    else:
        print("Error in access token\n")
        return -1

