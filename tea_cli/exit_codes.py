"""Standard exit codes for the Tea CLI.

These allow scripts and CI pipelines to distinguish between failure types.
"""

EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_AUTH = 2
EXIT_NOT_FOUND = 3
EXIT_VALIDATION = 4
EXIT_NETWORK = 5
EXIT_SERVER = 6
EXIT_DUPLICATE = 7
EXIT_SIGINT = 130
EXIT_SIGTERM = 143
