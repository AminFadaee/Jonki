import json
import os
import re
from hashlib import md5
from urllib.parse import urlencode

import commonmark
import genanki
import requests

model = genanki.Model(
    1085971095731245,
    'Joplin Note', [
        {'name': 'Front'},
        {'name': 'Back'},
        {'name': 'Note Tags'}
    ], [{
        'name': 'Joplin Note',
        'qfmt': '{{Front}}<br><tags>Tags: {{Note Tags}}</tags>',
        'afmt': '{{FrontSide}}<hr id="answer">{{Back}}'
    }],
    css='''body{font-size:18px}
    tags, tag, tag.card.nightmode{font-size:90%;color:cyan}
    strong, strong.card.nightmode{color:#FFBF00}
    '''
)
default_deck = genanki.Deck(13242340924387509, 'Notes')


def extract_config(body: str):
    try:
        return json.loads(re.findall('#+ Quiz.*[\s\S]<!-- ?([\s\S]*) ?-->', body)[0])
    except Exception as exp:
        print(f'Error reading the config: {exp}')
        return dict()


def extract_answer(body: str, question: int):
    matches = re.findall(f'\[\]\({question}\)([\s\S]*?)\[\]\(/{question}\)', body)
    return '\n'.join(matches)


def extract_questions(body: str):
    return [
        re.findall('[0-9]+. (.*)', question)[0]
        for question in re.findall('#+ Quiz([\s\S]*)', body)[0].strip().split('\n')
        if question[0] in '0123456789'
    ]


def get_resource_mime_type(id):
    query_parameters = urlencode({'token': token, 'fields': 'id,mime'})
    url = f'http://127.0.0.1:41184/resources/{id}?{query_parameters}'
    response = requests.get(url)
    return response.json()['mime']


def download_resource(id, mime):
    query_parameters = urlencode({'token': token, })
    url = f'http://127.0.0.1:41184/resources/{id}/file?{query_parameters}'
    response = requests.get(url)
    filename = f'{id}.{mime.split("/")[1]}'
    path = f'resources/{filename}'
    file = open(path, 'wb')
    file.write(response.content)
    file.close()
    return filename


def get_deck(config, question: int):
    if 'deck' in config:
        return config['deck']
    elif 'decks' in config:
        for item in config['decks']:
            if question in item['questions']:
                return item['deck']
    return None


if 'JOPLIN_TOKEN' not in os.environ:
    raise LookupError("token not provided")

token = os.getenv('JOPLIN_TOKEN')
fields = 'id,parent_id,title'
limit = 100
page = 1
query_parameters = urlencode({
    'token': token,
    'fields': fields,
    'query': 'quiz',
    'type': 'note',
    'limit': limit,
    'page': page
})
url = f'http://127.0.0.1:41184/search?{query_parameters}'

response = requests.get(url)
notes = response.json()['items']
fronts = []
backs = []
all_tags = []
paths = []
ids = []
decks = []
all_decks = [default_deck]

for note in notes:
    id = note['id']
    query_parameters = urlencode({
        'token': token,
        'fields': 'body,id,title'
    })
    url = f'http://127.0.0.1:41184/notes/{id}?{query_parameters}'
    response = requests.get(url)
    body = response.json()['body']
    title = response.json()['title']
    note_id = response.json()['id']
    query_parameters = urlencode({
        'token': token,
        'fields': 'id,mime'
    })

    query_parameters = urlencode({
        'token': token,
        'fields': 'title',
        'limit': 100
    })
    url = f'http://127.0.0.1:41184/notes/{id}/tags?{query_parameters}'
    response = requests.get(url)
    tags = [
        item['title']
        for item in response.json()['items']
    ]
    config = extract_config(body)
    questions = extract_questions(body)
    for i, question in enumerate(questions):
        deck = get_deck(config, question=i + 1)
        answer = extract_answer(body, i + 1)
        if not answer:
            raise ValueError(f'Question "{question}" in Card "{title}" has no answer!')
        ids.append(id + str(i))
        fronts.append(question)
        backs.append(answer)
        all_tags.append(tags)
        decks.append(deck)

for i in range(len(fronts)):
    backs[i] = commonmark.commonmark(backs[i])
    backs[i] = re.sub(r'\$\$(.*?)\$\$', r'\[ \1 \]', backs[i])  # apply latex block
    backs[i] = re.sub(r'\$(.*?)\$', r'\( \1 \)', backs[i])  # apply latex
    new_back = backs[i]  # adding resources (only images)
    for match in re.findall(r'src="(.*?)"', backs[i]):
        if match.startswith(':/'):
            id = match[2:]
            mime = get_resource_mime_type(id)
            if mime.startswith('image'):
                filename = download_resource(id, mime)
                paths.append(f'resources/{filename}')
                new_back = re.sub(f'src=":/{id}"', f'src="{filename}"', new_back)
    backs[i] = new_back

    fronts[i] = commonmark.commonmark(fronts[i])
html = ''
for id, front, back, tags, deck_name in zip(ids, fronts, backs, all_tags, decks):
    tags_string = ', '.join(tags)
    html += f'{front}\n\n{back}<hr>'
    proper_tags = [
        tag.replace(' ', '_').replace('&', 'and').replace('-', '_').replace('.', '')
        for tag in tags
    ]
    note = genanki.Note(model=model, fields=[front, back, tags_string], tags=proper_tags, guid=id)
    if deck_name is None:
        default_deck.add_note(note)
    else:
        deck_id = int(md5(deck_name.lower().encode()).hexdigest(), 16) % 8
        deck = genanki.Deck(deck_id, deck_name)
        all_decks.append(deck)
        deck.add_note(note)
    default_deck = genanki.Deck(13242340924387509, 'Notes')

file = open('output.html', 'w')
file.write(html)
file.close()

package = genanki.Package(all_decks)
package.media_files = paths
package.write_to_file('notes.apkg')
