{
  lib,
  buildPythonApplication,
  fetchFromGitHub,
  pbr,
  jsonpath-rw,
}:

buildPythonApplication rec {
  pname = "jsonpath-rw-ext";
  version = "1.2.2";

  src = fetchFromGitHub {
    owner = "sileht";
    repo = "python-jsonpath-rw-ext";
    rev = version;
    hash = "sha256-kvFHRGWTOK6HJK3NCDq7bYLkMMdK2L3CXLv0hgEpElg=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    jsonpath-rw
  ];

  meta = with lib; {
    description = "Extensions for JSONPath RW";
    homepage = "https://github.com/sileht/python-jsonpath-rw-ext";
    license = licenses.asl20;
  };
}
