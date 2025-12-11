"""
Small test runner for Control-system-Agent API.

Usage:
  python scripts/test_agent_api.py           # run all cases
  python scripts/test_agent_api.py --case ds # run one case

Env:
  AGENT_URL - full URL to POST /v1/ask (default: http://localhost:8000/v1/ask)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List

import requests


BASE_URL = os.getenv("AGENT_URL", "http://localhost:8000/v1/ask")


def build_cases() -> Dict[str, str]:
    return {
        "cls_nyquist": "Объясни, как критерий Найквиста используют для проверки устойчивости линейной системы.",
        "ds_signals": "Чем отличается дискретный сигнал от цифрового и что такое квантование?",
        "nl_lyapunov": "Расскажи кратко про устойчивость по Ляпунову для нелинейных систем",
    }


def send_case(name: str, question: str) -> None:
    payload = {"question": question, "chat_history": []}
    print(f"\n=== Case: {name} ===")
    try:
        resp = requests.post(BASE_URL, json=payload, timeout=900)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print("Response JSON:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print("Raw response:")
            print(resp.text)
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="Run only one case by name.")
    parser.add_argument(
        "--sleep",
        type=int,
        default=1,
        help="Seconds to wait between cases (default: 1).",
    )
    args = parser.parse_args()

    cases = build_cases()

    if args.case:
        if args.case not in cases:
            print(f"Case {args.case} not found. Available: {', '.join(cases.keys())}")
            sys.exit(1)
        send_case(args.case, cases[args.case])
        return

    items = list(cases.items())
    for idx, (name, question) in enumerate(items):
        send_case(name, question)
        if idx < len(items) - 1 and args.sleep > 0:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
