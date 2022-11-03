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
