from contextlib import ExitStack, contextmanager
from textwrap import dedent
from typing import Any, Dict, Generator, List, Literal, Union

if False:  # pragma: nocover
    from responses import RequestsMock  # noqa

TypeRule = Union[str, bytes]

TypeRuleParsed = Dict[str, Union[str, bytes, int, Dict[str, str]]]


def parse_rules(rules: Union[List[TypeRule], TypeRule]) -> List[TypeRuleParsed]:
    """Parses rule strings into structured dicts.

    Rules are simple strings, of pattern: ``HTTP_METHOD URL -> STATUS_CODE :BODY``.

    :param rules: One or several rules for response.

    """
    parsed = []

    if isinstance(rules, (str, bytes)):
        rules = [rules]

    for rule in rules:

        if not rule:
            continue

        is_binary = isinstance(rule, bytes)

        if not is_binary:
            rule = dedent(rule)

        rule = rule.strip()

        type_ = bytes if is_binary else str
        newline = b'\n' if is_binary else '\n'
        colon = b':' if is_binary else ':'

        def enc(val, binary=is_binary):
            return val.encode() if binary else val

        def dec(val, binary=is_binary):
            return val.decode() if binary else val

        directives, _, response = rule.partition(enc('->'))

        headers = {}

        if newline in directives:
            directives, *headers_block = directives.splitlines()

            for header_line in headers_block:
                header_line = header_line.strip()

                if not header_line:
                    continue

                key, _, val = header_line.partition(colon)
                val = val.strip()

                if val:
                    headers[dec(key.strip())] = dec(val)

        directives = list(
            filter(
                None,
                map(
                    type_.strip,
                    directives.split(enc(' '))
                )
            ))

        if len(directives) != 2:
            raise ValueError(f'Unsupported directives: {directives}. Expected two entries: HTTP_METHOD and URL')

        status, _, response = response.partition(colon)

        parsed.append({
            'method': dec(directives[0]),
            'url': dec(directives[1]),
            'status': int(status.strip()),
            'headers': headers,
            'body': response,
        })

    return parsed


@contextmanager
def response_mock(
        rules: Union[List[TypeRule], TypeRule],
        *,
        bypass: bool = False,
        backend: Literal['requests', 'httpx', 'all'] = 'requests',
        **kwargs
) -> Generator[Any, None, None]:
    """Simple context manager to mock responses for `requests` and `httpx` packages.

    Any request under that manager will be intercepted and mocked according
    to one or more ``rules`` passed to the manager. If actual request won't fall
    under any of given rules then an exception is raised (by default).

    Rules are simple strings, of pattern: ``HTTP_METHOD URL -> STATUS_CODE :BODY``.

    Example::

        def test_me(response_mock):


            json_response = json.dumps({'key': 'value', 'another': 'yes'})

            with response_mock([

                'GET http://a.b -> 200 :Nice',

                b'GET http://a.b/binary/ -> 200 :\xd1\x82\xd0\xb5\xd1\x81\xd1\x82',

                f'POST http://some.domain -> 400 :{json_response}'

                '''
                GET https://some.domain

                Allow: GET, HEAD
                Content-Language: ru

                -> 200 :OK
                '''

            ], bypass=False) as mock:

                mock.add_passthru('http://c.d')

                this_makes_requests()

    :param rules: One or several rules for response.
    :param bypass: Whether to bypass (disable) mocking.
    :param backend: Backend selection:

        * ``requests`` (default) — intercept `requests` only;
        * ``httpx`` — intercept `httpx` (both sync and async clients) only;
        * ``all`` — intercept both.

        Note that with both backends active the `assert_all_requests_are_fired`
        option of ``RequestsMock`` defaults to ``False``, since rules may fire
        through either of the two backends.

    :param kwargs: Additional keyword arguments to pass to `RequestsMock`.

    """
    if bypass:

        yield
        return

    parsed = parse_rules(rules)

    use_requests = backend != 'httpx'
    use_httpx = backend != 'requests'

    if not (use_requests or use_httpx):
        raise ValueError(f'Unsupported backend: {backend}')

    with ExitStack() as stack:

        mock = None

        if use_requests:
            from responses import RequestsMock

            if use_httpx:
                # With two active backends rules may fire through either of them,
                # so the per-backend "all fired" assertion cannot hold.
                kwargs.setdefault('assert_all_requests_are_fired', False)

            mock = stack.enter_context(RequestsMock(**kwargs))

            for rule in parsed:

                headers = dict(rule['headers'])

                add_kwargs = {}

                content_type = headers.pop('Content-Type', None)

                if content_type:
                    add_kwargs['content_type'] = content_type

                mock.add(
                    method=rule['method'],
                    url=rule['url'],
                    body=rule['body'],
                    status=rule['status'],
                    adding_headers=headers or None,
                    **add_kwargs
                )

        if use_httpx:
            import respx

            router = stack.enter_context(respx.mock(
                # Strictness is only possible when no other backend may serve the rules.
                assert_all_called=not use_requests,
            ))

            for rule in parsed:
                router.route(method=rule['method'], url=rule['url']).respond(
                    status_code=rule['status'],
                    content=rule['body'],
                    headers=rule['headers'] or None,
                )

            if mock is None:
                mock = router

        yield mock
