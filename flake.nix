{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pythonPackagesOverlay = final: prev: {
          pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
            (python-final: python-prev: {
              etcd3gw = pkgs.python3Packages.callPackage ./pkgs/etcd3gw { };
              futurist = python-final.callPackage ./pkgs/futurist { };
              gabbi = pkgs.python3Packages.callPackage ./pkgs/gabbi { };
              jsonpath-rw-ext = pkgs.python3Packages.callPackage ./pkgs/jsonpath-rw-ext { };
              keystonemiddleware = pkgs.python3Packages.callPackage ./pkgs/keystonemiddleware { };
              microversion-parse = pkgs.python3Packages.callPackage ./pkgs/microversion-parse { };
              oslo-cache = pkgs.python3Packages.callPackage ./pkgs/oslo-cache { };
              oslo-messaging = pkgs.python3Packages.callPackage ./pkgs/oslo-messaging { };
              oslo-metrics = pkgs.python3Packages.callPackage ./pkgs/oslo-metrics { };
              oslo-middleware = pkgs.python3Packages.callPackage ./pkgs/oslo-middleware { };
              oslo-service = pkgs.python3Packages.callPackage ./pkgs/oslo-service { };
              pycadf = pkgs.python3Packages.callPackage ./pkgs/pycadf { };
              python-binary-memcached = pkgs.python3Packages.callPackage ./pkgs/python-binary-memcached { };
              uhashring = pkgs.python3Packages.callPackage ./pkgs/uhashring { };
            })
          ];
        };

        pkgs = import nixpkgs {
          inherit system;
          overlays = [ pythonPackagesOverlay ];
        };
      in
      {
        formatter = pkgs.nixfmt-rfc-style;

        packages = {
          openstack-placement = pkgs.python3Packages.callPackage ./pkgs/openstack-placement { };
        };

        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            bashInteractive
            docutils
            earthly
            gh
            glibcLocales
            go
            just
            kubernetes-helm
            nixpkgs-fmt
            patchutils
            python311Packages.tox
            reno
            renovate
            uv
            vale
          ];
        };
      }
    );
}
