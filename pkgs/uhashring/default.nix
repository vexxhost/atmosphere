{
  lib,
  buildPythonApplication,
  fetchFromGitHub,
  hatchling,
  pytestCheckHook,
  python-memcached
}:

buildPythonApplication rec {
  pname = "uhashring";
  version = "2.4";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "ultrabug";
    repo = "uhashring";
    rev = version;
    hash = "sha256-6zNPExbcwTUne0lT8V6xp2Gf6J1VgG7Q93qizVOAc+k=";
  };

  build-system = [
    hatchling
  ];

  nativeCheckInputs = [
    pytestCheckHook
    python-memcached
  ];

  meta = with lib; {
    description = "Full featured consistent hashing python library compatible with ketama";
    homepage = "https://github.com/ultrabug/uhashring";
    license = licenses.bsd3;
  };
}
