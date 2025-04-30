{
  lib,
  pkgs,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  debtcollector,
  eventlet,
  greenlet,
  oslo-concurrency,
  oslo-config,
  oslo-i18n,
  oslo-log,
  oslo-utils,
  paste,
  pastedeploy,
  routes,
  webob,
  yappi,
  coverage,
  fixtures,
  oslotest,
  requests,
  stestr,
}:

buildPythonApplication rec {
  pname = "oslo-service";
  version = "4.1.1";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.service";
    rev = version;
    hash = "sha256-pLp/DzD0XXo2Knu0pSSvZOCtSWn/AEh0JY7IZ+w8/h8=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    debtcollector
    eventlet
    greenlet
    oslo-concurrency
    oslo-config
    oslo-i18n
    oslo-log
    oslo-utils
    paste
    pastedeploy
    routes
    webob
    yappi
  ];

  nativeCheckInputs = [
    pkgs.ps
    coverage
    fixtures
    oslotest
    requests
    stestr
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "OpenStack library for collecting metrics from Oslo libraries";
    homepage = "https://opendev.org/openstack/oslo.metrics";
    license = licenses.asl20;
  };
}
