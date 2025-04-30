{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  debtcollector,
  eventlet,
  coverage,
  python-subunit,
  oslotest,
  stestr,
  testscenarios,
  testtools,
  prettytable,
}:

buildPythonApplication rec {
  pname = "futurist";
  version = "3.1.1";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "futurist";
    rev = version;
    hash = "sha256-qFI3q1zOGdw9tK52ZDWuuI9afEXr54jRLceoMJss4vo=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    debtcollector
  ];

  nativeCheckInputs = [
    eventlet
    coverage
    python-subunit
    oslotest
    stestr
    testscenarios
    testtools
    prettytable
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "A collection of async functionality and additions from the future.";
    homepage = "https://opendev.org/openstack/futurist";
    license = licenses.asl20;
  };
}
