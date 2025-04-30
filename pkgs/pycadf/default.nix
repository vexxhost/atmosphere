{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  oslo-config,
  oslo-serialization,
  coverage,
  fixtures,
  flake8-import-order,
  hacking,
  python-subunit,
  stestr,
  testtools,
}:

buildPythonApplication rec {
  pname = "pycadf";
  version = "4.0.1";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "pycadf";
    rev = version;
    hash = "sha256-jIpjOADfZmEX8ev3oBN8FiH41The/8X6SC5WetuLRMo=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    oslo-config
    oslo-serialization
  ];

  nativeCheckInputs = [
    coverage
    fixtures
    flake8-import-order
    hacking
    python-subunit
    stestr
    testtools
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "CADF Python module";
    homepage = "https://opendev.org/openstack/pycadf";
    license = licenses.asl20;
  };
}
