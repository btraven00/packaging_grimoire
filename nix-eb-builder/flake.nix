{
  description = "Reproducible EasyBuild builder shell with Nix + pip-installed EasyBuild";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";  # Adjust to your preferred channel
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pip
          setuptools
          wheel
        ]);
      in {
        devShells.default = pkgs.mkShell {
          name = "easybuild-env";

          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.gcc
            pkgs.curl
            pkgs.openssl
            pkgs.zlib
            pkgs.libffi
            pkgs.libxml2
            pkgs.libxslt
            pkgs.autoconf
            pkgs.automake
            pkgs.pkg-config
            pkgs.which
          ];

          shellHook = ''
            export LC_ALL=C.UTF-8
            export LANG=C.UTF-8
            export PATH=$HOME/.local/bin:$PATH

            if ! command -v eb >/dev/null; then
              echo "🔧 Installing EasyBuild (user-level pip)..."
              pip install --quiet --user easybuild
            fi

            echo "✅ EasyBuild is ready:"
            echo "   eb --version => $(eb --version 2>/dev/null || echo 'not found')"
          '';
        };
      });
}
