import json
import requests
import pprint
import yaml
import re
from time import time

configuration = 'credentials.yml'

with open(configuration, 'r') as config_file:
    config = yaml.safe_load(config_file)
    

LISTEN_NOTE_API = config['secret']['listen_note_api'] 


episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'
podcast_endpoint = 'https://listen-api.listennotes.com/api/v2/podcasts'
transcript_endpoint = 'https://talkpython.fm/episodes/transcript'


def get_episode(listen_note_api, episode_id):
    """ Get the podcast episode details. """
    headers_listen_note = {
                            'X-ListenAPI-Key': listen_note_api, 
    }
    # url = podcast_endpoint + '/' + podcast_id # to get all podcast data
    url = episode_endpoint + '/' + episode_id
    response = requests.request('GET', url, headers=headers_listen_note)
    data = response.json()
    # print(response.status_code) # 200: ok
    # pprint.pprint(data)

    # fetch the data we need
    episode_title = data['title']
    thumbnail = data['thumbnail']
    podcast_title = data['podcast']['title']
    audio_url = data['audio']
    return audio_url, thumbnail, podcast_title, episode_title


def extract(text):
    """ Extract timeline and text from transcript. """
    expression = r'(\d{2}(?:\:\d{2})(?:\:\d{2})?)' # timeline with 2 or 3 colon separate group

    # timeline = re.findall(expression, text)
    description = re.split(expression, text)
    description = [d.replace('\n','').strip() for d in description][1:]
    return description

def parse_html(text):
    """ Parse html response. """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    # transcript data is in p tag within calss 'transcript-segment'
    transcript_segment = soup.find_all("p", {'class':"transcript-segment"})
    return transcript_segment

def write_file(transcript_segment, audio_url, thumbnail, podcast_title, episode_title, to_txt=False):
    """ Write transcript in file.

        transcript_segment: transcript reponse
        audio_url(str): audio url
        thumbnail(str): thumbnail url
        podcast_title(str): podcast title
        episode_title(str): episode title
        to_txt(bool): flag to store in text format (default: False)
    """
    ep_title = "_".join(episode_title.lower().split()[1:]) 
    if transcript_segment != None:
        # text
        if to_txt: 
            with open(f'{ep_title}.txt', 'w') as f:
                for t in transcript_segment:
                    # print("Transcript --> ",t.text)
                    description = extract(t.text)
                    f.writelines(description[0])
                    f.write(' ')
                    f.writelines(description[1])
                    f.write('\n')

                
        # json
        # save transcripts 
        transcript_dir = "transcripts/talk_python_to_me"
        with open(f'{transcript_dir}/{ep_title}_timestamp.json', 'w') as f:
            data = {}
            # let's do some stuff here (manually -_-)
            f.write('{"podcast" : [\n')
            for t in transcript_segment:
                description = extract(t.text)
                data['timestamp'] = description[0]
                data['text'] = description[1]

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
    

def transcribe(episode_title):
    """ Transcript the podcast episode from endpoints. 

        episode_title: title of episode
    """
    ep = episode_title.lower().split()[0].replace('#', '').replace(':', '') # extract episode number
    ep_title = "-".join(episode_title.lower().split()[1:])                  # extract and join the title
    trans_endpoint = transcript_endpoint + '/' + ep + '/' + ep_title

    transcript_response = requests.post(trans_endpoint)

    # print(transcript_response.status_code, "<-------") # 200 : ok

    # returns html so parse text with beautifulsoup
    trans_data = transcript_response.text 
    transcript = parse_html(trans_data)
    return transcript

def podcast_pipeline(listen_note_api, episode_id):
    audio_url, thumbnail, podcast_title, episode_title = get_episode(listen_note_api, episode_id)
    transcript = transcribe(episode_title)

    s = time()
    written = write_file(transcript, audio_url, thumbnail, podcast_title, episode_title)
    if written:
        print(f"{episode_title}'s transcript saved in {(time() - s):.4f} sec")
    else:
        print('Transcribe not found') # if None


if __name__ == "__main__":
    ep_id = 'dfa0bbed6c2d4bc781af3d098d106963'
    listen_note_api = LISTEN_NOTE_API
    result = podcast_pipeline(listen_note_api, str(ep_id))



