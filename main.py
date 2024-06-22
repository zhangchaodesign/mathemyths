import Levenshtein
import argparse
import asyncio
import atexit
import concurrent.futures
import datetime
import io
import json
import keyboard
import multiprocessing
import os
import random
import re
import threading
import time
from threading import Thread

import openai
from dotenv import load_dotenv
from playsound import playsound

from src.ask_gpt import ask_gpt4_streaming, ask_gpt4, check_violation
from src.elevenlab_text_to_speech import elevenlab_text_to_speech
from src.google_speech_to_text import speech_to_text
from src.google_text_to_speech import google_text_to_speech
from src.prompts import (storytelling_chat_preset,
                         question_generator_prompt_quan,
                         storytelling_prompt_addon_identifier,
                         storytelling_prompt_addon_continue,
                         storytelling_prompt_addon_end,
                         extract_story_elements,
                         storytelling_prompt_encouragement,
                         storytelling_prompt_creativity,
                         storytelling_prompt_addon_continue_no_praise,
                         storytelling_prompt_addon_end_no_praise)

# load OPENAI_API_KEY
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def fuzzy_match(answer, options, threshold=0.7):
    best_match = None
    max_similarity = 0

    for option in options:
        similarity = Levenshtein.ratio(answer.lower(), option.lower())
        if similarity > max_similarity and similarity >= threshold:
            best_match = option
            max_similarity = similarity

    return best_match


def generate_question_gpt4(story_fragment):
    chat = [
        {"role": "system", "content": question_generator_prompt_quan(args.terms)}]
    if args.terms != ['equal', 'sum', 'half', 'add', 'subtract', 'estimate']:
        chat.append({"role": "user", "content": story_fragment})
    else:
        content = "Story: " + story_fragment + "\n" + "Question: "
        chat.append({"role": "user", "content": content})

    result = ask_gpt4(chat, temperature=0.7)
    return result


def generate_question_gpt3(messages, temperature=0.7, max_tokens=256):
    response = openai.Completion.create(
        model='davinci:ft-university-of-michigan:storywhiz-2023-05-02-03-30-59',
        prompt=messages,
        max_tokens=max_tokens,)

    questions = re.findall(r'[A-Za-z0-9][^.!?]*[?]',
                           response['choices'][0]['text'])
    if questions:
        return questions[0].replace('(', '').replace(')', '')
    else:
        return response['choices'][0]['text'].split("END", 1)[0].replace('(', '').replace(')', '')
    # return response['choices'][0]['text'].split("END", 1)[0]


def check_story_fragment(input_text, temperature=0, max_tokens=256):
    messages = storytelling_prompt_addon_identifier() + input_text + ":"

    response = openai.Completion.create(
        model='gpt-3.5-turbo-instruct',
        prompt=messages,
        max_tokens=max_tokens,)

    # print(response)

    try:
        result = extract_numbers(response['choices'][0]['text'])[0]
    except:
        result = 0

    return result


def generate_encouragement(input_text, question, temperature=1):
    messages = [{"role": "system", "content": storytelling_prompt_encouragement(question)},
                {"role": "user", "content": input_text}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
    )
    return response['choices'][0]['message']['content']


def generate_creativity(input_text, question, temperature=1):
    messages = [{"role": "system", "content": storytelling_prompt_creativity(question)},
                {"role": "user", "content": input_text}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=temperature,
    )
    return response['choices'][0]['message']['content']


def extract_numbers(s):
    return [int(n) for n in re.findall(r'\d', s)]


def remove_symbols_and_spaces(s):
    # remove all non-alphanumeric characters
    cleaned_string = re.sub(r'\W+', '', s)
    return cleaned_string.lower()


def remove_consecutive_duplicates(sentence):
    words = sentence.split()
    i = 0
    while i < len(words) - 1:
        if remove_symbols_and_spaces(words[i]) == remove_symbols_and_spaces(words[i+1]):
            del words[i]
        else:
            i += 1
    return ' '.join(words)


def is_sentence(string):
    # check if the string is a sentence
    char_list = ['.', '!', '?']
    return any(char in string for char in char_list)


def storyteller(sentence_list, event):
    if sentence_list:
        to_speak = sentence_list.pop(0).replace("\"", "\\\"")
        speak(to_speak)

    # if the event is stop, speak the rest of the sentence_list
    if event['choices'][0]['finish_reason'] == "stop":
        while True:
            if len(sentence_list):
                to_speak = sentence_list.pop(0).replace("\"", "\\\"")
                speak(to_speak)
            else:
                break

    return sentence_list


