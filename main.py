"""
main.py
-------
Entry point for the "System Pulse" live resource dashboard.

Run with:
    python main.py

Works on Windows, Linux and macOS. Make sure you have created the
conda environment and installed requirements.txt first (see README
instructions given alongside this project).
"""

import sys


def main():
    try:
        from dashboard import App
    except ImportError as e:
        print("Missing dependency ->", e)
        print("Run:  pip install -r requirements.txt")
        sys.exit(1)

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()