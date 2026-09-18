import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"


def main() -> None:
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