def save_chat_history():
    if chat_history != []:
        # ensure the existence of a folder named "history"
        if not os.path.exists("history"):
            os.mkdir("history")

        # get the current time and format it as a string
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # generate the file name and path
        file_name = f"{args.user}__{current_time}.json"
        file_path = os.path.join("history", file_name)

        # save the list as a JSON file
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(chat_history, file, ensure_ascii=False)

        print("Saving chat history...")


def randomly_choose_story_element():
    character_list = [{"character": "dragon", "name": "Hugo", "setting": "castle"},
                      {"character": "car", "name": "Addie", "setting": "sky"},
                      {"character": "tree", "name": "Jude", "setting": "desert"},
                      {"character": "tiger", "name": "Pedro",
                       "setting": "Jungle"},
                      {"character": "fish", "name": "Remi", "setting": "ocean"}]
    story_elements = random.choice(character_list)
    return story_elements


def chat_loop():
    global restart_chat
    # 将restart_chat设置为False，表示聊天循环正常运行
    restart_chat = False

    if not args.demo:
        if args.opening == 1:
            print("\n>>> AI: \n")
            warmup_name = "Hello, my little friend! My name is Alexa. I'm really looking forward to spending some time with you today! May I know your name, please?"
            print(warmup_name + '\n')
            if not args.text:
                speak(warmup_name)
            get_user_input()

            print("\n>>> AI: \n")
            warmup_mood = "Nice to meet you, " + args.name + \
                "! Now, could you please tell me how you're feeling today? Are you feeling happy, excited, or maybe a little sleepy?"
            print(warmup_mood + '\n')
            if not args.text:
                speak(warmup_mood)
            get_user_input()

            print("\n>>> AI: \n")
            opening = "Thank you for sharing your feelings! I'm here to make your day more fun. How about we make up a story together? We'll use our imaginations and even learn some math words. I'll start, then you can add to the story. If you have any questions or need help, just ask me. Always remember, the power of our imaginations knows no bounds!"
        else:
            print("\n>>> AI: \n")
            opening = "Hello again, " + args.name + "! Let's continue our fun storytelling game. We'll create a new story and delve deeper into the language of mathematics. As always, I'll start, then it's your turn. If you have any questions or need help, just ask me! Let's not forget, the magic of our imaginations is limitless!"

        print(opening + '\n')
        if not args.text:
            speak(opening)

        print("\n>>> AI: \n")
        ask_character = "Now, let's come up with a cool main character for the story. This could be an animal, a person, a mythical creature, or anything else that fits our story. What do you want our main character to be?"
        print(ask_character + '\n')
        if not args.text:
            speak(ask_character)
        user_input_character = get_user_input()

        if if_user_say_nothing(user_input_character):
            print("\n>>> AI: \n")
            ask_character = "Which character do you prefer? A dragon or a unicorn?"
            print(ask_character + '\n')
            if not args.text:
                speak(ask_character)
            user_input_character = get_user_input()
            options = ['dragon', 'unicorn']
            best_match = fuzzy_match(user_input_character, options)
            if best_match:
                user_input_character = best_match
            else:
                user_input_character = random.choice(options)
            if user_input_character == 'dragon':
                user_input_name = 'Fireball'
            else:
                user_input_name = 'Uni'
        else:
            print("\n>>> AI: \n")
            ask_name = "That's interesting! What's the character's name?"
            print(ask_name + '\n')
            if not args.text:
                speak(ask_name)
            user_input_name = get_user_input()

        print("\n>>> AI: \n")
        ask_setting = "Great! Where will our story happen?"
        print(ask_setting + '\n')
        if not args.text:
            speak(ask_setting)
        user_input_setting = get_user_input()

        if if_user_say_nothing(user_input_setting):
            print("\n>>> AI: \n")
            ask_setting = "Which setting do you prefer your character to be in? A forest or your house?"
            print(ask_setting + '\n')
            if not args.text:
                speak(ask_setting)
            user_input_setting = get_user_input()
            options = ['forest', 'house']
            best_match = fuzzy_match(user_input_setting, options)
            if best_match:
                user_input_setting = best_match
            else:
                user_input_setting = random.choice(options)

        user_input = user_input_character + " " + \
            user_input_name + " " + user_input_setting

        try:
            story_elements = json.loads(ask_gpt4(
                extract_story_elements(user_input), temperature=0))
            story_elements = {k: v.lower() if isinstance(
                v, str) else v for k, v in story_elements.items()}
        except:
            story_elements = randomly_choose_story_element()
        # print(story_elements)
        character = story_elements['character']
        name = story_elements['name']
        setting = story_elements['setting']

        print("\n>>> AI: \n")
        initial_element = f"Okay! We'll dive into an incredible adventure with a {character} named {name} in the {setting}."
        print(initial_element +
              ' Ready to start the story? Let\'s go!\n')
        if not args.text:
            speak(
                initial_element + ' Ready to start the story? Let\'s go!\n')
    else:
        story_elements = {'character': 'dragon',
                          'name': 'Nick', 'setting': 'castle'}
        args.dialog = 3

    global chat
    global chat_history

    # dialog counter, used to end the story after 10 dialogs
    dialog_counter = args.dialog

    # save chat history
    chat = storytelling_chat_preset(
        story_elements['character'], story_elements['name'], story_elements['setting'], args.vocabulary, args.terms, args.name, args.gender)
    chat_history = storytelling_chat_preset(
        story_elements['character'], story_elements['name'], story_elements['setting'], args.vocabulary, args.terms, args.name, args.gender)
    while True:
        if restart_chat:
            print("Restarting chat loop...\n")
            break

        # get agent output
        try:
            # stream the gpt-4 response
            delay_time = 0.01  # faster
            answer = ''
            result = ''
            sentence = ''
            sentence_list = []
            question = ''
            question_list = []
            start_time = time.time()

            # change temperature to 0.7 for a more random response
            response = ask_gpt4_streaming(chat, temperature=0.7)

            print("\n>>> AI: \n")
            for event in response:
                if restart_chat:
                    print("\nRestarting chat loop...\n")
                    break

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

                time.sleep(delay_time)

                # if the event is stop, speak the rest of the sentence_list
                if event['choices'][0]['finish_reason'] == "stop":
                    print("\n")
                    chat.append({"role": "assistant", "content": result})
                    chat_history.append(
                        {"role": "assistant", "content": result})

                    # check violation
                    try:
                        check_violation(result)
                    except Exception as e:
                        print("Error in checking violation .\n")
                        print(repr(e))

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        if args.question == "gpt4":
                            question_generator_future = executor.submit(
                                generate_question_gpt4, result)
                        elif args.question == "gpt3":
                            question_generator_future = executor.submit(
                                generate_question_gpt3, result)

                if not args.text:
                    # append the content to the sentence
                    sentence = sentence + \
                        answer.replace('(', '').replace(')', '')
                    if is_sentence(sentence):
                        sentence_list.append(sentence)
                        sentence = ''

                    # speak the sentence
                    sentence_list = storyteller(sentence_list, event)

            if restart_chat:
                print("\nRestarting chat loop...\n")
                break

            if dialog_counter > 0:
                print("\n")
                print("Question: \n")

                question = question_generator_future.result().replace('\n', '')
                print(question)
                print("\n")

                chat_history.append({"role": "question", "content": question})
                if not args.text:
                    speak("Question: " + question)
                # print("\n")

        except Exception as e:
            print("Oops! Something went wrong.\n")
            print(repr(e))
            chat.pop()
            chat_history.pop()

        # end the game when the number of dialogs reaches 10
        if dialog_counter == 0:
            print("\n>>> AI: \n")
            print(
                "\nWe created an amazing story together. Till next time, little friend!\n")
            if not args.text:
                speak(
                    "We created an amazing story together. Till next time, little friend!")
            # restart_chat_loop(0)
            break

        # get user input
        user_input = get_user_input()

        # tag of if the agent has encouraged the user to continue the story
        if_encouraged = False

        # tag of user successful continue the story
        if_user_continue_story = False

        # check if the user successfully added a new story fragment
        if if_user_say_nothing(user_input):
            if_encouraged = True
            print("\n>>> AI: \n")
            if user_input is None or user_input.strip() == '':
                user_input = "I don't know."
            encouragement = generate_encouragement(user_input, question)
            print(encouragement + "\n")
            if not args.text:
                speak(encouragement)

            user_input = get_user_input()

            if remove_symbols_and_spaces(user_input) in ['yes', 'yeah', 'ok', 'okay']:
                pass
            elif if_user_say_nothing(user_input):
                print("\n>>> AI: \n")
                reassurance = random.choice(["It's okay! I'll continue the story for you.",
                                             "Don't worry! I'll continue the story for you",
                                             "No worries! I'll continue the story for you."])
                print(reassurance + "\n")
                if not args.text:
                    speak(reassurance)
            else:
                if_user_continue_story = True
        else:
            if_user_continue_story = True

        prev_user_input = user_input
        if if_user_continue_story and not if_encouraged:
            # if the user' words are less than 5, encourage the user to say more
            new_user_input = encourage_to_say_more(user_input, question)
            user_input = prev_user_input + '\n' + new_user_input

        # end the story when the number of dialogs reaches 10
        next_terms = next(terms_generator)
        if dialog_counter > 1:
            if if_user_continue_story:
                user_input = user_input + "\n" + \
                    storytelling_prompt_addon_continue(
                        next_terms, not args.demo)
            else:
                user_input = user_input + "\n" + \
                    storytelling_prompt_addon_continue_no_praise(
                        next_terms, not args.demo)
        else:
            if if_user_continue_story:
                user_input = user_input + "\n" + \
                    storytelling_prompt_addon_end(next_terms, not args.demo)
            else:
                user_input = user_input + "\n" + \
                    storytelling_prompt_addon_end_no_praise(
                        next_terms, not args.demo)
        chat.append({"role": "user", "content": user_input})
        chat_history.append({"role": "user", "content": user_input})

        # decount the number of dialogs
        dialog_counter -= 1


