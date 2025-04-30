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
        packagesOverlay = final: prev: {
          openstack-placement = prev.python3Packages.callPackage ./pkgs/openstack-placement { };

          pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
            (python-final: python-prev: {
              etcd3gw = python-final.callPackage ./pkgs/etcd3gw { };
              futurist = python-final.callPackage ./pkgs/futurist { };
              gabbi = python-final.callPackage ./pkgs/gabbi { };
              jsonpath-rw-ext = python-final.callPackage ./pkgs/jsonpath-rw-ext { };
              keystonemiddleware = python-final.callPackage ./pkgs/keystonemiddleware { };
              microversion-parse = python-final.callPackage ./pkgs/microversion-parse { };
              os-resource-classes = python-final.callPackage ./pkgs/os-resource-classes { };
              os-traits = python-final.callPackage ./pkgs/os-traits { };
              oslo-cache = python-final.callPackage ./pkgs/oslo-cache { };
              oslo-messaging = python-final.callPackage ./pkgs/oslo-messaging { };
              oslo-metrics = python-final.callPackage ./pkgs/oslo-metrics { };
              oslo-middleware = python-final.callPackage ./pkgs/oslo-middleware { };
              oslo-policy = python-final.callPackage ./pkgs/oslo-policy { };
              oslo-service = python-final.callPackage ./pkgs/oslo-service { };
              oslo-upgradecheck = python-final.callPackage ./pkgs/oslo-upgradecheck { };
              pycadf = python-final.callPackage ./pkgs/pycadf { };
              python-binary-memcached = python-final.callPackage ./pkgs/python-binary-memcached { };
              uhashring = python-final.callPackage ./pkgs/uhashring { };
            })
          ];
        };

        pkgs = import nixpkgs {
          inherit system;
          overlays = [ packagesOverlay ];
        };
      in
      {
        formatter = pkgs.nixfmt-rfc-style;

        packages = {
          openstack-placement = pkgs.openstack-placement;
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
