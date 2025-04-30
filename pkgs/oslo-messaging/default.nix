{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  amqp,
  cachetools,
  debtcollector,
  futurist,
  kombu,
  oslo-config,
  oslo-context,
  oslo-log,
  oslo-metrics,
  oslo-middleware,
  oslo-serialization,
  oslo-service,
  oslo-utils,
  pyyaml,
  stevedore,
  webob,
  confluent-kafka,
  coverage,
  eventlet,
  fixtures,
  greenlet,
  oslotest,
  pifpaf,
  stestr,
  testscenarios,
  testtools,
}:

buildPythonApplication rec {
  pname = "oslo-messaging";
  version = "16.1.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.messaging";
    rev = version;
    hash = "sha256-Jy44WDsZSW0TIaxxDelsXzp2zU4PKgQ0h2B/UQuLc+A=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    amqp
    cachetools
    debtcollector
    futurist
    kombu
    oslo-config
    oslo-context
    oslo-log
    oslo-metrics
    oslo-middleware
    oslo-serialization
    oslo-service
    oslo-utils
    pyyaml
    stevedore
    webob
  ];

  nativeCheckInputs = [
    confluent-kafka
    coverage
    eventlet
    fixtures
    greenlet
    oslotest
    pifpaf
    stestr
    testscenarios
    testtools
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "OpenStack library for messaging";
    homepage = "https://opendev.org/openstack/oslo.messaging";
    license = licenses.asl20;
  };
}
