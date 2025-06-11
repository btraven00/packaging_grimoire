#!/usr/bin/env python3
import sys
import subprocess
import json
import pkg_resources
from datetime import date

def get_python_packages():
    result = {}
    for dist in pkg_resources.working_set:
        metadata = dist.get_metadata_lines("METADATA") if dist.has_metadata("METADATA") else []
        meta = {line.split(": ", 1)[0].lower(): line.split(": ", 1)[1] for line in metadata if ": " in line}
        result[dist.project_name] = {
            "version": dist.version,
            "origin": meta.get("home-page", "unknown"),
            "date": meta.get("date", "unknown")
        }
    return result

def get_r_packages():
    r_script = r"""
    get_r_packages_info <- function() {
      info <- devtools::session_info()
      pkgs <- info$packages
      result <- list()

      for (i in seq_len(nrow(pkgs))) {
        pkg <- pkgs[i, ]
        name <- pkg$package
        version <- if (!is.na(pkg$loadedversion)) pkg$loadedversion else pkg$version
        origin <- if (!is.na(pkg$source)) pkg$source else "unknown"
        date <- if (!is.na(pkg$date)) as.character(pkg$date) else "unknown"

        result[[name]] <- list(
          version = version,
          origin = origin,
          date = date
        )
      }

      jsonlite::toJSON(result, auto_unbox = TRUE, pretty = FALSE)
    }

    cat(get_r_packages_info())
    """
    proc = subprocess.run(["Rscript", "-e", r_script], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"R error: {proc.stderr.strip()}")
    return json.loads(proc.stdout)

if __name__ == "__main__":
    full = {
        "date": date.today().isoformat(),
        "python": get_python_packages(),
        "r": get_r_packages()
    }
    json.dump(full, sys.stdout, indent=2)
    print()

