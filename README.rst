pytest-responsemock
===================
https://github.com/idlesign/pytest-responsemock

|release| |lic| |ci| |coverage|

.. |release| image:: https://img.shields.io/pypi/v/pytest-responsemock.svg
    :target: https://pypi.python.org/pypi/pytest-responsemock

.. |lic| image:: https://img.shields.io/pypi/l/pytest-responsemock.svg
    :target: https://pypi.python.org/pypi/pytest-responsemock

.. |ci| image:: https://img.shields.io/travis/idlesign/pytest-responsemock/master.svg
    :target: https://travis-ci.org/idlesign/pytest-responsemock

.. |coverage| image:: https://img.shields.io/coveralls/idlesign/pytest-responsemock/master.svg
    :target: https://coveralls.io/r/idlesign/pytest-responsemock


Description
-----------

*Simplified requests calls mocking for pytest*

Provides ``response_mock`` fixture, exposing simple context manager.

Any request under that manager will be intercepted and mocked according
to one or more ``rules`` passed to the manager. If actual request won't fall
under any of given rules then an exception is raised (by default).

Rules are simple strings, of pattern: ``HTTP_METHOD URL -> STATUS_CODE :BODY``.


Requirements
------------

* Python 3.6+


Usage
-----

When this package is installed ``response_mock`` is available for ``pytest`` test functions.

.. code-block:: python

    def for_test():
        return requests.get('http://some.domain')


    def test_me(response_mock):

        # Pass response rule as a string,
        # or many rules (to mock consequent requests) as a list of strings.
        # Use optional `bypass` argument to disable mock conditionally.

        with response_mock('GET http://some.domain -> 200 :Nice', bypass=False):

            result = for_test()

            assert result.ok
            assert result.content == b'Nice'


Test json response:

.. code-block:: python

    response = json.dumps({'key': 'value', 'another': 'yes'})

    with response_mock(f'POST http://some.domain -> 400 :{response}'):
        ...


Access underlying RequestsMock (from ``responses`` package) as ``mock``:

.. code-block:: python

    with response_mock(f'HEAD http://some.domain -> 200 :Nope') as mock:

        mock.add_passthru('http://other.domain')

