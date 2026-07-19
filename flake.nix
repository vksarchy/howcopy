{
  description = "howcopy — OPERATION HOW COPY: tactical radio comms drill for everyday life";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        # anthropic's check phase pulls inline-snapshot, currently broken in
        # nixpkgs-unstable (3 failing tests). Runtime is unaffected.
        anthropic = python.pkgs.anthropic.overridePythonAttrs (_: {
          doCheck = false;
        });
        howcopy = python.pkgs.buildPythonApplication {
          pname = "howcopy";
          version = "0.1.0";
          pyproject = true;
          src = ./.;
          build-system = [ python.pkgs.setuptools ];
          dependencies = [ anthropic ];
          # No network at build time; runtime backends are auto-detected.
          doCheck = false;
          meta = {
            description = "Terminal drill: translate daily life into tactical radio comms, graded by an LLM instructor";
            mainProgram = "howcopy";
            license = pkgs.lib.licenses.mit;
          };
        };
      in {
        packages.default = howcopy;
        apps.default = {
          type = "app";
          program = "${howcopy}/bin/howcopy";
        };
        devShells.default = pkgs.mkShell {
          packages = [ (python.withPackages (_: [ anthropic ])) ];
        };
      });
}
