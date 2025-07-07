{
  description = "EasyBuild shell with virtualenv setup inside Nix flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python3;
        venvDir = ".venv";
      in {
        devShells.default = pkgs.mkShell {
          name = "easybuild-env";

          buildInputs = [
            python
            python.pkgs.pip
            pkgs.gcc
            pkgs.git
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

            if [ ! -d "${venvDir}" ]; then
              echo "🐍 Creating Python virtual environment in ${venvDir}"
              python -m venv ${venvDir}
            fi

            source ${venvDir}/bin/activate

            if ! command -v eb >/dev/null; then
              echo "🔧 Installing EasyBuild into virtualenv..."
              pip install --quiet --upgrade pip setuptools wheel
              pip install --quiet easybuild
            fi

            echo "✅ EasyBuild version: $(eb --version)"
          '';
        };
      });
}

