import httpx
import pytest
import requests


def run_get():
    response = requests.get('http://yandex.ru', allow_redirects=False)
    return response


def test_oneline(response_mock):

    with response_mock('GET http://yandex.ru -> 200 :Nice'):
        result = run_get()
        assert result.ok
        assert result.content == b'Nice'


def test_binary(response_mock):

    with response_mock(
            b'GET http://yandex.ru \n'
            b'Allow: GET, HEAD\n'
            b'Content-Language: ru\n'
            b'-> 200 :\xd1\x82\xd0\xb5\xd1\x81\xd1\x82'
    ):
        result = requests.get('http://yandex.ru', allow_redirects=False)
        assert result.ok
        assert result.content.decode() == 'тест'
        assert result.headers['Content-Language'] == 'ru'


def test_header_fields(response_mock):

    with response_mock('''
        GET http://yandex.ru

        Content-Type: image/png
        Cache-Control: no-cache,no-store,max-age=0,must-revalidate
        Set-Cookie: key1=val1

        -> 200 :Nicer
    '''):
        result = run_get()
        assert result.ok
        assert result.content == b'Nicer'
        assert dict(result.headers) == {
            'Content-Type': 'image/png',
            'Cache-Control': 'no-cache,no-store,max-age=0,must-revalidate',
            'Set-Cookie': 'key1=val1'
        }
        assert dict(result.cookies) == {'key1': 'val1'}


def test_many_lines(response_mock):

    with response_mock([
        'GET http://yandex.ru -> 200 :Nice',
        '',  # Support empty rule for debug actual request in tests.
    ]):
        result = run_get()
        assert result.content == b'Nice'


def test_status(response_mock):

    with response_mock('GET http://yandex.ru -> 500 :Bad'):
        result = run_get()
        assert not result.ok
        assert result.content == b'Bad'


def test_bypass(response_mock):

    with response_mock('GET http://yandex.ru -> 500 :Nice', bypass=True):
        result = run_get()
        assert result.status_code in {301, 302}  # https redirect


def test_httpx_sync(aresponse_mock):

    with aresponse_mock('GET http://yandex.ru -> 200 :Nice'):
        result = httpx.get('http://yandex.ru')
        assert result.status_code == 200
        assert result.content == b'Nice'


def test_httpx_headers(response_mock):

    with response_mock('''
        GET http://yandex.ru

        Content-Type: image/png
        Content-Language: ru

        -> 200 :Nicer
    ''', backend='httpx'):
        result = httpx.get('http://yandex.ru')
        assert result.headers['Content-Type'] == 'image/png'
        assert result.headers['Content-Language'] == 'ru'
        assert result.content == b'Nicer'


def test_both_backends(response_mock):

    with response_mock([
        'GET http://yandex.ru -> 200 :Nice',
        'GET http://google.com -> 200 :Sweet',
    ], backend='all'):
        assert requests.get('http://yandex.ru', allow_redirects=False).content == b'Nice'
        assert httpx.get('http://google.com').content == b'Sweet'


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_httpx_async(aresponse_mock):

    with aresponse_mock('GET http://yandex.ru -> 200 :Nice'):

        async with httpx.AsyncClient() as client:
            result = await client.get('http://yandex.ru')
            assert result.status_code == 200
            assert result.content == b'Nice'
