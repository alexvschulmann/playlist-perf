import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from Tkinter import *
import tkMessageBox

from stravalib.client import Client

import spotipy
import spotipy.util as util

import AuthorizeStrava
import AuthorizeSpotify
import Configuration

import time
from functools import partial
from collections import namedtuple


# === G L O B A L ===
client = None
sp = None
tracks = []
ids = []
times = []
velos = []
alts = []
mass = None
maxVeloGoal = 4.44 # m/s (3.75 min/km)
minVeloGoal = 2.78 # m/s (6 min/km)
spotifyUser = None
stravaUser = None

class trackData(object):
    
    def __init__(self, track, score, rate, start, finish):
        self.track = track
        self.score = score
        self.rate = rate
        self.start = start
        self.finish = finish


# === W I N D O W ===
class Window(Frame):

# === L O G I N   W I N D O W ===
    def createLoginWidgets(self):
    
        self.winfo_toplevel().title("Input User Data")
    
    # === F R A M E S ===
        self.top = Frame(self)
        self.mid = Frame(self)
        self.bot = Frame(self)
        self.top.pack(side = TOP)
        self.mid.pack(side = TOP)
        self.bot.pack(side = TOP)
        
        # === U S E R   I N P U T ===
        
        # STRAVA
        self.StravaLoginLabel = Label(self, width = "20")
        self.StravaLoginLabel["text"] = "Strava Username: "
        self.StravaLoginLabel["fg"] = "#fc4c02"
        self.StravaLoginLabel.pack(in_ = self.top, side = LEFT)
        
        self.StravaLoginEntry = Entry(self)
        self.StravaLoginEntry.pack(in_ = self.top, side = RIGHT)
        
        # SPOTIFY
        self.SpotifyLoginLabel = Label(self, width = "20")
        self.SpotifyLoginLabel["text"] = "Spotify Username: "
        self.SpotifyLoginLabel["fg"] = "#1db954"
        self.SpotifyLoginLabel.pack(in_ = self.mid, side = LEFT)
        
        self.SpotifyLoginEntry = Entry(self)
        self.SpotifyLoginEntry.bind("<Return>", self.authenticate)
        self.SpotifyLoginEntry.pack(in_ = self.mid, side = RIGHT)
        
        # QUIT
        self.QuitButton = Button(self)
        self.QuitButton["text"] = "Quit"
        self.QuitButton["fg"]   = "red"
        self.QuitButton["command"] =  self.quit
        self.QuitButton.pack(in_ = self.bot, side = LEFT)
        
        # AUTHENTICATE
        self.AuthenticateButton = Button(self)
        self.AuthenticateButton["text"] = "Authenticate"
        self.AuthenticateButton.bind('<Button-1>', self.authenticate)
        self.AuthenticateButton.pack(in_ = self.bot, side = RIGHT)
        
        # FOCUS
        self.StravaLoginEntry.focus()

# === A U T H E N T I C A T E   U S E R ===
    def authenticate(self, event):
        global stravaUser, spotifyUser
        
        # DEBUGGING/TESTING PURPOSES
        if(len(self.StravaLoginEntry.get()) == 0 or len(self.SpotifyLoginEntry.get()) == 0):
            stravaUser = "avonschulmann"
            spotifyUser = "avonsch"
        else:
            while True:
                try:
                    if((getattr(Configuration, self.StravaLoginEntry.get()).type != "Strava") or (getattr(Configuration, self.SpotifyLoginEntry.get()).type != "Spotify")):
                        raise NameError("Wrong Account")
                    break
                except NameError:
                    tkMessageBox.showinfo("Login Error", "Mixed up authentication.")
                    return
                except:
                    tkMessageBox.showinfo("Login Error", "Credentials not stored in Configuration.py")
                    return

            stravaUser = self.StravaLoginEntry.get()
            spotifyUser = self.SpotifyLoginEntry.get()
        
        # Strava Authentication
        global client, mass
        client = AuthorizeStrava.get_authorized_client(stravaUser)
        athlete = client.get_athlete()
        mass = athlete.weight
        
        # Spotify Authentication
        global sp
        sp = AuthorizeSpotify.get_authorized_user(spotifyUser)
        
        # Clear Login Info
        self.top.destroy()
        self.mid.destroy()
        self.bot.destroy()
        self.createSpotifyWidgets()
    
