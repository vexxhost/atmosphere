import pydantic
from hypothesis import given
from hypothesis import strategies as st

from atmosphere.operator.api import types


class TestHostname:
    def test_modify_schema(self):
        class FakeObj(pydantic.BaseModel):
            hostname: types.Hostname

        assert FakeObj.schema().get("properties").get("hostname").get("examples") == [
            "example.com"
        ]

    def test_repr(self):
        assert repr(types.Hostname("example.com")) == "Hostname('example.com')"


class TestObjectMeta:
    @given(st.builds(types.ObjectMeta))
    def test_property(self, instance):
        assert isinstance(instance, types.ObjectMeta)
        assert isinstance(instance.name, str)
        assert instance.name != ""
        assert isinstance(instance.namespace, str)
        assert instance.namespace != ""


class TestKubernetesObject:
    @given(st.builds(types.KubernetesObject))
    def test_property(self, instance):
        assert isinstance(instance, types.KubernetesObject)
        assert isinstance(instance.metadata, types.ObjectMeta)


class TestServiceBackendPort:
    @given(st.builds(types.ServiceBackendPort))
    def test_property(self, instance):
        assert isinstance(instance, types.ServiceBackendPort)
        assert isinstance(instance.number, int)
        assert 1 <= instance.number <= 65535


class TestIngressServiceBackend:
    @given(st.builds(types.IngressServiceBackend))
    def test_property(self, instance):
        assert isinstance(instance, types.IngressServiceBackend)
        assert isinstance(instance.name, str)
        assert instance.name != ""
        assert isinstance(instance.port, types.ServiceBackendPort)


class TestOpenstackHelmRabbitmqClusterSpec:
    @given(st.builds(types.OpenstackHelmRabbitmqClusterSpec))
    def test_property(self, instance):
        assert isinstance(instance, types.OpenstackHelmRabbitmqClusterSpec)
        assert isinstance(instance.image, str)
        assert instance.image != ""


class TestOpenstackHelmIngressObjectMetaName:
    def test_name_order(self):
        assert [*types.OpenstackHelmIngressObjectMetaName] == sorted(
            [*types.OpenstackHelmIngressObjectMetaName]
        )


class TestOpenstackHelmIngressObjectMeta:
    @given(st.builds(types.OpenstackHelmIngressObjectMeta))
    def test_property(self, instance):
        assert isinstance(instance, types.OpenstackHelmIngressObjectMeta)
        assert isinstance(instance.name, types.OpenstackHelmIngressObjectMetaName)


class TestOpenstackHelmIngressSpec:
    @given(st.builds(types.OpenstackHelmIngressSpec))
    def test_property(self, instance):
        assert isinstance(instance, types.OpenstackHelmIngressSpec)
        assert instance.clusterIssuer != ""
        assert instance.ingressClassName != ""
        assert instance.host != ""
