import requests


def run_get():
    response = requests.get('http://yandex.ru', allow_redirects=False)
    return response


def test_oneline(response_mock):

    with response_mock('GET http://yandex.ru -> 200 :Nice'):
        result = run_get()
        assert result.ok
        assert result.content == b'Nice'


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
        assert result.status_code == 302  # https redirect
