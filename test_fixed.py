#!/usr/bin/env python3

import subprocess
import time
import argparse
import os
import signal
from collections import defaultdict


# -----------------------
# Utility Helpers
# -----------------------

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except subprocess.CalledProcessError:
        return ""


def header(title):
    print(f"\n=== {title} ===")


def get_pty_processes():
    """
    Returns dict: pid -> { 'cmd': str, 'ptys': [tty paths] }
    """
    # Don't filter with grep - parse the full lsof output
    out = run("lsof -FpncT")
    lines = out.splitlines()

    processes = {}
    current_pid = None
    current_cmd = None

    for line in lines:
        if line.startswith("p"):    # PID
            current_pid = line[1:]
            current_cmd = None  # Reset command for new PID
        elif line.startswith("c"):  # Command name
            current_cmd = line[1:]
        elif line.startswith("n/dev/ttys"):  # PTY path
            if current_pid:
                if current_pid not in processes:
                    processes[current_pid] = {"cmd": current_cmd, "ptys": []}
                processes[current_pid]["ptys"].append(line[1:])
                # Update cmd if we have it now
                if current_cmd and not processes[current_pid]["cmd"]:
                    processes[current_pid]["cmd"] = current_cmd

    return processes


def kill_pid(pid):
    try:
        os.kill(int(pid), signal.SIGTERM)
        return True
    except:
        return False


def is_copilot_like(cmd):
    if not cmd:
        return False
    cmd = cmd.lower()
    return (
        "copilot" in cmd or
        ("node" in cmd and "copilot" in cmd) or
        ("agent" in cmd and "copilot" in cmd)
    )


def cleanup(processes, quiet=False):
    killed = []
    for pid, info in processes.items():
        if is_copilot_like(info["cmd"]):
            if kill_pid(pid):
                killed.append(pid)
                if not quiet:
                    print(f"Killed PID {pid} ({info['cmd']}) — {len(info['ptys'])} PTYs")
    return killed


def summarize(processes):
    total_ptys = sum(len(info["ptys"]) for info in processes.values())

    header("Summary")
    print(f"Total PTYs in use: {total_ptys}")
    print(f"Processes holding PTYs: {len(processes)}")

    heavy = [(p, info) for p, info in processes.items() if len(info["ptys"]) > 4]
    if heavy:
        print("\nHeavy PTY users (>4 PTYs):")
        for pid, info in heavy:
            print(f"• PID {pid} ({info['cmd']}) — {len(info['ptys'])} PTYs")

    suspected = [(p, info) for p, info in processes.items() if is_copilot_like(info['cmd'])]
    if suspected:
        print("\nSuspected Copilot/Node leaks:")
        for pid, info in suspected:
            print(f"• PID {pid} ({info['cmd']}) — {len(info['ptys'])} PTYs")


# -----------------------
# Main Commands
# -----------------------

def command_show():
    processes = get_pty_processes()

    header("PTY Usage")
    print(f"Found {len(processes)} processes with PTYs.\n")

    for pid, info in processes.items():
        cmd = info["cmd"] or "(unknown)"
        print(f"PID {pid}: {cmd}")
        for p in info["ptys"]:
            print(f"   - {p}")

    summarize(processes)


def command_clean():
    processes = get_pty_processes()

    header("Cleaning PTY leaks")

    killed = cleanup(processes)

    if not killed:
        print("No Copilot-related PTY leaks detected.")
    else:
        print(f"\nKilled {len(killed)} leaking processes.")

    summarize(get_pty_processes())


def command_watch(interval):
    print(f"Watching PTY usage every {interval}s… Ctrl+C to stop.\n")

    while True:
        processes = get_pty_processes()
        total_ptys = sum(len(info["ptys"]) for info in processes.values())

        # Print compact status line
        print(f"[watch] PTYs={total_ptys:3d}  procs={len(processes):3d}", end="")

        if total_ptys > 200:
            print("  !! HIGH — cleaning…")
            cleanup(processes, quiet=True)
        else:
            print("")

        time.sleep(interval)


# -----------------------
# Argument Parser
# -----------------------

def main():
    p = argparse.ArgumentParser(prog="pty", description="PTY inspector + cleaner")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("show", help="List PTY usage in detail")
    sub.add_parser("clean", help="Kill Copilot-related PTY leaks")

    w = sub.add_parser("watch", help="Monitor PTY usage and auto-clean")
    w.add_argument("--interval", type=int, default=5)

    args = p.parse_args()

    if args.cmd == "show":
        command_show()
    elif args.cmd == "clean":
        command_clean()
    elif args.cmd == "watch":
        command_watch(args.interval)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
