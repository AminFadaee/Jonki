from urllib.parse import urlencode

import requests


def get_title_and_body(token, note_id):
    query_parameters = urlencode({
        'token': token,
        'fields': 'body,id,title'
    })
    url = f'http://127.0.0.1:41184/notes/{note_id}?{query_parameters}'
    response = requests.get(url)
    body = response.json()['body']
    title = response.json()['title']
    return title, body


def get_tags(token, note_id):
    query_parameters = urlencode({
        'token': token,
        'fields': 'title',
        'limit': 100
    })
    url = f'http://127.0.0.1:41184/notes/{note_id}/tags?{query_parameters}'
    response = requests.get(url)
    return [
        item['title']
        for item in response.json()['items']
    ]


def get_resource_mime_type(token, id):
    query_parameters = urlencode({'token': token, 'fields': 'id,mime'})
    url = f'http://127.0.0.1:41184/resources/{id}?{query_parameters}'
    response = requests.get(url)
    return response.json()['mime']


def download_resource(token, id, mime):
    query_parameters = urlencode({'token': token, })
    url = f'http://127.0.0.1:41184/resources/{id}/file?{query_parameters}'
    response = requests.get(url)
    filename = f'{id}.{mime.split("/")[1]}'
    path = f'resources/{filename}'
    file = open(path, 'wb')
    file.write(response.content)
    file.close()
    return filename


def get_notes(token):
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
    return notes
