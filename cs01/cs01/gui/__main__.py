"""
CS-01 DPDP Compliance Auditor — GUI entrypoint.

Launch with any of:
  python -m cs01.gui
  cs01-gui           (after pip install -e .)
"""
from __future__ import annotations

import sys


def main() -> None:
    from cs01.gui.app import create_app
    from cs01.gui.main_window import MainWindow

    app = create_app(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
