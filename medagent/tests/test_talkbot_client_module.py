import base64
import hashlib
import importlib
import json

import pytest
import requests

import medagent.talkbot_client as tc


def reload_module():
    importlib.reload(tc)


def test_encode_and_hash(tmp_path, monkeypatch):
    reload_module()
    data = b'hello world'
    file_path = tmp_path / 'test.bin'
    file_path.write_bytes(data)

    encoded = tc.encode_image_to_base64(str(file_path))
    expected = 'data:application/octet-stream;base64,' + base64.b64encode(data).decode()
    assert encoded == expected
    assert tc.sha256_file_hash(str(file_path)) == hashlib.sha256(data).hexdigest()


def test_headers(monkeypatch):
    reload_module()
    monkeypatch.setattr(tc, 'TALKBOT_TOKEN', 'token')
    h = tc._headers({'a': 1})
    assert h['Authorization'] == 'token'
    assert h['Content-Type'] == 'application/json'


def test_tb_chat_error(monkeypatch):
    reload_module()
    def fake_post(*a, **k):
        raise requests.RequestException('fail')
    monkeypatch.setattr(tc, 'requests', type('R', (), {'post': fake_post}))
    result = tc.tb_chat([{'role': 'user', 'content': 'hi'}])
    data = json.loads(result)
    assert data['text_summary'].startswith('خطا')


class DummyResp:
    def __init__(self, data):
        self._data = data
    def raise_for_status(self):
        pass
    def json(self):
        return self._data


def test_vision_analyze_base64(monkeypatch, tmp_path):
    reload_module()
    file_path = tmp_path / 'img.png'
    file_path.write_text('x')
    monkeypatch.setattr(tc, 'encode_image_to_base64', lambda p: 'DATA')
    monkeypatch.setattr(tc, 'sha256_file_hash', lambda p: 'HASH')
    def fake_post(url, headers=None, json=None, timeout=20):
        return DummyResp({'ok': True, 'body': json})
    monkeypatch.setattr(tc, 'requests', type('R', (), {'post': fake_post}))
    result = tc.vision_analyze(str(file_path), input_type='base64')
    assert result['ok'] is True
    assert result['body']['image_base64'] == 'DATA'
    assert result['body']['image_hash'] == 'HASH'
