"""forge CLI — `forge generate` / `forge validate`.

Usage:
    forge generate --source <file://… | http://… | azureblob://…>
                   --target <csharp|typescript|python|all>
                   --out <dir>
                   [--consumer-repo owner/repo]   # if set, opens a PR via pr_opener

    forge validate --source <…>

Same code path as the FastAPI /generate handler (server.py imports `generate`).
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import __version__
from .ir import Model, validate as validate_ir
from .parsers import rdf_parser, yaml_parser
from .sources import load as load_source

TARGETS = ("csharp", "typescript", "python", "bpmn", "cacao", "all")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="forge", description="agentarmy-forge codegen CLI")
    p.add_argument("--version", action="version", version=f"forge {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate source files for one or more targets")
    g.add_argument("--source", required=True, help="source URI (file://, http://, azureblob://)")
    g.add_argument("--target", required=True, choices=TARGETS)
    g.add_argument("--out", required=True, help="output directory (created if absent)")
    g.add_argument(
        "--consumer-repo",
        default=None,
        help="if set, open a PR against owner/repo with the generated files",
    )
    g.add_argument(
        "--branch",
        default=None,
        help="branch name for the consumer PR (default: derived from source URI)",
    )

    v = sub.add_parser("validate", help="parse a source + report IR validation errors")
    v.add_argument("--source", required=True)

    args = p.parse_args(argv)

    if args.cmd == "generate":
        return _cmd_generate(args)
    if args.cmd == "validate":
        return _cmd_validate(args)
    return 2


def _cmd_generate(args) -> int:
    try:
        result = generate(
            source=args.source,
            target=args.target,
            out_dir=args.out,
            consumer_repo=args.consumer_repo,
            branch=args.branch,
        )
    except Exception as e:
        sys.stderr.write(f"forge generate FAILED: {e}\n")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_validate(args) -> int:
    try:
        model = _load_and_parse(args.source)
    except Exception as e:
        sys.stderr.write(f"forge validate FAILED to parse: {e}\n")
        return 1
    errors = validate_ir(model)
    if errors:
        sys.stderr.write("forge validate FAILED:\n")
        for e in errors:
            sys.stderr.write(f"  - {e}\n")
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "version": model.version,
                "namespace": model.namespace,
                "object_types": len(model.object_types),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


# ---------------------------------------------------------------------------
# Library-shape entrypoint — server.py calls this directly for /generate.
# ---------------------------------------------------------------------------
def generate(
    *,
    source: str,
    target: str,
    out_dir: str,
    consumer_repo: Optional[str] = None,
    branch: Optional[str] = None,
    if_none_match: Optional[str] = None,
) -> dict:
    if target not in TARGETS:
        raise ValueError(f"target must be one of {TARGETS}; got {target!r}")

    sr = load_source(source, if_none_match=if_none_match)
    if sr.bytes == b"":  # HTTP 304 — no change since last etag
        return {
            "ok": True,
            "source": source,
            "etag": sr.etag,
            "no_change": True,
            "files": [],
        }

    model = _parse_bytes(sr.bytes, sr.source_uri)
    errors = validate_ir(model)
    if errors:
        raise ValueError("invalid model: " + "; ".join(errors))

    targets = [target] if target != "all" else ["csharp", "typescript", "python"]
    written: dict[str, list[str]] = {}
    for t in targets:
        em = _emitter_for(t)
        written[t] = em.emit(model, out_dir)

    pr_info = None
    if consumer_repo:
        from .pr_opener import open_pr

        pr_info = open_pr(
            consumer_repo=consumer_repo,
            files_dir=out_dir,
            source=source,
            model_version=model.version,
            branch=branch,
        )

    return {
        "ok": True,
        "source": source,
        "etag": sr.etag,
        "version": model.version,
        "namespace": model.namespace,
        "object_types": [ot.name for ot in model.object_types],
        "targets": targets,
        "files": {t: written[t] for t in targets},
        "out_dir": out_dir,
        "pr": pr_info,
    }


def _load_and_parse(source: str) -> Model:
    sr = load_source(source)
    return _parse_bytes(sr.bytes, sr.source_uri)


def _parse_bytes(data: bytes, source_uri: str) -> Model:
    parser = _parser_for(source_uri)
    return parser.parse(data, source_uri=source_uri)


def _parser_for(source_uri: str):
    low = source_uri.lower()
    if any(low.endswith(ext) for ext in (".yaml", ".yml")):
        return yaml_parser
    if any(low.endswith(ext) for ext in (".ttl", ".jsonld", ".json-ld", ".nt", ".ntriples")):
        return rdf_parser
    # Default: try YAML (the safer default — RDF rejects unrelated input
    # noisily while YAML loads almost anything as a string and we can fail
    # at the validate step).
    return yaml_parser


def _emitter_for(target: str):
    if target == "csharp":
        from .emitters import csharp

        return csharp
    if target == "typescript":
        from .emitters import typescript

        return typescript
    if target == "python":
        from .emitters import python

        return python
    if target == "bpmn":
        from .emitters import bpmn

        return bpmn
    if target == "cacao":
        from .emitters import cacao

        return cacao
    raise ValueError(f"unknown target: {target!r}")


if __name__ == "__main__":
    sys.exit(main())
