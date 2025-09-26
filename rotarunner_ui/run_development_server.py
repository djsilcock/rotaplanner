# runs the vite development server

import pathlib
import subprocess


def generate_types():
    """Generate types for the application."""
    subprocess.run(
        "npm run generate-client",
        shell=True,
        check=True,
        cwd=str(pathlib.Path(__file__, "..").resolve()),
    )
    print("Types generated successfully.")


def build_frontend():
    """Build the frontend application."""
    subprocess.run(
        "npm run build",
        shell=True,
        check=True,
        cwd=str(pathlib.Path(__file__, "..").resolve()),
    )
    print("Frontend built successfully.")
