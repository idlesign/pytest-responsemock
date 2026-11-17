from functools import partial

import pytest

from .utils import response_mock as response_mock_


@pytest.fixture
def response_mock() -> response_mock_:
    """Fixture exposing simple context manager to mock responses for `requests` and `httpx` packages.

    Any request under that manager will be intercepted and mocked according
    to one or more ``rules`` passed to the manager. If actual request won't fall
    under any of given rules then an exception is raised (by default).

    The backend is selected with the ``backend`` argument: ``requests`` (default)
    intercepts `requests` only, ``httpx`` intercepts `httpx` (both sync and async
    clients) only, ``all`` intercepts both.

    Rules are simple strings, of pattern: ``HTTP_METHOD URL -> STATUS_CODE :BODY``.

    Example::

        def test_me(response_mock):


            json_response = json.dumps({'key': 'value', 'another': 'yes'})

            with response_mock([

                'GET http://a.b -> 200 :Nice',

                f'POST http://some.domain -> 400 :{json_response}',

                '''
                GET https://some.domain

                Allow: GET, HEAD
                Content-Language: ru

                -> 200 :OK
                ''',

            ], bypass=False) as mock:

                mock.add_passthru('http://c.d')

                this_mades_requests()


    """
    return response_mock_


@pytest.fixture
def aresponse_mock() -> response_mock_:
    """Fixture exposing the same context manager as ``response_mock``,
    but preset to intercept `httpx` only (both sync and async clients).

    Example::

        async def test_me(aresponse_mock):

            with aresponse_mock('GET http://a.b -> 200 :Nice'):

                async with httpx.AsyncClient() as client:
                    await client.get('http://a.b')

    """
    return partial(response_mock_, backend='httpx')
