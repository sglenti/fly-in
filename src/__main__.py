"""Command-line entry point for the fly-in project.

This module imports the application entry point and presents a friendly
startup error message if the runtime environment is missing dependencies.
"""

import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"


def main() -> None:
    """Run the application entry point with graceful error handling.

    This wrapper imports the real application entry point and reports any
    dependency or runtime errors in a user-friendly way before exiting.

    Raises:
        SystemExit: If the application fails to start or a dependency is
            missing.
    """
    try:
        from src.main import main as run
        run()
    except ImportError as e:
        print(f"Error: Missing required dependency -> {e}", file=sys.stderr)
        print("Did you run 'make install' or 'uv sync'?", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fatal Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
