import json
import re


def extract_config(body: str):
    try:
        return json.loads(re.findall('#+ Quiz.*[\s\S]<!-- ?([\s\S]*) ?-->', body)[0])
    except Exception as exp:
        print(f'Error reading the config: {exp}')
        return dict()


def get_deck(config, question: int):
    if 'deck' in config:
        return config['deck']
    elif 'decks' in config:
        for item in config['decks']:
            if question in item['questions']:
                return item['deck']
    return None


def extract_answer(body: str, question: int):
    matches = re.findall(f'\[\]\({question}\)([\s\S]*?)\[\]\(/{question}\)', body)
    return '\n\n'.join(matches)


def extract_questions(body: str):
    return [
        re.findall('[0-9]+. (.*)', question)[0]
        for question in re.findall('#+ Quiz([\s\S]*)', body)[0].strip().split('\n')
        if question[0] in '0123456789'
    ]
