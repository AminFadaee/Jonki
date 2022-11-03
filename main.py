import os
import re
from hashlib import md5
from typing import List

import commonmark
import genanki

from anki.anki import default_deck, model
from joplin.client import get_notes, get_resource_mime_type, download_resource, get_tags, get_title_and_body
from parsers.parser import extract_config, get_deck, extract_questions, extract_answer


if 'JOPLIN_TOKEN' not in os.environ:
    raise LookupError("token not provided")

token = os.getenv('JOPLIN_TOKEN')
notes = get_notes(token)
fronts = []
backs = []
all_tags = []
paths = []
ids = []
decks = []
all_decks = [default_deck]

for note in notes:
    note_id = note['id']
    title, body = get_title_and_body(token, note_id)
    tags = get_tags(token, note_id)
    config = extract_config(body)
    questions = extract_questions(body)
    for i, question in enumerate(questions):
        deck = get_deck(config, question=i + 1)
        answer = extract_answer(body, i + 1)
        if not answer:
            raise ValueError(f'Question "{question}" in Card "{title}" has no answer!')
        ids.append(note_id + str(i))
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
            mime = get_resource_mime_type(token, id)
            if mime.startswith('image'):
                filename = download_resource(token, id, mime)
                paths.append(f'resources/{filename}')
                new_back = re.sub(f'src=":/{id}"', f'src="{filename}"', new_back)
    backs[i] = new_back

    fronts[i] = commonmark.commonmark(fronts[i])
for id, front, back, tags, deck_name in zip(ids, fronts, backs, all_tags, decks):
    tags_string = ', '.join(tags)
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

package = genanki.Package(all_decks)
package.media_files = paths
package.write_to_file('notes.apkg')
