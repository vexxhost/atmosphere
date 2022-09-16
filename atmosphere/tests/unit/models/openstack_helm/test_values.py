import confspirator
import pykube
import pytest

from atmosphere.config import CONF
from atmosphere.models.openstack_helm import values as osh_values


class TestMemcachedValues:
    def test_values_for_chart(self):
        values = osh_values.Values.for_chart("memcached")

        assert {
            "endpoints": {
                "oslo_cache": {
                    "auth": {"memcache_secret_key": CONF.memcached.secret_key}
                }
            },
            "images": {
                "pull_policy": "Always",
                "tags": {
                    "memcached": CONF.images.memcached,
                    "prometheus_memcached_exporter": CONF.images.memcached_exporter,
                },
            },
            "monitoring": {
                "prometheus": {
                    "enabled": True,
                }
            },
        } == values.to_primitive()

    def test_apply_for_chart_with_no_existing_config(self, mocker):
        values = osh_values.Values.for_chart("memcached")

        api = mocker.MagicMock()

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = values.secret()
        mocked_secret.exists.return_value = False

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        values.apply(api)

        mocked_secret_class.assert_called_once_with(api, values.secret())
        mocked_secret.exists.assert_called_once()
        mocked_secret.create.assert_called_once()
        mocked_secret.reload.assert_called_once()
        mocked_secret.update.assert_not_called()

    def test_apply_for_chart_with_no_config_change(self, mocker):
        values = osh_values.Values.for_chart("memcached")

        api = mocker.MagicMock()

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = values.secret()
        mocked_secret.exists.return_value = True

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        values.apply(api)

        mocked_secret_class.assert_called_once_with(api, values.secret())
        mocked_secret.exists.assert_called_once()
        mocked_secret.create.assert_not_called()
        mocked_secret.reload.assert_called_once()
        mocked_secret.update.assert_not_called()

    def test_apply_for_chart_with_config_change(self, mocker):
        old_values = osh_values.Values.for_chart("memcached")

        with confspirator.modify_conf(
            CONF,
            {
                "atmosphere.memcached.secret_key": [
                    {"operation": "override", "value": "barfoo"}
                ],
            },
        ):
            new_values = osh_values.Values.for_chart("memcached")

        api = mocker.MagicMock()

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = old_values.secret()
        mocked_secret.exists.return_value = True

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        new_values.apply(api)

        mocked_secret_class.assert_called_once_with(api, new_values.secret())
        mocked_secret.exists.assert_called_once()
        mocked_secret.create.assert_not_called()
        mocked_secret.reload.assert_called_once()
        mocked_secret.update.assert_called_once()

    def test_apply_for_chart_with_unknown_failure(self, mocker):
        values = osh_values.Values.for_chart("memcached")

        api = mocker.MagicMock()
        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = values.secret()
        mocked_secret.exists.side_effect = pykube.exceptions.KubernetesError

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        with pytest.raises(pykube.exceptions.KubernetesError):
            values.apply(api)

        mocked_secret_class.assert_called_once_with(api, values.secret())
        mocked_secret.exists.assert_called_once()
