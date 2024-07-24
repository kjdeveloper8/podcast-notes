import json
import requests
import pprint
import yaml
import re
from time import time
from bs4 import BeautifulSoup

configuration = 'credentials.yml'

with open(configuration, 'r') as config_file:
    config = yaml.safe_load(config_file)
    

LISTEN_NOTE_API = config['secret']['listen_note_api'] 


episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'
podcast_endpoint = 'https://listen-api.listennotes.com/api/v2/podcasts'


def get_episode(listen_note_api, episode_id):
    """ Get the podcast episode details. """
    headers_listen_note = {
                            'X-ListenAPI-Key': listen_note_api, 
    }
    
    url = episode_endpoint + '/' + episode_id
    response = requests.request('GET', url, headers=headers_listen_note)
    data = response.json()
    print(response.status_code) # 200: ok
    # pprint.pprint(data)

    # fetch the data we need
    episode_title = data['title']
    thumbnail = data['thumbnail']
    podcast_title = data['podcast']['title']
    audio_url = data['audio']
    description = data['description']
    return audio_url, thumbnail, podcast_title, episode_title, description

def parse_endpoint(text):
    """ Parse transcript endpoint. """
    soup = BeautifulSoup(text, 'html.parser')
    # parse the tag with match (Transcript:)
    expression= r'Transcript: (\bhttps?:\/\/\S+)' # to capture transcript followed with url
    transcript_endpoint = re.findall(expression, soup.text)
    return transcript_endpoint


def write_file(transcript_segment, audio_url, thumbnail, podcast_title, episode_title):
    """ Write transcript in file.

        transcript_segment: transcript reponse
        audio_url(str): audio url
        thumbnail(str): thumbnail url
        podcast_title(str): podcast title
        episode_title(str): episode title
    """
    split_title = episode_title.lower().split()[:4] # ep number and guest name
    ep_title = "_".join([i.replace('#','').replace(':','') for i in split_title if i != '–']) # U_002d not ('-' U+2013)

    # json
    transcript_dir = "transcripts/lex_fridman_podcast"
    if transcript_segment != None:
        with open(f'{transcript_dir}/{ep_title}.json', 'w') as f:
            data = {}
            prev = None
            # let's do some more stuff here 
            f.write('{"podcast" : [\n')
            for t in transcript_segment:
                description = t.text
                description = description.split('\n')
                data['speaker'] = description[1]
                # set the prev speaker (non empty)
                if description[1] == '':
                    description[1] = prev
                    data['speaker'] = description[1]
                prev = description[1]
                data['timestamp'] = description[2].replace('(','').replace(')','')
                data['text'] = description[3]

                f.write(json.dumps(data) + ',\n')   
                if t == transcript_segment[-1]:
                        f.write(json.dumps(data) + '\n')   # remove ',' in last line in json file
            f.write('],\n')
            f.write(f'"episode_title": "{episode_title}",\n')
            f.write(f'"podcast_title": "{podcast_title}",\n')
            f.write(f'"audio_url": "{audio_url}",\n')
            f.write(f'"thumbnail": "{thumbnail}"\n')
            f.write('}')
        return True
    return False


def parse_html(text):
    """ Parse html response. """
    soup = BeautifulSoup(text, 'html.parser')
    # transcript data is in div tag within class 'ts-segment'
    transcript_segment = soup.find_all("div", {'class':"ts-segment"})
    return transcript_segment


def transcribe(transcipt_endpoint):
    """ Transcript the podcast episode from endpoints. 

        transcript_endpoint: endpoint of transcript
    """
    transcript_response = requests.post(transcipt_endpoint)
    # print(transcript_response.status_code, "<-------") # 200 : ok
    # returns html so extract info with beautifulsoup
    transcript = transcript_response.text 
    transcript_text = parse_html(transcript)
    return transcript_text

def pipeline(listen_note_api, episode_id):
    audio_url, thumbnail, podcast_title, episode_title, description = get_episode(listen_note_api, episode_id)
    t_endpoint = parse_endpoint(description)
    transcript_segment = transcribe(t_endpoint[0])

    s = time()
    written = write_file(transcript_segment, audio_url, thumbnail, podcast_title, episode_title)
    if written:
        print(f"{episode_title}'s transcript saved in {(time() - s):.4f} sec")
    else:
        print('Transcribe not found') # if None


if __name__ == "__main__":
    # Podcast : Lex fridman's podcast
    listen_note_api = LISTEN_NOTE_API
    ep_id = 'd6f08aede6474d2e950b1a7ac648b65c'
    pipeline(listen_note_api, episode_id=ep_id)







