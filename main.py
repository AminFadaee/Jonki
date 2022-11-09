import os

import genanki

from anki.anki import Note
from anki.anki import model
from joplin.client import get_notes, get_tags, get_title_and_body
from parsers.parser import extract_config, get_deck, extract_questions, extract_answer

j_notes = get_notes()
notes = []
decks = set()

for j_note in j_notes:
    note_id = j_note['id']
    title, body = get_title_and_body(note_id)
    tags = get_tags(note_id)
    config = extract_config(body)
    questions = extract_questions(body)
    for i, question in enumerate(questions):
        deck = get_deck(config, question=i + 1)
        answer = extract_answer(body, i + 1)
        if not answer:
            raise ValueError(f'Question "{question}" in Card "{title}" has no answer!')
        note = Note(note_id + str(i), question, answer, tags, deck)
        notes.append(note)
        deck = note.get_anki_deck()
        deck.add_note(note.get_anki_note(model))
        decks.add(deck)

package = genanki.Package(decks)
package.media_files = [
    resource
    for note in notes
    for resource in note.resources
]
package.write_to_file('notes.apkg')
