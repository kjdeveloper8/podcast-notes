import streamlit as st
import json
from glob import glob
from threading import Thread
from podcast_notes import podcast_pipeline
from podcasts import pipeline

st.title("Podcast Notes")

option = st.selectbox( "Select the Podcast", ("Talk Python", "Lex Fridman"))

if option == "Talk Python":
    transcript_dir = "transcripts/talk_python_to_me"      # path to transcripts json
    json_files = glob(f'{transcript_dir}/*.json')
    load_podcast = podcast_pipeline
else:
    transcript_dir = "transcripts/lex_fridman_podcast"      # path to transcripts json
    json_files = glob(f'{transcript_dir}/*.json')
    load_podcast = pipeline


# download podcast episode
listen_note_api = st.sidebar.text_input("listen_note_api_key")
episode_id = st.sidebar.text_input("Episode ID")
button = st.sidebar.button("Download Episode")
if button and episode_id:
    with st.status('Get podcast episode') as stat:
        st.sidebar.write('downloading ...')
        t = Thread(target=load_podcast, args=(listen_note_api, episode_id,))
        t.start()
        stat.update(label="Download complete!", state="complete", expanded=False)
        st.rerun()

def get_podcast_data(podcast):
    """ Get the podcast episode data. """
    txt = ''
    for episode in podcast:
        txt += f'timestamp: {episode['timestamp']}'
        txt += '\n\n'
        txt += episode['text']
        txt += '\n\n'
    return txt

# load the podcast json files
# and fetch the data
for file in json_files:
    with open(file, 'r') as rfile:
        data = json.load(rfile)

    podcast_episode = data['podcast']
    episode_title = data['episode_title']
    thumbnail = data['thumbnail']
    podcast_title = data['podcast_title']
    audio = data['audio_url']

    with st.expander(f"{podcast_title} - {episode_title}"):
        st.image(thumbnail, width=200)
        st.markdown(f'#### {episode_title}')
        st.write(get_podcast_data(podcast_episode))
