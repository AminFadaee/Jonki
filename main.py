import os

import genanki

from anki.anki import Note
from anki.anki import model
from joplin.client import Joplin
from parsers.parser import extract_config, get_deck, extract_questions, extract_answer

joplin = Joplin(token=os.getenv('JOPLIN_TOKEN'))
notes = []
decks = set()
j_notes = list(joplin.get_notes())

for j_note in j_notes:
    config = extract_config(j_note.body)
    questions = extract_questions(j_note.body)
    for i, question in enumerate(questions):
        deck = get_deck(config, question=i + 1)
        answer = extract_answer(j_note.body, i + 1)
        if not answer:
            raise ValueError(f'Question "{question}" in Card "{j_note.title}" has no answer!')
        note = Note(j_note.id + str(i), question, answer, j_note.tags, j_note.resources, deck)
        notes.append(note)
        deck = note.get_anki_deck()
        deck.add_note(note.get_anki_note(model))
        decks.add(deck)

package = genanki.Package(decks)
package.media_files = [
    resource.path
    for note in notes
    for _, resource in note.resources.items()
]

package.write_to_file('notes.apkg')
