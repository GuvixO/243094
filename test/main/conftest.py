import pytest
from datetime import datetime


@pytest.fixture(scope='session', autouse=True)
def record_time():
    pytest.start_time = datetime.now()
    yield
    pytest.finish_time = datetime.now()