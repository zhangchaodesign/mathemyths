#!/usr/bin/env python

from __future__ import division

import re
import sys
import threading
import numpy as np

# from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech

import pyaudio
from six.moves import queue

import os
# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "src/alpine-surge-325521-b6c84344dd6e.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk, silence_chunks=50):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

        self.silent_chunks_count = 0  # count of silent chunks
        self.silence_threshold = 400  # Adjust this value as needed

        self.silent_chunks_beginning = 100
        self.silent_chunks_end = silence_chunks

        self.user_started_talking = False  # tag to indicate if user started talking

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""

        # Convert the byte data to ndarray
        audio_data = np.frombuffer(in_data, np.int16)

        # print(np.abs(audio_data).mean())

        # Check if this is a silent chunk
        if np.abs(audio_data).mean() < self.silence_threshold:
            self.silent_chunks_count += 1
        else:
            self.silent_chunks_count = 0
            if self.user_started_talking is False:
                self.user_started_talking = True  # Mark that user started talking

        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            max_silent_chunks = self.silent_chunks_end if self.user_started_talking else self.silent_chunks_beginning
            if self.silent_chunks_count > max_silent_chunks:  # If there are more than 100 silent chunks in a row
                # if self.user_started_talking:
                #     print("\nLong silence detected. End Speech-to-Text.\n")
                # else:
                #     print("\nNo speech detected. End Speech-to-Text.\n")
                print("\nSilence detected. End Speech-to-Text.\n")
                self.closed = True
                break

            yield b"".join(data)


def listen_print_loop(responses, stream):
    final_transcript = ""
    try:
        for response in responses:
            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if result.is_final:
                final_transcript += " " + transcript

        # Print everything on one line after silence detection
        print(final_transcript.strip())
        return final_transcript.strip()

    except Exception as e:
        print(f"Exception: {e}")
        stream.closed = True
        return final_transcript.strip()


def speech_to_text(silence=1):
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "en-US"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code
    )

    speech_contexts = [
        speech.SpeechContext(
            phrases=['none', 'any', 'few', 'fewer', 'fewest', 'little', 'less', 'least', 'a lot', 'much', 'many', 'more',
                     'most', 'same', 'enough', 'sufficient', 'insufficient', 'take away', 'add', 'different', 'longer', 'shorter', 'dragon', 'Hugo', 'castle', 'car', 'Addie', 'sky', 'tree', 'Jude', 'desert', 'tiger', 'Pedro', 'Jungle', 'fish', 'Remi', 'ocean', 'robot', 'Diego', 'forest'],
        )
    ]

    config.speech_contexts.extend(speech_contexts)

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    silence_chunks = silence * 10  # 10 chunks per second
    with MicrophoneStream(RATE, CHUNK, silence_chunks) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        try:
            responses = client.streaming_recognize(
                streaming_config, requests, timeout=30)
        except Exception as e:
            print("Oops! Something went wrong.\n")
            print(repr(e))
            return

        # pass stream into listen_print_loop
        return (listen_print_loop(responses, stream))


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "en-US"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)


if __name__ == "__main__":
    # main()
    print("Say something!")
    speech_to_text(silence=5)
