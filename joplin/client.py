import re
from typing import List
from urllib.parse import urlencode

import requests


class Question:
    def __init__(self):
        pass


class JoplinResource:
    def __init__(self, joplin_resource_id: str, token: str):
        self._resource_id = joplin_resource_id
        self._token = token
        self._mime_type = None
        self._filename = None
        self._path = None

    @property
    def mime_type(self) -> str:
        if self._mime_type is None:
            self._fetch_resource_mime_type()
        return self._mime_type

    @property
    def filename(self):
        if self._filename is None:
            self._download_resource()
        return self._filename

    @property
    def path(self):
        if self._path is None:
            self._download_resource()
        return self._path

    def _download_resource(self):
        filename = f'{self._resource_id}.{self.mime_type.split("/")[1]}'
        path = f'resources/{filename}'
        query_parameters = urlencode({'token': self._token, })
        url = f'http://127.0.0.1:41184/resources/{self._resource_id}/file?{query_parameters}'
        response = requests.get(url)
        file = open(path, 'wb')
        file.write(response.content)
        file.close()
        self._path = path
        self._filename = filename

    def _fetch_resource_mime_type(self):
        query_parameters = urlencode({'token': self._token, 'fields': 'id,mime'})
        url = f'http://127.0.0.1:41184/resources/{self._resource_id}?{query_parameters}'
        response = requests.get(url)
        self._mime_type = response.json()['mime']


class JoplinResources:
    def __init__(self, note_body: str, token: str):
        self.note_body = note_body
        self._resources = dict()
        self.token = token
        self._resource_ids = re.findall(r'!\[.*?]\(:/(.*?)\)', self.note_body)
        self._index = 0

    def __getitem__(self, resource_id):
        if resource_id in self._resources:
            return self._resources[resource_id]
        resource = self._fetch_resource(resource_id)
        if resource:
            self._resources[resource_id] = resource
        return self._resources[resource_id]

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._resource_ids):
            self._index = 0
            raise StopIteration
        resource_id = self._resource_ids[self._index]
        self._index += 1
        return resource_id

    def items(self):
        for resource_id in self:
            yield resource_id, self[resource_id]

    def _fetch_resource(self, resource_id):
        if re.findall(r'!\[.*?]\(:/(.*?)\)', self.note_body):
            return JoplinResource(resource_id, self.token)


class JoplinNote:
    def __init__(self, joplin_note_id: str, token: str, title=None, body=None):
        self._note_id = joplin_note_id
        self._token = token
        self._title = title
        self._body = body
        self._tags = None
        self._resources = None

    @property
    def id(self) -> str:
        return self._note_id

    @property
    def title(self) -> str:
        if self._title is None:
            self._fetch_title_and_body()
        return self._title

    @property
    def body(self) -> str:
        if self._body is None:
            self._fetch_title_and_body()
        return self._body

    @property
    def tags(self) -> List[str]:
        if self._tags is None:
            self._fetch_tags()
        return self._tags

    @property
    def resources(self) -> JoplinResources:
        if self._resources is None:
            self._resources = JoplinResources(self.body, self._token)
        return self._resources

    def _fetch_tags(self):
        query_parameters = urlencode({
            'token': self._token,
            'fields': 'title',
            'limit': 100
        })
        url = f'http://127.0.0.1:41184/notes/{self._note_id}/tags?{query_parameters}'
        response = requests.get(url)
        self._tags = [
            item['title']
            for item in response.json()['items']
        ]

    def _fetch_title_and_body(self):
        query_parameters = urlencode({
            'token': self._token,
            'fields': 'body,id,title'
        })
        url = f'http://127.0.0.1:41184/notes/{self._note_id}?{query_parameters}'
        response = requests.get(url)
        self._body = response.json()['body']
        self._title = response.json()['title']


class Joplin:
    def __init__(self, token: str):
        self.token = token

    def _request(self, page=1):
        fields = 'id,title,body'
        limit = 100
        query_parameters = urlencode({
            'token': self.token,
            'fields': fields,
            'query': 'quiz',
            'type': 'note',
            'limit': limit,
            'page': page
        })
        url = f'http://127.0.0.1:41184/search?{query_parameters}'

        response = requests.get(url)
        notes = response.json()['items']
        continued = response.json()['has_more']
        return notes, continued

    def get_notes(self) -> List[JoplinNote]:
        page = 0
        continued = True
        while continued:
            page += 1
            notes, continued = self._request(page)
            for note_data in notes:
                yield JoplinNote(
                    token=self.token,
                    joplin_note_id=note_data['id'],
                    title=note_data['title'],
                    body=note_data['body']
                )
