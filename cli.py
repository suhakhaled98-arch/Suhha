#!/usr/bin/env python3
"""Command-line entry point for Suhha agent.

Usage:
  python cli.py run "لخصيلي آخر أخبار الذكاء الاصطناعي"
  python cli.py chat
  python cli.py feedback "كنت عايزة رد أقصر المرة اللي فاتت"
  python cli.py reflect
"""
import sys

from suhha import learn, memory
from suhha.agent import run_task


def cmd_run(args: list[str]) -> None:
    if not args:
        print("استخدام: python cli.py run \"المهمة\"")
        sys.exit(1)
    task = " ".join(args)
    print(run_task(task))


def cmd_chat() -> None:
    print("Suhha جاهزة. اكتبي المهمة، أو 'خروج' للإنهاء.")
    while True:
        try:
            task = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if task in {"خروج", "exit", "quit"}:
            break
        if not task:
            continue
        print(run_task(task))


def cmd_feedback(args: list[str]) -> None:
    if not args:
        print("استخدام: python cli.py feedback \"النص\"")
        sys.exit(1)
    memory.record_feedback(" ".join(args))
    print("اتسجل، هيتاخد في الاعتبار في أول reflect.")


def cmd_reflect() -> None:
    print(learn.reflect())


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    command, rest = sys.argv[1], sys.argv[2:]
    if command == "run":
        cmd_run(rest)
    elif command == "chat":
        cmd_chat()
    elif command == "feedback":
        cmd_feedback(rest)
    elif command == "reflect":
        cmd_reflect()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
