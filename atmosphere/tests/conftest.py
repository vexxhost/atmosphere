import pathlib
import subprocess

import pytest
import requests


@pytest.fixture
def pykube(mocker):
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