def if_user_say_nothing(user_input):
    nonsense_list = ['go on', 'continue', 'please continue', 'I don\'t know',
                     'I like it', 'I don\'t like it', 'I am not sure', 'I\'m not sure']
    if user_input is None or user_input.strip() == '' or user_input in nonsense_list or check_story_fragment(user_input):
        return True
    else:
        return False


def encourage_to_say_more(user_input, question):
    # check if the user said too little
    if len(user_input.split()) < 5:
        print("\n>>> AI: \n")
        creativity = generate_creativity(user_input, question)
        print(creativity + "\n")
        if not args.text:
            speak(creativity)

        # get user input
        user_input = get_user_input()

    return user_input


def speak(content):
    global text_to_speech_future

    content = remove_consecutive_duplicates(content)

    if text_to_speech_future and not text_to_speech_future.done():
        text_to_speech_future.result()  # wait for the text-to-speech to finish

    text_to_speech_future = text_to_speech_executor.submit(
        direct_agent_speak, content, args.service)  # run the text-to-speech


def direct_agent_speak(content, service):
    if service == "paid":
        elevenlab_text_to_speech(content)
    elif service == "free":
        google_text_to_speech(content, args.highlight)


def get_user_input():
    # wait for the text-to-speech to finish
    if text_to_speech_future and not text_to_speech_future.done():
        text_to_speech_future.result()

    # get user input
    if args.text:
        user_input = input(">>> You:\n\n")
    else:
        print("\n>>> You: \n")

        # uncomment the following lines to use Google Speech-to-Text API
        user_input = speech_to_text(args.silence)

    playsound('src/effect.mp3', block=False)

    return user_input


