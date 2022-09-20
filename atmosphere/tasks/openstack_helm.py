from atmosphere.models.openstack_helm import values
from atmosphere.tasks import kubernetes


class CreateOrUpdateReleaseSecretTask(kubernetes.CreateOrUpdateSecretTask):
    def __init__(self, namespace: str, chart: str, *args, **kwargs):
        super().__init__(
            namespace,
            f"atmosphere-{chart}",
            values.Values.for_chart(chart).secret_data,
            *args,
            **kwargs,
        )
