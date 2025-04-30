{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    nix2container = {
      url = "github:nlewo/nix2container";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      nix2container,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        packagesOverlay = final: prev: {
          openstack-placement = prev.python3.pkgs.callPackage ./pkgs/openstack-placement { };

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

        nix2containerPkgs = nix2container.packages.${system};
        n2c = nix2containerPkgs.nix2container;

        uwsgi = pkgs.uwsgi.override({
          python3 = pkgs.python3;
          plugins = ["python3"];
        });
      in
      {
        formatter = pkgs.nixfmt-rfc-style;

        packages = {
          openstack-placement = n2c.buildImage {
            name = "ghcr.io/vexxhost/placement";
            maxLayers = 64;

            copyToRoot = [
              pkgs.dockerTools.caCertificates
              (pkgs.buildEnv {
                name = "root";
                paths = with pkgs; [ coreutils uwsgi openstack-placement ];
                pathsToLink = [ "/bin" "/etc" ];
              })
            ];
          };
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
