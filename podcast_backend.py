
import modal

def download_whisper():
  # Load the Whisper model
  import os
  import whisper
  print ("Download the Whisper model")

  # Perform download only once and save to Container storage
  whisper._download(whisper._MODELS["medium"], '/content/podcast/', False)


stub = modal.Stub("corise-podcast-project")
corise_image = modal.Image.debian_slim().pip_install("feedparser",
                                                     "https://github.com/openai/whisper/archive/9f70a352f9f8630ab3aa0d06af5cb9532bd8c21d.tar.gz",
                                                     "requests",
                                                     "ffmpeg",
                                                     "openai",
                                                     "tiktoken",
                                                     "wikipedia",
                                                     "ffmpeg-python").apt_install("ffmpeg").run_function(download_whisper)

@stub.function(image=corise_image, gpu="any", timeout=600)
def get_transcribe_podcast(rss_url, local_path):
  print ("Starting Podcast Transcription Function")
  print ("Feed URL: ", rss_url)
  print ("Local Path:", local_path)

  # Read from the RSS Feed URL
  import feedparser
  intelligence_feed = feedparser.parse(rss_url)
  podcast_title = intelligence_feed['feed']['title']
  episode_title = intelligence_feed.entries[0]['title']
  episode_image = intelligence_feed['feed']['image'].href
  for item in intelligence_feed.entries[0].links:
    if (item['type'] == 'audio/mpeg'):
      episode_url = item.href
  episode_name = "podcast_episode.mp3"
  print ("RSS URL read and episode URL: ", episode_url)

  # Download the podcast episode by parsing the RSS feed
  from pathlib import Path
  p = Path(local_path)
  p.mkdir(exist_ok=True)

  print ("Downloading the podcast episode")
  import requests
  with requests.get(episode_url, stream=True) as r:
    r.raise_for_status()
    episode_path = p.joinpath(episode_name)
    with open(episode_path, 'wb') as f:
      for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)

  print ("Podcast Episode downloaded")

  # Load the Whisper model
  import os
  import whisper

  # Load model from saved location
  print ("Load the Whisper model")
  model = whisper.load_model('medium', device='cuda', download_root='/content/podcast/')

  # Perform the transcription
  print ("Starting podcast transcription")
  result = model.transcribe(local_path + episode_name)

  # Return the transcribed text
  print ("Podcast transcription completed, returning results...")
  output = {}
  output['podcast_title'] = podcast_title
  output['episode_title'] = episode_title
  output['episode_image'] = episode_image
  output['episode_transcript'] = result['text']
  return output

@stub.function(image=corise_image, secret=modal.Secret.from_name("my-openai-secret-2"))
def get_podcast_summary(podcast_transcript):
  import openai
  instructPrompt = """
    Below is a podcast episode transcript. Provide a detailed summary of the episode, providing all key points and topics that are talked about.
    List each individual person mentioned, including details why they are talked about. Also include all significant performances and statistics that are
    talked about during the episode. Also mention all controversial opinions, ideas, or questions that were talked about during this episode. This should
    be an informative and interesting summary of the episode.
    """
  request = instructPrompt + podcast_transcript
  chatOutput = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                            messages=[{"role": "system", "content": "You are a helpful assistant."},
                                                      {"role": "user", "content": request}
                                                      ]
                                            )
  podcastSummary = chatOutput.choices[0].message.content
  return podcastSummary

