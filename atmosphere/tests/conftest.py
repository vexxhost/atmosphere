import pytest


@pytest.fixture
def pykube(mocker):
    mocked_api = mocker.MagicMock()
    mocker.patch("atmosphere.clients.get_pykube_api", return_value=mocked_api)
    return mocked_api