# === S P O T I F Y   I N T E R A C T I O N
    def createSpotifyWidgets(self):
        global tracks
        # === F R A M E S ===
        self.top = Frame(self)
        self.mid = Frame(self)
        self.bot = Frame(self)
        self.top.pack(side = TOP)
        self.mid.pack(side = TOP)
        self.bot.pack(side = BOTTOM)
        
        # SPOTIFY
        self.SpotifySearchLabel = Label(self)
        self.SpotifySearchLabel["text"] = "Search for Song #" + str(len(tracks) + 1) +": "
        self.SpotifySearchLabel["fg"] = "#1db954"
        self.SpotifySearchLabel.pack(in_ = self.top, side = LEFT)
    
        self.SpotifySearchEntry = Entry(self)
        self.SpotifySearchEntry.pack(in_ = self.top, side = RIGHT)
        self.SpotifySearchEntry.bind("<Return>", self.searchSpotify)
        
        # NEXT
        self.continueButton = Button(self)
        self.continueButton["text"] = "Continue"
        self.continueButton["command"] = self.createStravaWidgets
        self.continueButton.pack(in_ = self.bot, side = RIGHT)
        
        # PLAYLIST
        self.PlaylistButton = Button(self)
        self.PlaylistButton["text"] = "Playlist Select"
        self.PlaylistButton["command"] = self.loadPlaylist
        self.PlaylistButton.pack(in_ = self.bot, side = RIGHT)
        
        # SEARCH
        self.GoButton = Button(self)
        self.GoButton["text"] = "Search"
        self.GoButton.bind('<Button-1>', self.searchSpotify)
        self.GoButton.pack(in_ = self.bot, side = RIGHT)
    
        # QUIT
        self.QuitButton = Button(self)
        self.QuitButton["text"] = "Quit"
        self.QuitButton["fg"]   = "red"
        self.QuitButton["command"] =  self.quit
        self.QuitButton.pack(in_ = self.bot, side = LEFT)
        
        # FOCUS
        self.SpotifySearchEntry.focus()

# === P L A Y L I S T   S E A R C H ===
    def loadPlaylist(self):
        # REFRAME
        self.mid.destroy()
        self.mid = Frame(self)
        self.mid.pack(side = TOP, fill = X)
        
        # RELABEL FOR BETTER INSTRUCTION
        self.SpotifySearchLabel["text"] = "Select starting song: "
        
        playlistButtons = []
        self.playlistList = []
        
        playlists = sp.user_playlists(spotifyUser)
        for i, playlist in enumerate(playlists['items']):
            self.playlistList.append(playlist)
            playlistButtons.append(Label(self, relief = FLAT))
            playlistButtons[i]["anchor"] = 'w'
            playlistButtons[i]["text"] = playlist['name']
            playlistButtons[i].bind("<Button-1>", partial(self.playListPress, i))
            playlistButtons[i].pack(in_ = self.mid, side = TOP, fill = X)

# === P L A Y L I S T   S E L E C T ===
    def playListPress(self, index, event):
        self.mid.destroy()
        self.mid = Frame(self)
        self.mid.pack(side = TOP)

        self.playlist = sp.user_playlist(spotifyUser, self.playlistList[index]['id'])

        self.playlistTrackButtons = []
        trackString = None
        self.firstSelection = -1
        for i, item in enumerate(self.playlist['tracks']['items']):
            trackString = str(i + 1) + '. ' + item['track']['name'] + ' by ' + item['track']['artists'][0]['name']
            self.playlistTrackButtons.append(Label(self))
            self.playlistTrackButtons[i]["anchor"] = 'w'
            self.playlistTrackButtons[i]["text"] = trackString
            self.playlistTrackButtons[i].bind("<Button-1>", partial(self.playlistSongPress, i))
            self.playlistTrackButtons[i].pack(in_ = self.mid, side = TOP, fill = X)

