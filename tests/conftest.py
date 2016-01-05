import os

import pytest
from flask import Flask
from hypothesis import Settings

Settings.register_profile('slow', Settings(max_examples=200))
Settings.register_profile('fast', Settings(max_examples=20))
Settings.load_profile(os.getenv(u'HYPOTHESIS_PROFILE', 'fast'))


@pytest.fixture(autouse=True)
def flask(request):
    app = Flask(__name__)
    ctx = app.test_request_context('/')
    ctx.push()

    request.addfinalizer(ctx.pop)
