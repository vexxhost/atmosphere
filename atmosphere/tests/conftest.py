import pytest
import responses


@pytest.fixture
def kubeconfig(tmpdir):
    kubeconfig = tmpdir.join("kubeconfig")
    kubeconfig.write(
        """
apiVersion: v1
clusters:
- cluster: {server: 'https://localhost:9443'}
  name: test
contexts:
- context: {cluster: test, user: test}
  name: test
current-context: test
kind: Config
preferences: {}
users:
- name: test
  user: {token: testtoken}
    """
    )
    return kubeconfig


@pytest.fixture
def requests_mock():
    return responses.RequestsMock(target="pykube.http.KubernetesHTTPAdapter._do_send")


@pytest.fixture
def api(kubeconfig):
    import pykube

    config = pykube.KubeConfig.from_file(str(kubeconfig))
    return pykube.HTTPClient(config)


@pytest.fixture
def pykube(mocker):
    # TODO(mnaser): We should get rid of this fixture and rename the other one
    #               to pykube.
    mocked_api = mocker.MagicMock()
    mocker.patch("atmosphere.clients.get_pykube_api", return_value=mocked_api)
    return mocked_api
