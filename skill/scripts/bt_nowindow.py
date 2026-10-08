"""On Windows, run every child process (git, gitleaks…) without flashing a console window.

Hooks and the web server run without a console; when such a process starts a console program, Windows opens a
new window for it that pops up and closes. Importing this module makes subprocess default to CREATE_NO_WINDOW
whenever the caller didn't ask for specific creation flags (explicit flags — e.g. opening the executor's terminal
with CREATE_NEW_CONSOLE — are left untouched).
"""
import os
import subprocess

if os.name == "nt" and not getattr(subprocess.Popen, "_bt_nowindow", False):
    _NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW
    _original_init = subprocess.Popen.__init__

    def _init(self, *args, **kwargs):
        if not kwargs.get("creationflags"):
            kwargs["creationflags"] = _NO_WINDOW
        _original_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _init
    subprocess.Popen._bt_nowindow = True
