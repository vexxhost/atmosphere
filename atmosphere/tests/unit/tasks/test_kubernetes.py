import pykube
import pytest

from atmosphere.tasks import kubernetes


class TestExecuteSecretTask:
    def test_with_no_existing_secret(self, mocker):
        task = kubernetes.EnsureSecretTask()

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = {"data": {"values.yaml": "foo"}}
        mocked_secret.exists.return_value = False

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        task.execute("openstack", "atmosphere-keystone", mocked_secret.obj["data"])

        mocked_secret.exists.assert_called_once()
        mocked_secret.create.assert_called_once()
        mocked_secret.reload.assert_called_once()
        mocked_secret.update.assert_not_called()

    def test_with_no_changes(self, mocker):
        task = kubernetes.EnsureSecretTask()

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = {"data": {"values.yaml": "foo"}}
        mocked_secret.exists.return_value = True

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        task.execute("openstack", "atmosphere-keystone", mocked_secret.obj["data"])

        mocked_secret.exists.assert_called_once()
        mocked_secret.create.assert_not_called()
        mocked_secret.reload.assert_called_once()
        mocked_secret.update.assert_not_called()

    def test_with_changes(self, mocker):
        task = kubernetes.EnsureSecretTask()

        old_values = {"data": {"values.yaml": "foo"}}
        new_values = {"data": {"values.yaml": "bar"}}

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = old_values
        mocked_secret.exists.return_value = True

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        task.execute("openstack", "atmosphere-keystone", new_values)

        mocked_secret.exists.assert_called_once()
        mocked_secret.create.assert_not_called()
        mocked_secret.reload.assert_called_once()
        mocked_secret.update.assert_called_once()

    def test_with_unknown_error(self, mocker):
        task = kubernetes.EnsureSecretTask()

        mocked_secret = mocker.MagicMock()
        mocked_secret.obj = {"data": {"values.yaml": "foo"}}
        mocked_secret.exists.side_effect = pykube.exceptions.KubernetesError

        mocked_secret_class = mocker.patch("pykube.Secret")
        mocked_secret_class.return_value = mocked_secret

        with pytest.raises(pykube.exceptions.KubernetesError):
            task.execute("openstack", "atmosphere-keystone", mocked_secret.obj["data"])

        mocked_secret.exists.assert_called_once()
