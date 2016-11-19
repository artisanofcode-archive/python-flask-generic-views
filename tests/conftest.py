import os

import pytest
from flask import Flask
from hypothesis import settings

settings.register_profile('slow', settings(max_examples=200))
settings.register_profile('fast', settings(max_examples=20))
settings.load_profile(os.getenv(u'HYPOTHESIS_PROFILE', 'fast'))


@pytest.fixture(autouse=True)
def flask(request):
    app = Flask(__name__)
    ctx = app.test_request_context('/')
    ctx.push()

    request.addfinalizer(ctx.pop)