@stub.function(image=corise_image, secret=modal.Secret.from_name("my-openai-secret-2"))
def get_podcast_guest(podcast_transcript):
  import openai
  import wikipedia
  import json
  request = podcast_transcript[:11000]
  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": request}],
    functions=[
    {
        "name": "get_podcast_guest_information",
        "description": """Get information on the episode guest or individual who is a significant topic 
                          of the episode. Provide their full name, the organization they belong to, and 
                          their role. Don't use the host of the show and skip advertisements.""",
        "parameters": {
            "type": "object",
            "properties": {
                "guest_name": {
                    "type": "string",
                    "description": "The full name of the guest or significant individual in the podcast.",
                },
                "guest_organization": {
                    "type": "string",
                    "description": "The name of the organization that the podcast guest or significant individual belongs to.",
                },
                "guest_title": {
                    "type": "string",
                    "description": "The role of the podcast guest or significant individual in their organization.",
                },
            },
            "required": ["guest_name"],
        },
    }
    ],
    function_call={"name": "get_podcast_guest_information"}
    )
  response_message = completion["choices"][0]["message"]

  # Extract relevant information
  podcast_guest = ""
  podcast_guest_org = ""
  podcast_guest_title = ""

  if response_message.get("function_call"):
    function_name = response_message["function_call"]["name"]
    function_args = json.loads(response_message["function_call"]["arguments"])
    podcast_guest=function_args.get("guest_name")
    podcast_guest_org=function_args.get("guest_organization")
    podcast_guest_title=function_args.get("guest_title")
  if (podcast_guest is not None):
    if (podcast_guest_org is None):
      podcast_guest_org = ""
    if (podcast_guest_title is None):
      podcast_guest_title = ""
    try:
      input = wikipedia.page(podcast_guest + " " + podcast_guest_org + " " + podcast_guest_title, auto_suggest=True)
      podcast_guest_summary = input.summary
    except wikipedia.exceptions.PageError:
      print (f'The page for guest "{podcast_guest}" does not exist on Wikipedia.')
      print (f"Due to possible misspellings, let's see what Wikipedia thinks we meant and try that.")
      try:
        # Get suggestion from Wikipedia and try it
        suggestion = wikipedia.suggest(podcast_guest)
        print(f'Suggestion: {suggestion}')
        if (suggestion is None):
          suggestion = podcast_guest
        input = wikipedia.page(suggestion + " " + podcast_guest_org + " " + podcast_guest_title, auto_suggest=True)
        podcast_guest_summary = input.summary
      except wikipedia.exceptions.PageError:
        print (f'The page for guest "{suggestion}" does not exist on Wikipedia.')
        podcast_guest_summary = "Not Available"    
      except wikipedia.exceptions.DisambiguationError as e:
        print (f'The page for guest "{suggestion}" is ambiguous. Possible matches are:')
        print(e.options)
        podcast_guest_summary = "Not Available"
    except wikipedia.exceptions.DisambiguationError as e:
      print (f'The page for guest "{podcast_guest}" is ambiguous. Possible matches are:')
      print(e.options)
      podcast_guest_summary = "Not Available"
  else:
    podcast_guest = "Not Available"
    podcast_guest_org = "Not Available"
    podcast_guest_title = "Not Available"
    podcast_guest_summary = "Not Available"

  podcastGuest = {}
  podcastGuest['name'] = podcast_guest
  podcastGuest['org'] = podcast_guest_org
  podcastGuest['title'] = podcast_guest_title
  podcastGuest['summary'] = podcast_guest_summary
  return podcastGuest

@stub.function(image=corise_image, secret=modal.Secret.from_name("my-openai-secret-2"), timeout=375)
def process_podcast(url, path):
  output = {}
  podcast_details = get_transcribe_podcast.call(url, path)
  podcast_summary = get_podcast_summary.call(podcast_details['episode_transcript'])
  podcast_guest = get_podcast_guest.call(podcast_details['episode_transcript'])
  output['podcast_details'] = podcast_details
  output['podcast_summary'] = podcast_summary
  output['podcast_guest'] = podcast_guest
  return output

@stub.local_entrypoint()
def test_method(url, path):
  output = {}
  podcast_details = get_transcribe_podcast.call(url, path)
  print ("Podcast Summary: ", get_podcast_summary.call(podcast_details['episode_transcript']))
  print ("Podcast Guest Information: ", get_podcast_guest.call(podcast_details['episode_transcript']))
