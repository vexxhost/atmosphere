{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  coverage,
  hacking,
  oslotest,
  stestr,
  testscenarios,
  testtools,
}:

buildPythonApplication rec {
  pname = "os-traits";
  version = "3.4.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "os-traits";
    rev = version;
    hash = "sha256-+8lFutUCPzmLLXliC106bgdnPR4djdQDCGsfEQr9nUU=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  nativeCheckInputs = [
    coverage
    hacking
    oslotest
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
    description = "A library containing standardized trait strings. Used by placement service and clients to ensure consistency.";
    homepage = "https://opendev.org/openstack/os-traits";
    license = licenses.asl20;
  };
}