def restart_chat_loop(event):
    global restart_chat
    # 将restart_chat设置为True，表示需要重新启动聊天循环
    restart_chat = True


def listen_for_restart_key():
    keyboard.on_press_key('0', restart_chat_loop)
    keyboard.wait()


def listen_for_quit_key():
    keyboard.wait("9")
    save_chat_history()
    os._exit(0)


def word_generator(vocabulary):
    words = vocabulary * 2
    random.shuffle(words)

    for _ in range(args.dialog):
        if len(words) == 0:
            words = vocabulary * 2
            random.shuffle(words)

        # # print(words)
        # if len(words) == 1 or random.choice([True, False]):
        #     yield [words.pop()]
        # else:
        #     yield [words.pop(), words.pop()]
        yield [words.pop(), words.pop()]


def print_system_status(text, demo, user, service, dialog, question, vocabulary, silence, highlight, terms, name, gender, opening):
    # Print the current system status based on the input values
    print("System Status:")
    print(f"Text Input: {'enabled' if text else 'disabled'}")
    print(f"Demo Mode: {'enabled' if demo else 'disabled'}")
    print(f"User ID: {user}")
    print(f"Speech-to-Text Service: {service}")
    print(f"Number of Dialogs: {dialog}")
    print(f"Question Generator: {question}")
    print(f"Mathematical Vocabulary: {vocabulary}")
    print(f"Silence Duration: {silence}s (only applicable in voice mode)")
    print(f"Highlight Mode: {highlight} (only applicable in voice mode)")
    print(f"Mathematical Terms: {terms}")
    print(f"Child's Name: {name}")
    print(f"Child's Gender: {gender}")
    print(f"Opening Words: {opening}")


