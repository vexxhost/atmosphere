from taskflow import task

from atmosphere.models.openstack_helm import values


class GenerateReleaseSecretTask(task.Task):
    default_provides = ("secret_namespace", "secret_name", "secret_data")

    def execute(self, chart, *args, **kwargs):
        secret_name = f"atmosphere-{chart}"
        secret_data = values.Values.for_chart(chart).secret_data

        return "openstack", secret_name, secret_data
