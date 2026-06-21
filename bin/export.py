# -*- coding: utf-8 -*-

from reveal import exporter

from relib.frameworks.ida_pro import get_framework

import importlib
import importlib.resources
import logging.config
import os
import traceback


def main() -> int:
    try:
        path = importlib.resources.files("reveal.data") / "logging.ini"
        logging.config.fileConfig(str(path))
        program = get_framework()
        exporter.Exporter(program).export()
        if os.getenv("REVEAL_EXIT"):
            program.exit(0)
    except:
        traceback.print_exc()
    return os.EX_OK


if __name__ == "__main__":
    main()
