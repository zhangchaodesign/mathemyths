import os
import io
import argparse
import requests
from dotenv import load_dotenv
from io import BytesIO
from playsound import playsound

# load OPENAI_API_KEY
load_dotenv()
api_key = os.getenv("ELEVENLAB_API_KEY")

api_key = ELEVENLAB_API_KEY
voice_id = "EXAVITQu4vr4xnSDxMaL"  # Bella


def call_api(text, voice_id, api_key):
    url = 'https://api.elevenlabs.io/v1/text-to-speech/' + voice_id + "/stream"
    headers = {
        'accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': api_key
    }
    data = {
        'text': text,
        'voice_settings': {
            'stability': 0.2,
            'similarity_boost': 0.1
        }
    }
    response = requests.post(url, headers=headers, json=data, stream=True)
    if response.status_code == 200:
        return response
    else:
        print(f'Request failed with status code {response.status_code}')
        return None


def elevenlab_text_to_speech(text):
    response = call_api(text, voice_id, api_key)

    if response:
        try:
            with open('src/output_audio/agent_voice_temp.mp3', 'wb') as f:
                for chunk in response.iter_content(chunk_size=2048):
                    if chunk:
                        f.write(chunk)

            playsound('src/output_audio/agent_voice_temp.mp3', block=True)
        except Exception as e:
            print(
                "Oops! Something went wrong in elevenlab_text_to_speech. Please try again.\n")
            print(repr(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str,
                        default="hello world")
    args = parser.parse_args()

    elevenlab_text_to_speech(args.text)
