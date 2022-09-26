from atmosphere.models.openstack_helm import values
from atmosphere.tasks.kubernetes import flux, v1


class ApplyReleaseSecretTask(v1.ApplySecretTask):
    def __init__(self, namespace: str, chart: str, *args, **kwargs):
        super().__init__(
            namespace,
            f"atmosphere-{chart}",
            values.Values.for_chart(chart).secret_data,
            *args,
            **kwargs,
        )


class ApplyHelmReleaseTask(flux.ApplyHelmReleaseTask):
    def __init__(
        self,
        namespace: str,
        name: str,
        repository: str,
        version: str,
    ):
        super().__init__(
            namespace=namespace,
            name=name,
            repository=repository,
            chart=name,
            version=version,
            values_from=[
                {
                    "kind": "Secret",
                    "name": f"atmosphere-{name}",
                }
            ],
            requires=set([f"secret-{namespace}-atmosphere-{name}"]),
        )
