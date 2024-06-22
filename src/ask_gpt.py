import os
import sys
import time
import openai
import argparse
import asyncio
import concurrent.futures
from asyncio import Future
from subprocess import Popen
from dotenv import load_dotenv


sys.stdin.reconfigure(encoding='utf-8')


def ask_gpt3(messages, temperature=0):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
    )
    return response['choices'][0]['message']['content']


def ask_gpt4(messages, temperature=0, max_tokens=256):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        max_tokens=max_tokens,
        messages=messages,
        temperature=temperature,
    )
    return response['choices'][0]['message']['content']


def ask_gpt4_streaming(messages, temperature=0, max_tokens=256):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        max_tokens=max_tokens,
        messages=messages,
        temperature=temperature,
        stream=True,  # stream the response
    )
    return response


def gpt_moderation(text):
    response = openai.Moderation.create(
        input=text
    )
    output = response["results"][0]["flagged"]
    return output


def gpt_moderation_callback(flagged):
    if flagged:
        print("\n******The text is inappropriate!******\n")
    else:
        print("\n******The text is fine!******\n")


def check_violation(text):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(gpt_moderation, text)
        future.add_done_callback(lambda f: gpt_moderation_callback(f.result()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_engine", type=str,
                        default="gpt-4")
    args = parser.parse_args()

    # load OPENAI_API_KEY
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # text_to_speech process
    p = None

    print("Welcome!\n"
          "Please enter 'start' to start chat with chatgpt.\n"
          "This script is powered by the gpt-4 engine by default.\n"
          "To exit, simply type 'quit' or 'exit'.\n")

    # save chat history
    chat = []
    while True:
        user_input = input(">>> You:\n\n")
        if user_input.lower() == "quit" or user_input.lower() == "exit":
            print("\nBye!\n")
            break

        chat.append({"role": "user", "content": user_input})
        try:
            if args.model_engine == "gpt-3.5-turbo":
                result = ask_gpt3(chat)
                chat.append({"role": "assistant", "content": result})
                print("\n>>> AI: " + "\n" + "\n" + result + "\n")
            elif args.model_engine == "gpt-4":
                result = ask_gpt4(chat)
                chat.append({"role": "assistant", "content": result})
                print("\n>>> AI: " + "\n" + "\n" + result + "\n")
            elif args.model_engine == "gpt-4-stream":
                # stream the gpt-4 response
                delay_time = 0.01  # faster
                answer = ''
                result = ''
                sentence = ''
                sentence_list = []
                start_time = time.time()

                response = ask_gpt4_streaming(chat)

                print("\n>>> AI: " + "\n" + "\n")
                for event in response:
                    # print the response by word
                    print(answer, end='', flush=True)
                    # calculae the time delta by the event
                    event_time = time.time() - start_time
                    # retrieve the delta response
                    event_text = event['choices'][0]['delta']
                    # retrieve the content
                    answer = event_text.get('content', '')
                    # append the content to the result
                    result = result + answer

                    # append the content to the sentence
                    sentence = sentence + \
                        answer.replace('(', '').replace(')', '')
                    if is_sentence(sentence):
                        sentence_list.append(sentence)
                        sentence = ''

                    time.sleep(delay_time)

                print("\n")
                chat.append({"role": "assistant", "content": result})

            else:
                print("model_engine not supported")

        except Exception as e:
            print("Oops! Something went wrong. Please try again.\n")
            print(repr(e))
            chat.pop()
