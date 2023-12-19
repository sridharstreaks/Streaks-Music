import streamlit as st
import pandas as pd
import pickle
import requests
import numpy as np

# Load data and similarity from pickle files
mini = pickle.load(open('mini.pkl','rb'))
similarity = np.load('similarity.npz')
similarity = similarity['arr_0']

def search_musicbrainz(artist, song_title):
     # Initialize variables with default values
    mb_title = "N/A"
    mb_artist = "N/A"
    mb_release_date = "N/A"
    
    base_url = "https://musicbrainz.org/ws/2/"
    search_url = f"{base_url}recording/"

    # Set up parameters for the search
    params = {
        'query': f'artist:"{artist}" AND recording:"{song_title}"',
        'fmt': 'json',
        'limit': 1  # Limit the result to only one recording
    }

    # Make the request to the MusicBrainz API
    response = requests.get(search_url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Check if there are any recordings in the response
        if 'recordings' in data:
            recordings = data['recordings']

            # Print details for the top recording found
            if recordings:
                recording = recordings[0]
                mb_title=recording['title']
                print(f"Title: {mb_title}")
                mb_artist=', '.join(artist['name'] for artist in recording.get('artist-credit', []))
                print(f"Artist: {mb_artist}")
                mb_release_date=recording.get('first-release-date', 'N/A')
                print(f"Release Date: {mb_release_date}")
                print(f"ID: {recording['id']}")

                # Get album art from Deezer
                album_art_url = get_deezer_album_art(artist, song_title)
                if album_art_url:
                    print(f"Album Art: {album_art_url}")
                else:
                    print("No album art found.")

                print("\n-----\n")
            else:
                print("No recordings found.")
        else:
            print("No recordings found.")
    else:
        print(f"Error: {response.status_code} - {response.text}")

    return mb_title,mb_artist,mb_release_date

def get_deezer_album_art(artist, track):
    base_url = "https://api.deezer.com/search"

    # Set up parameters for Deezer album art search
    params = {
        'q': f'artist:"{artist}" track:"{track}"',
        'limit': 1
    }

    # Make the request to Deezer API
    response = requests.get(base_url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        # Check if there are any results
        if 'data' in data and data['data']:
            return data['data'][0]['album']['cover_big']
    return None

# Get unique song names for the select box
unique_song_names = sorted(set(mini.title))

# Recommender Function
def recommender(song_title):
    idx = mini[mini['title'] == song_title].index[0]
    distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])

    recommended_songs = []
    for idx, distance in distances[1:5]:
        recommended_song = {
            'title': mini.iloc[idx]['title'],
            'artist': mini.iloc[idx]['artist'],
            'genre': mini.iloc[idx]['tag']
        }
        recommended_songs.append(recommended_song)

    return recommended_songs


# Streamlit app
def main():
    st.title("Music Recommender App")

   # Sidebar with user input using a select box
    st.sidebar.header("Music Recommender by Streaks V.1.1")
    song_title = st.sidebar.selectbox("Select a song title:", unique_song_names)

    #Storing Selected song detials
    selected=mini.loc[mini["title"] == song_title].values.flatten().tolist()

    #To get Album Art of Selected Song
    selected_album_art_url = get_deezer_album_art(selected[2],selected[0])
    if selected_album_art_url:
        st.sidebar.image(selected_album_art_url, caption=f"Album Art for {selected[0]}")
    else:
        st.sidebar.warning("No album art found.")
    # To get music details of selected song
    selected_mb=search_musicbrainz(selected[2],selected[0])
    st.sidebar.write(f"Title: {selected_mb[0]}")
    st.sidebar.write(f"Artist/Artists: {selected_mb[1]}")
    st.sidebar.write(f"Release Date: {selected_mb[2]}")
    st.sidebar.write(f"Genre: {selected[1]}")
    
    recommend_button = st.sidebar.button("Recommend")

    # Display welcome page if no song title provided
    if not song_title or not recommend_button:
        st.header("Welcome to the Music Recommender App")
        st.markdown("Select a song title from the list and click the 'Recommend' button to get music recommendations.")

        # Information about the app
        st.subheader("App Information:")
        st.markdown("1. This recommender contains the most popular songs from 1950 up to 2005 as I want to explore songs between these periods, and it includes only English-language songs.")
        st.markdown("2. This is version 1 of the app, and more songs will be added in upcoming versions.")
        st.markdown("3. The recommender works based on lyric similarity between songs. New Methods might get implemented on upcoming versions for better recommendations")

        # Acknowledgments
        st.markdown("## Acknowledgments:")
        st.markdown("4. Thanks to MusicBrainz for providing song metadata.")
        st.markdown("5. Thanks to Deezer for providing album art for free.")
        st.markdown("6. Special thanks to [Yamac Eren Ay](https://www.kaggle.com/yamaerenay) for maintaining a massive dataset.")
        st.markdown("7. Thanks to [RAZA](https://www.kaggle.com/razauhaq) for helping code for cleaning lyrics of the massive dataset.")
    
        # Warning about API usage
        st.warning("⚠️ Please note that the MusicBrainz and Deezer APIs are free services. "
                   "Avoid excessive requests to prevent abuse of the service.")
        return

    # Display recommendations when the 'Recommend' button is clicked
    recommendations = recommender(song_title)

    # Display recommendations
    st.header("Top Recommendations:")
    for recommendation in recommendations:
        st.subheader(f"{recommendation['title']} by {recommendation['artist']}")
        mb_result=search_musicbrainz(recommendation['artist'], recommendation['title'])        
        album_art_url = get_deezer_album_art(recommendation['artist'], recommendation['title'])
        if album_art_url:
            st.image(album_art_url, caption=f"Album Art for {recommendation['title']}")
        else:
            st.warning("No album art found.")

        # Display release date and genre
        st.write(f"Title: {mb_result[0]}")
        st.write(f"Artist/Artists: {mb_result[1]}")
        st.write(f"Release Date: {mb_result[2]}")
        st.write(f"Genre: {recommendation['genre']}")

        st.markdown("---")  # Separator

if __name__ == "__main__":
    main()
