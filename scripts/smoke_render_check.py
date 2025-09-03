#!/usr/bin/env python3
"""Simple smoke checks for the local or deployed backend.

Usage:
  python scripts/smoke_render_check.py --url http://localhost:8000
"""
import argparse
import requests


def check(url, path):
    full = url.rstrip("/") + path
    try:
        r = requests.get(full, timeout=5)
        print(f"{full} -> {r.status_code}")
        print(r.text[:200])
    except Exception as e:
        print(f"ERROR {full}: {e}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000")
    args = p.parse_args()
    check(args.url, "/healthz/")
    check(args.url, "/api/v1/health/")


if __name__ == "__main__":
    main()
