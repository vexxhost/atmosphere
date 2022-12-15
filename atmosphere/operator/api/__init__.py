import pykube


class Cloud(pykube.objects.NamespacedAPIObject):
    version = "atmosphere.vexxhost.com/v1alpha1"
    endpoint = "clouds"
    kind = "Cloud"