def storytelling_game():
    print("\nWelcome to the co-creative storytelling game! Press the number key '0' to restart. Press 'Ctrl+C' twice to exit.\n")

    print_system_status(args.text, args.demo, args.user, args.service,
                        args.dialog, args.question, args.vocabulary, args.silence, args.highlight, args.terms, args.name, args.gender, args.opening)

    while True:
        chat_loop()
        save_chat_history()

        # reset the chat history
        global chat
        global chat_history
        chat = []
        chat_history = []

        # print(restart_chat)
        # jump out of the chat loop when restart_chat is True
        if not restart_chat:
            break


def play_music(parts):
    global keep_playing
    while keep_playing:
        for part in parts:
            if not keep_playing:
                break
            playsound(part)


def stop_music():
    global keep_playing
    keep_playing = False
    print("Stopping music...")
    music_thread.join()


def system_exit():
    stop_music()
    save_chat_history()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", action="store_true",
                        help="use text input instead of voice input",
                        default=False)
    parser.add_argument("--demo", action="store_true",
                        help="initiate the demo mode",
                        default=False)
    parser.add_argument("--user", type=str,
                        help="enter the participant id such as 0, 1, 2, ...",
                        default='0')
    parser.add_argument("--service", type=str,
                        help="select the speech_to_text service, free or paid; default is free",
                        default='free')
    parser.add_argument("--dialog", type=int,
                        help="set the number of dialogs; default is 8",
                        default=8)
    parser.add_argument("--question", type=str,
                        help="select the question generator model, gpt3 or gpt4; default is gpt4",
                        default='gpt4')
    parser.add_argument("--vocabulary", type=str,
                        help="select the type of mathematical vocabulary; only quan is supported for now.",
                        default='quan')
    parser.add_argument("--silence", type=int,
                        help="set the acceptable silence duration in seconds; default is 3",
                        default=3)
    parser.add_argument("--highlight", type=str,
                        help="whether slow down and stress the mathematical terms or not; on or off, default is on",
                        default='on')
    parser.add_argument("--terms", type=str,
                        help="specify the mathematical terms to be learned; replace the space between words in a term with a slash; default is equal,sum,half,add,subtract,estimate for quan",
                        default='equal,sum,half,add,subtract,estimate')
    parser.add_argument("--name", type=str,
                        help="input the child's name",
                        default='none')
    parser.add_argument("--gender", type=str,
                        help="input the child's gender, boy or girl",
                        default='kid')
    parser.add_argument("--opening", type=int,
                        help="select the opening words; default is 1",
                        default=1)
    args = parser.parse_args()

    str_vocabulary = args.terms.replace('/', ' ')
    args.terms = str_vocabulary.split(',')

    terms_generator = word_generator(args.terms)

    # text_to_speech process
    text_to_speech_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=1)
    text_to_speech_future = None

    # text_to_speech service
    service = args.service

    # chat history
    chat = []
    chat_history = []

    # save chat history and stop music when the program exits
    atexit.register(system_exit)

    # play background music
    keep_playing = True
    parts = [f"src/bgm/lower_volume_part_{i}.mp3" for i in range(10)]
    music_thread = threading.Thread(target=play_music, args=(parts,))
    music_thread.start()

    # restart_chat is used to control whether to restart the chat loop
    restart_chat = False

    # start the keyboard listener thread
    restart_keyboard_listener_thread = threading.Thread(
        target=listen_for_restart_key)
    restart_keyboard_listener_thread.daemon = True
    restart_keyboard_listener_thread.start()

    # quit_keyboard_listener_thread = threading.Thread(
    #     target=listen_for_quit_key)
    # quit_keyboard_listener_thread.daemon = True
    # quit_keyboard_listener_thread.start()

    storytelling_game()
    system_exit()
