{
  description = "Nix Packages collection for Atmosphere";

  inputs = {
    nixpkgs.url = "github:/nixos/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pkgs-by-name-for-flake-parts.url = "github:drupol/pkgs-by-name-for-flake-parts";
    nix2container.url = "github:nlewo/nix2container";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } (
      { withSystem, ... }:
      {
        systems = import inputs.systems;

        imports = [
          inputs.pkgs-by-name-for-flake-parts.flakeModule
        ];

        perSystem =
          {
            config,
            system,
            pkgs,
            ...
          }:
          let
            mkImage =
              args:
              let
                image = inputs.nix2container.packages.${system}.nix2container.buildImage args;
              in
              image
              // {
                copyToRegistryWithMetadataTags = pkgs.writeShellScriptBin "copy-docker-image" ''
                  IFS=$'\n'
                  set -x
                  for DOCKER_TAG in $DOCKER_METADATA_OUTPUT_TAGS; do
                    ${pkgs.lib.getExe image.copyTo} "docker://$DOCKER_TAG"
                  done
                '';
              };
          in
          {
            formatter = pkgs.nixfmt-rfc-style;

            # Load local packages into `nixpkgs`
            _module.args.pkgs = import inputs.nixpkgs {
              inherit system;
              overlays = [
                inputs.self.overlays.default
              ];
            };
            pkgsDirectory = ./pkgs/by-name;

            # Images
            packages =
              let
                imageDefinitions = {
                  capoControllerManagerImage = mkImage {
                    name = "ghcr.io/vexxhost/atmosphere/capo-controller-manager";
                    maxLayers = 64;

                    copyToRoot = with pkgs.dockerTools; [
                      caCertificates
                    ];

                    config = {
                      Entrypoint = [ (pkgs.lib.getExe config.packages.cluster-api-provider-openstack) ];
                    };
                  };

                  # More images here...
                };

                # Get a sample image to extract attributes (assuming all images have the same attributes)
                sampleImage = builtins.head (builtins.attrValues imageDefinitions);

                # Get all attributes that are derivations/executables (like copyToDockerDaemon, copyToRegistryWithMetadataTags)
                executableAttrs = builtins.filter (
                  attr:
                  builtins.hasAttr attr sampleImage
                  && builtins.isAttrs (builtins.getAttr attr sampleImage)
                  && builtins.hasAttr "type" (builtins.getAttr attr sampleImage)
                  && (builtins.getAttr attr sampleImage).type == "derivation"
                ) (builtins.attrNames sampleImage);

                # Create a function to generate a script that runs a specific attribute across all images
                makeParallelScript =
                  attrName:
                  pkgs.writeShellScriptBin "parallel-${attrName}" ''
                    #!/usr/bin/env bash
                    set -euo pipefail

                    ${builtins.concatStringsSep "\n" (
                      builtins.attrValues (
                        builtins.mapAttrs (
                          imageName: image:
                          let
                            attr = builtins.getAttr attrName image;
                          in
                          ''
                            echo "Running ${attrName} for image: ${imageName}"
                            ${pkgs.lib.getExe attr}
                          ''
                        ) imageDefinitions
                      )
                    )}

                    echo "Completed ${attrName} for all images successfully!"
                  '';

                # Generate parallel scripts for all executable attributes
                parallelScripts = builtins.listToAttrs (
                  map (attrName: {
                    name = attrName;
                    value = makeParallelScript attrName;
                  }) executableAttrs
                );

                # Create the linkfarm with all images
                imageLinkFarm = pkgs.linkFarm "atmosphere-images" (
                  builtins.attrValues (
                    builtins.mapAttrs (name: image: {
                      inherit name;
                      path = image;
                    }) imageDefinitions
                  )
                );
              in
              imageDefinitions
              // {
                # Expose the images linkfarm with all the parallel script capabilities
                images = imageLinkFarm // parallelScripts;
              };

            devShells.default = pkgs.mkShell {
              LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
              RUST_SRC_PATH = pkgs.rust.packages.stable.rustPlatform.rustLibSrc;

              buildInputs = with pkgs; [
                cargo
                clippy
                docutils
                gh
                go
                kubernetes-helm
                patchutils
                pre-commit
                python311Packages.tox
                reno
                renovate
                rust-analyzer
                rustc
                rustfmt
                uv
                vale
              ];
            };
          };

        flake = {
          # Expose package out of the Flake
          overlays.default =
            final: prev:
            withSystem prev.stdenv.hostPlatform.system (
              { config, ... }:
              {
                local = config.packages;
              }
            );
        };
      }
    );
}
