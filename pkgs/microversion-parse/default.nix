{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  webob,
  coverage,
  gabbi,
  hacking,
  pre-commit,
  stestr,
  testtools,
}:

buildPythonApplication rec {
  pname = "microversion-parse";
  version = "2.0.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "microversion-parse";
    rev = version;
    hash = "sha256-evwoYR0YVTEEhkXucEYMQPSXqjPFNYtmA7fjwIzhFqk=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    webob
  ];

  nativeCheckInputs = [
    coverage
    gabbi
    hacking
    pre-commit
    stestr
    testtools
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "Simple library for parsing OpenStack microversion headers.";
    homepage = "https://opendev.org/openstack/microversion-parse";
    license = licenses.asl20;
  };
}
