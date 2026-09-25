#!/usr/bin/env python3
"""CLI entry point.

Usage:
  python main.py --extract          # parse documents -> SQLite
  python main.py --index            # build BM25 + vector indexes
  python main.py --query "..."      # answer one requirement
  python main.py --eval             # score against labelled examples
  python main.py --eval --mode rag  # (stub until RAG variant is implemented)
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Windows PowerShell defaults to cp1252 which cannot encode ₹ (U+20B9).
# Reconfigure stdout/stderr to UTF-8 so all output works correctly.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import yaml  # noqa: E402


def load_cfg() -> dict:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    # Anchor every path entry to the project root so the pipeline is CWD-agnostic.
    for key, val in cfg["paths"].items():
        cfg["paths"][key] = str(ROOT / val)
    return cfg


def main() -> None:
    p = argparse.ArgumentParser(description="Financial opportunity recommendation engine")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--extract", action="store_true", help="extract documents into the DB")
    src.add_argument("--index", action="store_true", help="build retrieval indexes")
    src.add_argument("--query", metavar="TEXT", help="natural-language requirement")
    src.add_argument("--eval", action="store_true", help="evaluate on labelled examples")
    p.add_argument("--mode", choices=["rules", "rag"], default="rules")
    p.add_argument("--k", type=int, default=None, help="override result count")
    args = p.parse_args()

    cfg = load_cfg()

    if args.extract:
        from src.extractor.extract import extract_all
        from src.storage.db import OpportunityDB
        db = OpportunityDB(cfg)
        n = extract_all(Path(cfg["paths"]["opportunities_dir"]), db)
        print(f"Extracted {n} opportunities -> {cfg['paths']['db']}")
    elif args.index:
        from src.storage.index import build_index
        from src.storage.db import OpportunityDB
        build_index(cfg, OpportunityDB(cfg))
        print("Indexes built.")
    elif args.query:
        from src.pipeline import run_query
        rec = run_query(cfg, args.query, mode=args.mode)
        from src.evaluator.report import print_recommendation
        print_recommendation(rec, top_n=args.k or cfg["output"]["top_n"])
    elif args.eval:
        from src.evaluator.runner import run_evaluation
        from src.evaluator.report import print_eval_report
        rows, overall = run_evaluation(cfg, mode=args.mode)
        print_eval_report(rows, overall)


if __name__ == "__main__":
    main()
