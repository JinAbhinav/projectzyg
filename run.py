#!/usr/bin/env python
"""
Convenience script to run the SEER application.
"""

import os
import sys
import subprocess

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))


def run_command(command):
    """Run a command with proper output handling."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True
    )
    
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    return process.returncode


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the SEER application.")
    parser.add_argument("command", choices=["api", "migrate"], help="Command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    
    args = parser.parse_args()
    
    # Change to the script directory
    os.chdir(script_dir)
    
    if args.command == "api":
        print("Starting SEER API server...")
        return run_command(f"{sys.executable} main.py api")
    elif args.command == "migrate":
        migrate_args = " ".join(args.args)
        print("Running database migrations...")
        return run_command(f"{sys.executable} scripts/migrate.py {migrate_args}")
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 