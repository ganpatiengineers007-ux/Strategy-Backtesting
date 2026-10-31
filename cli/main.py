"""CLI: python -m cli.main {demo|list|run}"""
import argparse
import sys

from cli import commands


def main(argv=None):
    ap = argparse.ArgumentParser(prog="svl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=commands.cmd_list)
    d = sub.add_parser("demo")
    d.add_argument("--out", default="runs")
    d.set_defaults(fn=commands.cmd_demo)
    r = sub.add_parser("run")
    r.add_argument("--strategy", required=True)
    r.add_argument("--data", required=True)
    r.add_argument("--out", default="runs")
    r.set_defaults(fn=commands.cmd_run)
    o = sub.add_parser("optimize")
    o.add_argument("--strategy", required=True)
    o.add_argument("--data", required=True)
    o.add_argument("--grid", required=True, help='JSON: {"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}')
    o.add_argument("--out", default="runs")
    o.set_defaults(fn=commands.cmd_optimize)
    s = sub.add_parser("make-sample")
    s.add_argument("--out", default="data/samples/sample_5m.csv")
    s.add_argument("--days", type=int, default=120)
    s.set_defaults(fn=commands.cmd_sample)
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
