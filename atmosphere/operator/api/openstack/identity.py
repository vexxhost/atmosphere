import kopf
import pykube


class OpenStackNamespacedAPIObject(pykube.objects.NamespacedAPIObject):
    @classmethod
    def get(cls, api, namespace, name):
        resource = cls.objects(api, namespace=namespace).get_or_none(name=name)
        if resource is None or resource.obj["status"].get("id") is None:
            raise kopf.TemporaryError(f"{cls.kind}/{name} is not yet ready.", delay=5)
        return resource

    @property
    def id(self):
        return self.obj["status"]["id"]


class Endpoint(OpenStackNamespacedAPIObject):
    version = "identity.openstack.atmosphere.vexxhost.com/v1alpha1"
    endpoint = "endpoints"
    kind = "Endpoint"


class ImpliedRole(OpenStackNamespacedAPIObject):
    version = "identity.openstack.atmosphere.vexxhost.com/v1alpha1"
    endpoint = "impliedroles"
    kind = "ImpliedRole"


class Role(OpenStackNamespacedAPIObject):
    version = "identity.openstack.atmosphere.vexxhost.com/v1alpha1"
    endpoint = "roles"
    kind = "Role"


class Service(OpenStackNamespacedAPIObject):
    version = "identity.openstack.atmosphere.vexxhost.com/v1alpha1"
    endpoint = "services"
    kind = "Service"
