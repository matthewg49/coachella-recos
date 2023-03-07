import spotipy
import pandas as pd
import numpy as np
import networkx as nx

from spotipy.oauth2 import SpotifyClientCredentials
from creds import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET

COACHELLA_SPOTIFY_PLAYLIST = '1RIp2yQ4yyNuFHqP80pCpz'

#authenticate
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))


playlist_pull_1 = spotify.playlist_tracks(playlist_id=COACHELLA_SPOTIFY_PLAYLIST, fields='items.track.artists(id,name)')
playlist_pull_2 = spotify.playlist_tracks(playlist_id=COACHELLA_SPOTIFY_PLAYLIST, fields='items.track.artists(id,name)', offset=100)


def parsing(playlist):
    list_of_artists = []
    for artist in playlist['items']:
        dic = artist['track']['artists'][0]
        artist_details = spotify.artist(dic['id'])
        similar_artists = [i['name'] for i in spotify.artist_related_artists(dic['id'])['artists']]
        dic['genres'] = artist_details['genres']
        dic['popularity'] = artist_details['popularity']
        dic['similar_artists'] = similar_artists
        list_of_artists.append(dic)
    return list_of_artists

@st.cache_data
def data_pull():
    final_list = parsing(playlist_pull_1) + parsing(playlist_pull_2)
    df = pd.DataFrame(final_list)
    return df

df = data_pull()

st.dataframe(df)

network = df.explode('similar_artists', ignore_index=True)

network['weight'] = network.groupby('name')['index'].rank(ascending=False) / 20
network['name'] = network['name'].astype('str')
network['similar_artists'] = network['similar_artists'].astype('str')
network = network.replace(to_replace='None', value=np.nan).dropna()

G_large = nx.from_pandas_edgelist(network, 'name', 'similar_artists', ["weight"])

pairs_test = dict(nx.all_pairs_dijkstra_path_length(G_large))

f1 = {k:v for (k,v) in pairs_test.items() if k in list(df.name)}

f2 = {}
for k,v in f1.items():
  filtered_recos = {}
  for k2, v2 in v.items():
    if k2 in list(df.name):
      filtered_recos[k2] = v2
  f2[k] = filtered_recos

dictonary_recommendations = f2