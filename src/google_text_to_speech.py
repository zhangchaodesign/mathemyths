import re
import argparse
from playsound import playsound


import os
# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "src/alpine-surge-325521-b6c84344dd6e.json"


def add_ssml_tags(text):
    keywords = ['equal', 'sum', 'half', 'add', 'subtract', 'estimate']

    ssml_text = '<speak>\n'
    words = text.split()

    for word in words:
        # Remove punctuation & convert to lowercase
        word_stripped = re.sub(r'[^\w\s]', '', word).lower()

        # If the word contains any of the keywords as a substring
        if any(keyword in word_stripped for keyword in keywords):
            # Wrap the word with the prosody and emphasis tags
            ssml_text += '<prosody rate="slow">' + \
                word + '</prosody> '
            # ssml_text += '<break time="80ms"/><prosody rate="slow"><emphasis level="strong">' + \
            #     word + '</emphasis></prosody><break time="80ms"/> '
        else:
            ssml_text += word + ' '

    ssml_text += '\n</speak>'
    # print(ssml_text)

    return ssml_text


def google_text_to_speech(text, highlight='on'):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    if highlight == 'on':
        input_text = texttospeech.SynthesisInput(ssml=add_ssml_tags(text))
    else:
        input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Neural2-H",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice,
                 "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open("src/output_audio/agent_voice_temp.mp3", "wb") as out:
        out.write(response.audio_content)
        # print('Audio content written to file.')

    playsound('src/output_audio/agent_voice_temp.mp3', block=True)


# [END tts_synthesize_text]

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--text", type=str,
    #                     default="hello world")
    # args = parser.parse_args()

    # google_text_to_speech(args.text)

    google_text_to_speech(
        "Lily's mom estimated that it would take four hours to craft the perfect cake, ensuring each layer was equal in size and thickness.", "on")
