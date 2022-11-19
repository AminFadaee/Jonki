import re
from hashlib import md5

import commonmark
import genanki

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


class Note:
    def __init__(self, guid, front, back, tags, resources, deck):
        self.guid = guid
        self.front = self._preprocess_front(front)
        self.resources = resources
        self.back = self._preprocess_back(back, self.resources)
        self.tags = tags
        self.deck = deck

    def _preprocess_back(self, back, resources):
        back = commonmark.commonmark(back)
        back = re.sub(r'\$\$(.*?)\$\$', r'\[ \1 \]', back)  # apply latex block
        back = re.sub(r'\$(.*?)\$', r'\( \1 \)', back)  # apply latex
        for resource_id, resource in resources.items():
            back = re.sub(f'src=":/{resource_id}"', f'src="{resource.filename}"', back)
        return back

    def _preprocess_front(self, front):
        front = commonmark.commonmark(front)
        return front

    def _get_tag_string(self):
        return ', '.join(self.tags)

    def _get_anki_tags(self):
        return [
            tag.replace(' ', '_').replace('&', 'and').replace('-', '_').replace('.', '')
            for tag in self.tags
        ]

    def get_anki_note(self, anki_model):
        return genanki.Note(
            model=anki_model,
            fields=[self.front, self.back, self._get_tag_string()],
            tags=self._get_anki_tags(),
            guid=self.guid
        )

    def get_anki_deck(self):
        if self.deck is None:
            return default_deck
        else:
            deck_id = int(md5(self.deck.lower().encode()).hexdigest(), 16) % 10 ** 8
            return genanki.Deck(deck_id, self.deck)
