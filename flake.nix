{
  description = "Hísilómë - the Zola site and the radio station behind hisilo.me";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {nixpkgs, ...}: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    inherit (pkgs) lib;
    hisilome = import ./nix/packages.nix pkgs;
  in {
    # Not derivations; `nix flake check` would reject them.
    packages.${system} =
      lib.filterAttrs (_: lib.isDerivation) (removeAttrs hisilome ["devNginxConf" "site-html-check" "pwPython"])
      // {default = hisilome.site;};

    # `nix flake check`: the site builds and validates. Guards the push (lefthook.yml).
    checks.${system}.html = hisilome.site-html-check;

    # Consumer's pkgs, not this flake's nixpkgs: the host never mixes two.
    nixosModules.default = import ./nix/modules/default.nix;

    # Browser tests against the running dev stack; needs the stack, so an app, not a check.
    apps.${system}.e2e = {
      type = "app";
      program = "${hisilome.e2e}/bin/e2e";
    };

    devShells.${system} = {
      default = import ./nix/devshell.nix pkgs hisilome;
      # ~1 GB of browsers: kept out of the default shell on purpose.
      e2e = pkgs.mkShellNoCC {
        name = "hisilome-e2e";
        packages = [hisilome.pwPython pkgs.ruff hisilome.e2e];
        shellHook =
          hisilome.e2eEnv
          + ''
            echo "e2e [pytest args]      browser tests against E2E_BASE (default http://127.0.0.1:8099; start the stack from the default shell first)"
            echo "pytest tests/e2e -k x  the same, by hand"
          '';
      };
    };
  };
}
