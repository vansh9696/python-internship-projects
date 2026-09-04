import argparse
import json
import sys
from devcheck.inspector import run_diagnostics

def render_human_readable(data: dict) -> None:
    sep = "=" * 60
    print(sep)
    print(" DEVELOPER ENVIRONMENT DIAGNOSTICS REPORT")
    print(sep)
    print(f"Platform : {data['system']['platform']} ({data['system']['machine']})")
    print(f"Python   : {data['python']['installed_version']} [{data['python']['status']}]")
    print(f"Disk     : {data['disk']['free_gb']} GB free of {data['disk']['total_gb']} GB [{data['disk']['status']}]")
    
    print("\nEnvironment Variables:")
    for k, v in data["environment"]["variables"].items():
        state = "SET" if v["set"] else "MISSING"
        print(f"  • {k:<10}: {state}")
    
    print("\nDeveloper Tools:")
    for tool, details in data["tools"]["tools"].items():
        state = "FOUND" if details["found"] else "MISSING"
        v = f" ({details['version']})" if details['version'] else ""
        print(f"  • {tool:<10}: {state}{v}")
        
    print(sep)
    print(f"OVERALL STATUS: {data['overall_status']}")
    print(sep)

def main(args=None) -> int:
    parser = argparse.ArgumentParser(
        prog="devcheck",
        description="Inspect and report developer environment readiness."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw deterministic JSON report."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to file listing required CLI tools (one per line)."
    )

    parsed = parser.parse_args(args)

    try:
        results = run_diagnostics(parsed.config)
    except FileNotFoundError as e:
        sys.stderr.write(f"Configuration Error: {e}\n")
        return 2
    except ValueError as e:
        sys.stderr.write(f"Malformed Configuration: {e}\n")
        return 3
    except Exception as e:
        sys.stderr.write(f"Unexpected Runtime Error: {e}\n")
        return 4

    if parsed.json:
        print(json.dumps(results, indent=2))
    else:
        render_human_readable(results)

    # 0 for PASS, 1 for degraded / missing dependencies
    return 0 if results["overall_status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())