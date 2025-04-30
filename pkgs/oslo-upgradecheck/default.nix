{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  oslo-config,
  oslo-i18n,
  oslo-policy,
  oslo-utils,
  prettytable,
  oslo-serialization,
  oslotest,
  stestr,
}:

buildPythonApplication rec {
  pname = "oslo-upgradecheck";
  version = "2.5.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.upgradecheck";
    rev = version;
    hash = "sha256-HYvt/AGP3QGFB4pds4ml5W8gYyO8O87nwAOBkuaNKos=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    oslo-config
    oslo-i18n
    oslo-policy
    oslo-utils
    prettytable
  ];

  nativeCheckInputs = [
    oslo-serialization
    oslotest
    stestr
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "Common code for writing OpenStack upgrade checks.";
    homepage = "https://opendev.org/openstack/oslo.upgradecheck";
    license = licenses.asl20;
  };
}
