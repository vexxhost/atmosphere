import pykube


def get_pykube_api(timeout=None) -> pykube.HTTPClient:
    return pykube.HTTPClient(pykube.KubeConfig.from_env(), timeout=timeout)
