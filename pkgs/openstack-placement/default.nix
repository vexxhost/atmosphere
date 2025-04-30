{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  jsonschema,
  keystonemiddleware,
  microversion-parse,
  os-resource-classes,
  os-traits,
  oslo-concurrency,
  oslo-config,
  oslo-context,
  oslo-db,
  oslo-log,
  oslo-middleware,
  oslo-policy,
  oslo-serialization,
  oslo-upgradecheck,
  oslo-utils,
  requests,
  routes,
  sqlalchemy,
  webob,
  bandit,
  coverage,
  cryptography,
  fixtures,
  gabbi,
  hacking,
  oslotest,
  osprofiler,
  psycopg2,
  pymysql,
  stestr,
  testtools,
  wsgi-intercept,
}:

buildPythonApplication rec {
  pname = "openstack-placement";
  version = "13.0.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "placement";
    rev = version;
    hash = "sha256-N9zbXIIWLIgDs+fnN0zc1NUcE3JpAjYHdZBxats1W2I=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    jsonschema
    keystonemiddleware
    microversion-parse
    os-resource-classes
    os-traits
    oslo-concurrency
    oslo-config
    oslo-context
    oslo-db
    oslo-log
    oslo-middleware
    oslo-policy
    oslo-serialization
    oslo-upgradecheck
    oslo-utils
    requests
    routes
    sqlalchemy
    webob
  ];

  nativeCheckInputs = [
    bandit
    coverage
    cryptography
    fixtures
    gabbi
    hacking
    oslotest
    osprofiler
    psycopg2
    pymysql
    stestr
    testtools
    wsgi-intercept
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "OpenStack resource provider inventory allocation service";
    homepage = "https://opendev.org/openstack/placement";
    license = licenses.asl20;
    teams = [ teams.openstack ];
  };
}
