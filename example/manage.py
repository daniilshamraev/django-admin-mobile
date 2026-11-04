#!/usr/bin/env python
"""Run the demo admin. Local only."""

import os
import sys
from pathlib import Path


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")
    project_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_dir))
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