# === G R A B   F R O M   P L A Y L I S T ===
    def playlistSongPress(self, index, event):
        global tracks
        if(self.firstSelection == -1):
            self.firstSelection = index
            self.playlistTrackButtons[index]["background"] = "#1db954"
            self.playlistTrackButtons[index]["fg"] = "white"
            self.SpotifySearchLabel["text"] = "Select ending song: "
            return
        
        for i in range(self.firstSelection, index + 1):
            tracks.append(trackData(self.playlist['tracks']['items'][i]['track'],0,0,0,0))
        
        # ALLOW MANUAL ADDITION OF SONGS AGAIN
        self.top.destroy()
        self.mid.destroy()
        self.bot.destroy()
        self.createSpotifyWidgets()



# === S O N G   S E L E C T ===
    def songPress(self, index):
        global tracks
        tracks.append(trackData(self.trackList[index],0,0,0,0))
        self.top.destroy()
        self.mid.destroy()
        self.bot.destroy()
        self.createSpotifyWidgets()
    
# === D I S P L A Y   S E A R C H ===
    def searchSpotify(self, event):
        self.mid.destroy()
        self.mid = Frame(self)
        self.mid.pack(side = TOP)
        
        trackButtons = []
        self.trackList = []
        
        results = sp.search(q=self.SpotifySearchEntry.get(), limit = 10)
        for i, t in enumerate(results['tracks']['items']):
            self.trackString = str(i + 1) + '. ' + t['name'] + ' by ' + t['artists'][0]['name']
            self.trackList.append(t)
            trackButtons.append(Button(self))
            trackButtons[i]["justify"] = 'left'
            trackButtons[i]["text"] = self.trackString
            trackButtons[i]["command"] = partial(self.songPress, i)
            trackButtons[i].pack(in_ = self.mid, side = TOP, fill = X)
    
# === S T R A V A   I N T E R A C T I O N ===
    def createStravaWidgets(self):
        
        self.top.destroy()
        self.mid.destroy()
        self.bot.destroy()
        
        # === F R A M E S ===
        self.top = Frame(self)
        self.mid = Frame(self)
        self.bot = Frame(self)
        self.top.pack(side = TOP)
        self.mid.pack(side = TOP)
        self.bot.pack(side = BOTTOM)
        
        self.StravaLabel = Label(self)
        self.StravaLabel["text"] = "Select Run: "
        self.StravaLabel["fg"] = "#fc4c02"
        self.StravaLabel.pack(in_ = self.top, side = LEFT)
        
        # STRAVA
        acts = client.get_activities(limit = 10)
        global ids
        actButtons = []
        
        for i, act in enumerate(acts):
            actButtons.append(Button(self))
            actButtons[i]["text"] = act.name + " for " + str(act.distance) + " in " + str(act.elapsed_time)
            actButtons[i]["justify"] = 'left'
            actButtons[i]["command"] = partial(self.actPress, i)
            actButtons[i].pack(in_ = self.mid, side = TOP, fill = X)

            ids.append(act.id)
    
        # QUIT
        self.QuitButton = Button(self)
        self.QuitButton["text"] = "Quit"
        self.QuitButton["fg"]   = "red"
        self.QuitButton["command"] =  self.quit
        self.QuitButton.pack(in_ = self.bot, side = LEFT)

