{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  coverage,
  hacking,
  oslotest,
  stestr,
  testtools,
}:

buildPythonApplication rec {
  pname = "os-resource-classes";
  version = "1.1.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "os-resource-classes";
    rev = version;
    hash = "sha256-JaV33YiP94RmsTb4nK2OnxVoMWfRBxoO4HfV24Uydog=";
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
    testtools
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "A library containing standardized resource class names in the Placement service.";
    homepage = "https://opendev.org/openstack/os-resource-classes";
    license = licenses.asl20;
  };
}
