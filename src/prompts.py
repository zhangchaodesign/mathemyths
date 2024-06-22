def storytelling_prompt_quan(character, name, setting, vocabulary, child_name, child_gender) -> str:
    """
    Compose a straightforward prompt to initiate a joint storytelling game with a 6-year-old.

    Returns:
        prompt
    """

    formatted_vocabulary = ' '.join(
        [f'"{word},"' for word in vocabulary[:-1]])
    formatted_vocabulary += f' or "{vocabulary[-1]}."'

    if child_name == 'none' or child_gender == 'none':
        prompt = f"Let's play a joint storytelling game where we build a story together with the main character being a {character} named {name} in the {setting}. This story should revolve around the main character reaching a certain location, attaining a certain object, or fulfilling a certain objective while conquering many obstacles along the way.\n" + "To start, please craft a 2-sentence introduction to the story. From there, we will alternate turns, with each person adding more to the story. Your response should be simple and appropriate for a young child. When it is your turn, only write the story content while using as many of the following words as possible: " + formatted_vocabulary + \
            " To indicate usage, enclose them in parentheses (like this).\nPlease keep your responses simple and appropriate for a young child. Please do not ask me any questions or respond with anything unrelated to the story. If I need to communicate with you in English, I will use curly brackets {like this}.\nPlease be creative and have fun with this storytelling adventure! If you understand and are ready to begin, respond with only \"yes.\" "
    else:
        prompt = f"Let's play a joint storytelling game where we build a story together with the main character being a {character} named {name} in the {setting}. This story should revolve around the main character and a little {child_gender} named {child_name} reaching a certain location, attaining a certain object, or fulfilling a certain objective while conquering many obstacles along the way.\n" + "To start, please craft a 2-sentence introduction to the story. From there, we will alternate turns, with each person adding more to the story. When it is your turn, only write the story content while using as many of the following words as possible: " + formatted_vocabulary + \
            " To indicate usage, enclose them in parentheses (like this).\nPlease keep your responses simple and appropriate for a young child. Please do not ask me any questions or respond with anything unrelated to the story. If I need to communicate with you in English, I will use curly brackets {like this}.\nPlease be creative and have fun with this storytelling adventure! If you understand and are ready to begin, respond with only \"yes.\" "

    return prompt


def storytelling_chat_preset(character, name, setting, content, vocabulary, child_name, child_gender) -> list:
    """
    Compose a preset to initiate a joint storytelling game with a 6-year-old.

    Returns:
        chat preset
    """

    chat = [{"role": "system", "content": storytelling_prompt_quan(character, name, setting, vocabulary, child_name, child_gender)}, {
        "role": "assistant", "content": "Yes."}, {"role": "user", "content": "Let's start."}]

    return chat


def simulator_chat_preset(character, name, setting) -> list:
    """
    Compose a preset to simulate a joint storytelling game with a agent.

    Returns:
        chat preset
    """

    chat = [{"role": "system", "content": simulator_prompt(character, name, setting)}, {
        "role": "assistant", "content": "Yes."}]

    return chat


def storytelling_prompt_addon_continue(terms, explain) -> str:
    """
    Compose an addon prompt to continue the story.

    Returns:
        addon
    """

    formatted_terms = ' '.join([f'"{word},"' for word in terms])

    addon = "{First, in curly brackets, acknowledge my addition and commend me in a concise 10-word sentence. Next, continue the story by correctly using " + \
        formatted_terms + " or their variants within two distinct 15-word sentences. " + \
            "Lastly, explain their meanings within a 20-word sentence, grounding it firmly within the story's context. " if explain else '' + \
        "Do not end the story.}"

    return addon


def storytelling_prompt_addon_continue_no_praise(terms, explain) -> str:
    """
    Compose an addon prompt to continue the story.

    Returns:
        addon
    """

    formatted_terms = ' '.join([f'"{word},"' for word in terms])

    addon = "{Continue the story straight away by correctly using " + \
        formatted_terms + " or their variants two 15-word sentences. " + \
            "Lastly, explain their meanings within a 20-word sentence, grounding it firmly within the story's context. " if explain else '' + \
        "Do not end the story.}"

    return addon


def storytelling_prompt_addon_end(terms, explain) -> str:
    """
    Compose an addon prompt to end the story.

    Returns:
        addon
    """

    formatted_terms = ' '.join([f'"{word},"' for word in terms])
    

    addon = "{First, in curly brackets, acknowledge my addition and commend me in a concise 10-word sentence. Next, end the story by correctly using " + \
        formatted_terms + \
            " or their variants within two distinct 15-word sentences. " + "Then, explain their meanings within a 20-word sentence, grounding it firmly within the story's context. " if explain else '' + \
        "Lastly, summarize the story in one 30-word sentence.}"

    return addon


