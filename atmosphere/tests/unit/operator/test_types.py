from hypothesis import given
from hypothesis import provisional as prov
from hypothesis import strategies as st

from atmosphere.operator.api import types


class TestObjectMeta:
    @given(st.builds(types.ObjectMeta))
    def test_property(self, instance):
        assert isinstance(instance, types.ObjectMeta)
        assert isinstance(instance.name, str)
        assert instance.name != ""


class TestNamespacedObjectMeta:
    @given(st.builds(types.NamespacedObjectMeta))
    def test_property(self, instance):
        assert isinstance(instance, types.NamespacedObjectMeta)
        assert isinstance(instance.name, str)
        assert instance.name != ""
        assert isinstance(instance.namespace, str)
        assert instance.namespace != ""


class TestKubernetesObject:
    @given(st.builds(types.KubernetesObject))
    def test_property(self, instance):
        assert isinstance(instance, types.KubernetesObject)
        assert isinstance(instance.metadata, types.ObjectMeta)


class TestNamespacedKubernetesObject:
    @given(st.builds(types.NamespacedKubernetesObject))
    def test_property(self, instance):
        assert isinstance(instance, types.NamespacedKubernetesObject)
        assert isinstance(instance.metadata, types.NamespacedObjectMeta)


class TestCrossNamespaceObjectReference:
    @given(st.builds(types.CrossNamespaceObjectReference))
    def test_property(self, instance):
        assert isinstance(instance, types.CrossNamespaceObjectReference)
        assert isinstance(instance.kind, str)
        assert instance.kind != ""
        assert isinstance(instance.name, str)
        assert instance.name != ""
        assert isinstance(instance.namespace, str) or instance.namespace is None
        assert instance.namespace != ""


class TestHelmRepositorySpec:
    @given(st.builds(types.HelmRepositorySpec, url=prov.urls()))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmRepositorySpec)
        assert isinstance(instance.url, str)
        assert instance.url != ""
        assert isinstance(instance.interval, str)
        assert instance.interval != ""


class TestHelmChartTemplateSpec:
    @given(st.builds(types.HelmChartTemplateSpec))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmChartTemplateSpec)
        assert isinstance(instance.chart, str)
        assert instance.chart != ""
        assert isinstance(instance.version, str) or instance.version is None
        assert instance.version != ""


class TestHelmChartTemplate:
    @given(st.builds(types.HelmChartTemplate))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmChartTemplate)
        assert isinstance(instance.spec, types.HelmChartTemplateSpec)


class HelmReleaseActionRemediation:
    @given(st.builds(types.HelmReleaseActionRemediation))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmReleaseActionRemediation)
        assert isinstance(instance.retries, int)


class TestHelmReleaseActionSpec:
    @given(st.builds(types.HelmReleaseActionSpec))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmReleaseActionSpec)
        assert isinstance(instance.crds, types.HelmReleaseActionSpecCRDsPolicy)
        assert isinstance(instance.disable_wait, bool)
        assert instance.disable_wait in [True, False]
        assert isinstance(instance.remediation, types.HelmReleaseActionRemediation)


class TestHelmReleaseValuesReference:
    @given(st.builds(types.HelmReleaseValuesReference))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmReleaseValuesReference)
        assert isinstance(instance.kind, str)
        assert instance.kind != ""
        assert isinstance(instance.name, str)
        assert instance.name != ""
        assert isinstance(instance.values_key, str) or instance.values_key is None
        assert instance.values_key != ""
        assert isinstance(instance.target_path, str) or instance.target_path is None
        assert instance.target_path != ""


class TestHelmReleaseSpec:
    @given(st.builds(types.HelmReleaseSpec))
    def test_property(self, instance):
        assert isinstance(instance, types.HelmReleaseSpec)
        assert isinstance(instance.interval, str)
        assert instance.interval != ""
        assert isinstance(instance.chart, types.HelmChartTemplate)
        assert isinstance(instance.install, types.HelmReleaseActionSpec)
        assert isinstance(instance.upgrade, types.HelmReleaseActionSpec)
        assert isinstance(instance.values, dict)
        assert isinstance(instance.values_from, list)