# === S E L E C T E D   A C T I V I T Y ===
    def actPress(self, index):
        global mass, tracks, songScore, times, velos, alts
        
        # GET ACTIVITY STREAM
        stream = client.get_activity_streams(ids[index], types = ['time','velocity_smooth','altitude'])
        times = stream['time'].data
        velos = stream['velocity_smooth'].data
        alts = stream['altitude'].data
        power = []
        
        # SCORING
        
        powerCapHigh = float(0.5 * mass * maxVeloGoal**2)
        powerCapLow = float(0.5 * mass * minVeloGoal**2)
        
        for i in range(0, len(times)):
            if i == 0:
                power.append(0.5 * mass * velos[i]**2)
            else:
                power.append(0.5 * mass * velos[i]**2)
        
        i = 0
        time = 0
        powerSum = 0.0
        veloSum = 0.0
        count = 0
        for track in tracks:
            powerSum = 0.0
            veloSum = 0.0
            count = 0
            track.start = time;
            time += (track.track['duration_ms'] / 1000)
            track.finish = time;
            while(i < len(times) and times[i] < time):
                powerSum += int(power[i])
                veloSum += float(velos[i])
                count += 1
                i += 1
            
            if count == 0:
                tkMessageBox.showinfo("Song Error", "Song included that was not run to.\nDefaulting to a score of zero for that/those songs.")
                break
            powerMean = float(powerSum/count)
            
            # SCALE SCORING
            if(powerMean > powerCapHigh):
                track.score = 100.0
            elif(powerMean < powerCapLow):
                track.score = 0.0
            else:
                track.score = (((powerMean - powerCapLow)/(powerCapHigh - powerCapLow)) * 100)
            track.rate = float(16.667/(veloSum/count))
        
        self.displayResults()

# === R E S U L T   D I S P L A Y ===
    def displayResults(self):
        global tracks, songScore
        self.winfo_toplevel().title("Song Scores: ")

        self.top.destroy()
        self.mid.destroy()
        
        # === F R A M E S ===
        self.top = Frame(self)
        self.left = Frame(self)
        self.right = Frame(self)
        self.top.pack(side = TOP)
        self.left.pack(side = LEFT)
        self.right.pack(side = RIGHT)
        
        self.DisplayLabel = Label(self)
        self.DisplayLabel["text"] = "Playlist Performance: "
        self.DisplayLabel["fg"] = "#fc4c02"
        self.DisplayLabel.pack(in_ = self.top, side = TOP)
    
        # === S O R T ===
        sortedTracks = sorted(tracks, key = lambda trackData: trackData.score, reverse = True)
    
        resultSongLabel = []
        resultScoreLabel = []
        
        # === P L O T ==

        fig, ax1 = plt.subplots(figsize = (9, 4))
        ax1.set_xlabel('Time (s)', fontweight = 'bold')
        ax1.set_ylabel('Speed (m/s)', fontweight = 'bold')
        ax1.plot(times, velos, color = '#fc4c02')
        ax1.yaxis.label.set_color('#fc4c02')
        ax1.set_xlim([0, times[-1]])
        
        ax2 = ax1.twinx()
        
        ax2.set_ylabel('Altitude (m)', fontweight = 'bold')
        ax2.plot(times, alts, color = '#1db954')
        ax2.yaxis.label.set_color('#1db954')
        ax2.set_xlim([0, times[-1]])
        
        for track in tracks:
            ax2.text((track.finish + track.start)/(2.0 * times[-1]), track.score/100, track.track['name'], transform = ax1.transAxes, fontsize = 8, backgroundcolor = '#000000', color = '#ffffff', rotation = 'vertical', verticalalignment = 'top', horizontalalignment = 'center', weight = 'heavy')

        fig.tight_layout()
        fig.patch.set_facecolor('#ffffff')
        
        canvas = FigureCanvasTkAgg(fig, master = root)
        canvas.get_tk_widget().configure(background='white',  highlightcolor='white', highlightbackground='white')
        canvas.show()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        
        
        # === P R I N T ===
        for i, track in enumerate(sortedTracks):
            resultSongLabel.append(Label(self))
            resultSongLabel[i]["text"] = track.track['name']  + ' by ' + track.track['artists'][0]['name']
            resultSongLabel[i]["anchor"] = 'w'
            resultSongLabel[i].pack(in_ = self.left, side = TOP, fill = X)
            
            resultScoreLabel.append(Label(self))
            resultScoreLabel[i]["text"] = str(int(track.score)) + " (" + str(round(float(track.rate),1)) + " min/km)"
            resultScoreLabel[i]["anchor"] = 'w'
            resultScoreLabel[i].pack(in_ = self.right, side = TOP, fill = X)

    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.pack()
        self.createLoginWidgets()

# === M A I N ===

root = Tk()
app = Window(master = root)
app.mainloop()
root.destroy()