def storytelling_prompt_addon_end_no_praise(terms, explain) -> str:
    """
    Compose an addon prompt to end the story.

    Returns:
        addon
    """

    formatted_terms = ' '.join([f'"{word},"' for word in terms])

    addon = "{First, end this story straight away by correctly using " + formatted_terms + \
        " or their variants within two distinct 15-word sentences. " + "Next, explain their meanings within a 20-word sentence, grounding it firmly within the story's context. " if explain else '' + \
            "Lastly, summarize the story in one 30-word sentence.}"

    return addon


def storytelling_prompt_addon_identifier() -> str:
    """
    Compose an identifier prompt to encourage the child.

    Returns:
        identifier
    """

    identifier = """As a language model, your task is to determine whether a given phrase expresses a feeling or emotion in the first person, such as uncertainty, agreement, satisfaction, or interest. Your response should be a binary output of either 1 or 0, where 1 indicates that the phrase does express a feeling or emotion in the first person, and 0 indicates that it does not.

    I don't know: 1
    I like it: 1
    I don't like it: 1
    Diego is happy: 0
    He is sad: 0
    I am not sure: 1
    """

    return identifier


def storytelling_prompt_encouragement(question) -> str:
    """
    Compose an encouragement prompt to encourage the child.

    Returns:
        encouragement
    """

    encouragement = "You and a 6-year-old are playing a storytelling game, taking turns to contribute to a unique story. However, when the child fails to continue the story or just wants you to continue the story, your task is to encourage them to keep going by simplifying this question: " + \
        question + " and give them some hints. Limit your response to 30 words."

    return encouragement


def storytelling_prompt_creativity(question) -> str:
    """
    Compose an creativity prompt to encourage the child.

    Returns:
        creativity
    """

    creativity = "You and a 6-year-old are playing a storytelling game, taking turns to contribute to a unique story. However, Sometimes the child just says a few words, your task is to first acknowledge what he says and then encourage him to say more. Limit your response to 30 words."

    return creativity


def question_generator_prompt_quan(vocabulary) -> str:
    """
    Compose a straightforward question to prompt a 6-year-old to expand on an unfinished story.

    Returns:
        prompt
    """

    if set(vocabulary).issubset(['equal', 'sum', 'half', 'add', 'subtract', 'estimate', 'quarter', 'percentage', 'divide', 'multiply']):
        formatted_vocabulary = ' '.join(
            [f'"{word},"' for word in vocabulary[:-1]])
        formatted_vocabulary += f' and "{vocabulary[-1]}"'

        prompt = "Given an unfinished story, compose one single, straightforward question to prompt a 6-year-old to expand on the story. The question should focus on the main character's next steps or feelings and motivate the child to use words like " + \
            formatted_vocabulary + \
            " in their response. Do not mention \"math\", \"mathematics\", and \"mathematical skills\". Limit your response to 20 words. Simple future tense. Only reply with the question." + """
            <!--start-example1-input-->
            In a distant galaxy, a robot named Diego embarked on a journey to retrieve a rare artifact that would bring balance to his home planet. His objective was to locate the legendary Crystal of Equilibrium, which was said to hold the power to create equal harmony among the stars.: Once Diego finds the Crystal of Equilibrium, how do you think he will use its power to create equal harmony among the stars?
            <!--end-example1-input-->
            <!--start-example1-output-->
            Once Diego finds the Crystal of Equilibrium, how do you think he will use its power to create equal harmony among the stars?
            <!--end-example1-output-->
            <!--start-example2-input-->
            Samantha knew that the sum of challenges she would face would be great, but she was determined to succeed. She began her journey, keeping her eyes and ears open for any clues that would lead her closer to the gem.
            <!--end-example2-input-->
            <!--start-example2-output-->
            What challenges do you think Samantha will face halfway through the journey?
            <!--end-example2-output-->
            <!--start-example3-input-->
            Jennie overheard a group of sea creatures talking about the cave's entrance, which could only be found when the sum of the three tallest coral reefs was equal to the depth of the sunken ship nearby. Determined to solve this riddle, Jennie decided to set out and add this great adventure to her life's experiences.
            <!--end-example3-input-->
            <!--start-example3-output-->
            How do you think Jennie will figure out if the sum of the heights of the three tallest coral reefs is equal to the depth of the sunken ship nearby?
            <!--end-example3-output-->
            <!—start-example4-input-->
            As he trotted through the city, Tom stumbled upon a wise old dog who claimed to know the exact location of the park. The elder dog agreed to share the information, but only if Tom could solve a riddle: "What is half of one hundred?"
            <!—end-example4-input-->
            <!—start-example4-output—>
            How do you think Tom will estimate “What is half of one hundred”?
            <!--end-example4-output—>
            <!—start-example5-input-->
            As Ashley embarked on her journey, she began to subtract her old habits of procrastination and self-doubt. With each passing day, her confidence grew, and she soared higher and higher towards her goal.
            <!—end-example5-input-->
            <!—start-example5-output—>
            What do you think Ashley will do to subtract old habits and add more self-confidence?
            <!--end-example5-output—>
            <!—start-example6-input-->
            The ancient prophecy stated that the Dragon's Heart would be hidden in a place where the sum of two particular rivers met. Michael realized that the location must equal to the intersection of the mighty Sapphire River and the mysterious Emerald River, deep within the enchanted forest.
            <!—end-example6-input-->
            <!—start-example6-output—>
            What do you think Michael will do to estimate where the two rivers meet?
            <!--end-example6-output-->
            <!—start-example7-input-->
            Tommy estimated that the treasure was hidden somewhere deep within the mysterious forest, which was said to be full of challenges and riddles. Together, they decided to divide their tasks to conquer the obstacles in their path more efficiently.
            <!—end-example7-input→
            <!—start-example7-output—>
            What do you think they will do to divide their tasks? 
            <!--end-example7-output→
            <!—start-example8-input-->
            To reach the cave, Bruce knew he would have to add many miles to his daily swim. As he journeyed, he encountered various sea creatures who multiplied his knowledge about the ocean and its mysteries.
            <!—end-example8-input→
            <!—start-example8-output—>
            How do you think Bruce will use the knowledge he gained to multiply his understanding of the ocean? 
            <!--end-example8-output-->
            """
    else:
        formatted_vocabulary = ' '.join(
            [f'"{word},"' for word in vocabulary[:-1]])
        formatted_vocabulary += f' and "{vocabulary[-1]}"'

        prompt = "Given an unfinished story, compose one single, straightforward question to prompt a 6-year-old to expand on the story. The question should focus on the main character's next steps or feelings and motivate the child to use words like " + \
            formatted_vocabulary + \
            " in their response. Do not mention \"math\", \"mathematics\", and \"mathematical skills\". Limit your response to 20 words. Simple future tense. Only reply with the question."

    return prompt


