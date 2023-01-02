import pathlib
import subprocess

import pytest
import requests
import responses

from atmosphere.models import config


@pytest.fixture
def sample_config():
    return config.Config(
        {
            "memcached": {
                "secret_key": "foobar",
            }
        }
    )


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


@pytest.fixture(scope="session")
def flux_cluster(kind_cluster):
    path = pathlib.Path(".pytest-flux")
    path.mkdir(parents=True, exist_ok=True)

    install_path = path / "install.sh"
    flux_path = path / "flux"

    if not install_path.exists():
        url = "https://fluxcd.io/install.sh"
        tmp_file = install_path.with_suffix(".tmp")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with tmp_file.open("wb") as fd:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        fd.write(chunk)
        tmp_file.chmod(0o755)
        tmp_file.rename(install_path)

    if not flux_path.exists():
        subprocess.check_output(
            ["bash", install_path, path],
            encoding="utf-8",
        )

    assert flux_path.exists() is True

    subprocess.check_output(
        [flux_path, "install"],
        env={"KUBECONFIG": str(kind_cluster.kubeconfig_path)},
        encoding="utf-8",
    )

    return kind_cluster
