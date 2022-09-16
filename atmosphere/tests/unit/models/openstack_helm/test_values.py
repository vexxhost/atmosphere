import pytest
import pykube

from atmosphere.models import conf
from atmosphere.models.openstack_helm import values as osh_values


class TestMemcachedValues:
    def test_values_for_chart(self):
        data = conf.AtmosphereConfig.get_mock_object()
        data.memcached.secret_key = "foobar"

        values = osh_values.Values.for_chart("memcached", data)

        assert {
            "endpoints": {"oslo_cache": {"auth": {"memcache_secret_key": "foobar"}}},
            "images": {
                "pull_policy": "Always",
                "tags": {
                    "memcached": data.memcached.images.memcached,
                    "prometheus_memcached_exporter": data.memcached.images.prometheus_memcached_exporter,
                },
            },
            "monitoring": {
                "prometheus": {
                    "enabled": True,
                }
            },
        } == values.to_primitive()

    def test_apply_for_chart_with_no_existing_config(self, mocker):
        data = conf.AtmosphereConfig.get_mock_object()
        data.memcached.secret_key = "foobar"

        values = osh_values.Values.for_chart("memcached", data)

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
        mocked_secret.update.assert_not_called()

    def test_apply_for_chart_with_no_config_change(self, mocker):
        data = conf.AtmosphereConfig.get_mock_object()
        data.memcached.secret_key = "foobar"

        values = osh_values.Values.for_chart("memcached", data)

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
        mocked_secret.update.assert_not_called()

    def test_apply_for_chart_with_config_change(self, mocker):
        data = conf.AtmosphereConfig.get_mock_object()
        data.memcached.secret_key = "foobar"

        old_values = osh_values.Values.for_chart("memcached", data)

        data.memcached.secret_key = "barfoo"
        new_values = osh_values.Values.for_chart("memcached", data)

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
        mocked_secret.update.assert_called_once()

    def test_apply_for_chart_with_unknown_failure(self, mocker):
        data = conf.AtmosphereConfig.get_mock_object()
        data.memcached.secret_key = "foobar"

        values = osh_values.Values.for_chart("memcached", data)

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
