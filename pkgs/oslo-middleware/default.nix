{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  bcrypt,
  debtcollector,
  jinja2,
  oslo-config,
  oslo-context,
  oslo-i18n,
  oslo-utils,
  statsd,
  stevedore,
  webob,
  coverage,
  fixtures,
  oslo-serialization,
  oslotest,
  stestr,
  testtools,
}:

buildPythonApplication rec {
  pname = "oslo-middleware";
  version = "6.4.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.middleware";
    rev = version;
    hash = "sha256-zOPa1UhB8ChS5EqHUCeOUmYGRKql6xJXmH8FEkdGEII=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    bcrypt
    debtcollector
    jinja2
    oslo-config
    oslo-context
    oslo-i18n
    oslo-utils
    statsd
    webob
  ];

  nativeCheckInputs = [
    coverage
    fixtures
    oslo-serialization
    oslotest
    stestr
    testtools
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "OpenStack middleware library";
    homepage = "https://opendev.org/openstack/oslo.middleware";
    license = licenses.asl20;
  };
}
