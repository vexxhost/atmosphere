{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  packages = with pkgs; [
    pkgs.earthly
    pkgs.poetry
  ];
}