def extract_character_preset(response) -> str:
    """
    Compose a prompt to extract the character from the user's response

    Returns:
        preset
    """

    prompt = """
    I want you to extract the character from the user's response to the question, "First, let's choose a character. You can choose from a panda, a robot, a penguin, a donut, a dog, or anything else you'd like. Which one would you like to be?"

    A robot: robot
    The character will be a cat: cat
    I like coconuts: coconut
    It must be an alien: alien
    Can it be a train: train
    """

    chat = [{"role": "system", "content": prompt}, {
        "role": "user", "content": "User: " + response + ": "}]

    return chat


def extract_name_preset(response) -> str:
    """
    Compose a prompt to extract the name from the user's response

    Returns:
        preset
    """

    prompt = """
    I want you to extract the name from the user's response to the question, "Great! Now, let's give your character a name. What would you like to name your character?"

    He name is Jack: Jack
    She will be Selena: Selena
    Tim: Tim
    It is Tommy: Tommy
    """

    chat = [{"role": "system", "content": prompt}, {
        "role": "user", "content": "User: " + response + ": "}]

    return chat


def extract_setting_preset(response) -> str:
    """
    Compose a prompt to extract the setting from the user's response

    Returns:
        preset
    """

    prompt = """
    I want you to extract the setting from the user's response to the question, "Awesome! Now, let's choose a setting. You can choose from a forest, a space, a mountain, a house, a city, or anything else you'd like. Where would you like your story to take place?"

    The story will take place in a forest: forest
    It should be in the space: space
    I think it would happen in a sea: sea
    Maybe in my house: house
    """

    chat = [{"role": "system", "content": prompt}, {
        "role": "user", "content": "User: " + response + ": "}]

    return chat


def extract_story_elements(response) -> str:
    """
    Compose a prompt to extract the story elements from the user's response

    Returns:
        preset
    """

    prompt = """
    I want you to extract the character, the character's name, and the setting for a story from the user's response. Please return the answer in JSON format.

    A robot named Diego will be in the space: {"character": "robot", "name": "Diego", "setting": "space"}
    The character is a dog. His name is Tommy. He will be in the forest: {"character": "dog", "name": "Tommy", "setting": "forest"}
    I like coconuts. So the character is a coconut. Her name will be Samantha. She is in my home: {"character": "coconut", "name": "Samantha", "setting": "home"}
    """

    chat = [{"role": "system", "content": prompt}, {
        "role": "user", "content": "User: " + response + ": "}]

    return chat


if __name__ == "__main__":
    print(question_generator_prompt_quan(
        ['equal', 'sum', 'half', 'add', 'subtract', 'estimate']))
