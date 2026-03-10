#!/usr/bin/env python3
"""Lisa — entry point."""
import sys
import argparse
from core.spawner import spawn

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lisa — AI-native terminal assistant",
        epilog='Examples:\n  lisa "install nmap"\n  lisa "clean up home dir"\n  lisa --reconfigure'
    )
    parser.add_argument("intent", type=str, nargs="?", default="", help="What you want done")
    parser.add_argument("--reconfigure", action="store_true", help="Rerun install probe")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive REPL mode")
    parser.add_argument("--stderr", type=str, metavar="ERROR", help="Passive mode: error from shell hook")
    args = parser.parse_args()

    if args.stderr:
        spawn("", stderr_context=args.stderr)
        return

    if args.reconfigure:
        from env.probe import run_probe
        run_probe()
        return

    if not args.intent.strip() and not args.interactive:
        parser.print_help()
        sys.exit(1)

    spawn(args.intent, interactive=args.interactive)

if __name__ == "__main__":
    main()
