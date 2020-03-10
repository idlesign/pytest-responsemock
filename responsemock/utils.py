from contextlib import contextmanager
from typing import Union, List, Generator, Optional

if False:  # pragma: nocover
    from responses import RequestsMock


@contextmanager
def response_mock(
        rules: Union[List[str], str],
        *,
        bypass: bool = False,
        **kwargs
) -> Generator[Optional['RequestsMock'], None, None]:
    """Simple context manager to mock responses for `requests` package.

    Any request under that manager will be intercepted and mocked according
    to one or more ``rules`` passed to the manager. If actual request won't fall
    under any of given rules then an exception is raised (by default).

    Rules are simple strings, of pattern: ``HTTP_METHOD URL -> STATUS_CODE :BODY``.

    Example::

        def test_me(response_mock):


            json_response = json.dumps({'key': 'value', 'another': 'yes'})

            with response_mock([

                'GET http://a.b -> 200 :Nice',
                f'POST http://some.domain -> 400 :{json_response}'

            ], bypass=False) as mock:

                mock.add_passthru('http://c.d')

                this_mades_requests()

    :param rules: One or several rules for response.
    :param bypass: Whether to to bypass (disable) mocking.
    :param kwargs: Additional keyword arguments to pass to `RequestsMock`.

    """
    from responses import RequestsMock

    if bypass:

        yield

    else:

        with RequestsMock(**kwargs) as mock:

            if isinstance(rules, str):
                rules = [rules]

            for rule in rules:

                if not rule:
                    continue

                directives, _, response = rule.partition('->')

                directives = list(filter(None, map(str.strip, directives.split(' '))))

                assert len(directives) == 2, (
                    f'Unsupported directives: {directives}. Expected: HTTP_METHOD URL')

                status, _, response = response.partition(':')

                status = int(status.strip())

                mock.add(
                    method=directives[0],
                    url=directives[1],
                    body=response,
                    status=status,
                )

            yield mock
