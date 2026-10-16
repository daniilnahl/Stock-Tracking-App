"""Fixed loopback process entry point; help never performs launch preflight."""

import sys

from .configuration import ApiConfigurationError, load_api_configuration


HELP = """Usage: python -m stock_tracker.api --database FILE --history-cache FILE
       --menu-legacy FILE --evaluation-legacy FILE [--enable-history] [--dashboard]

Authenticated local holdings read-only API at 127.0.0.1:8000.
Four explicit distinct file paths are required; no parents are created.
Historical acquisition is disabled by default.

Options:
  --database FILE           Existing holdings SQLite file or explicit new path
  --history-cache FILE      Explicit historical cache file path
  --menu-legacy FILE        Corresponding menu legacy file path
  --evaluation-legacy FILE  Corresponding evaluation legacy file path
  --dashboard              Serve the packaged local read-only dashboard at /
  --enable-history         Enable only after owner-confirmed local display/cache
                           rights are recorded in docs/API_OPERATIONS.md
  -h, --help               Show this help without configuration or data access
"""


def parse_arguments(argv):
    # Static English help avoids argparse/gettext's locale files, language
    # environment and terminal-size reads. Only these six launch flags exist.
    if "--help" in argv or "-h" in argv:
        sys.stdout.write(HELP)
        raise SystemExit(0)
    names = {"--" + name.replace("_", "-"): name for name in
             ("database", "history_cache", "menu_legacy", "evaluation_legacy")}
    values, enabled, dashboard = {}, False, False
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--enable-history" and not enabled:
            enabled = True
            index += 1
        elif option == "--dashboard" and not dashboard:
            dashboard = True
            index += 1
        elif option in names and names[option] not in values and index + 1 < len(argv) and not argv[index + 1].startswith("--"):
            values[names[option]] = argv[index + 1]
            index += 2
        else:
            break
    if index != len(argv) or len(values) != 4:
        sys.stderr.write("Local API arguments are invalid. Use --help for the four required file options.\n")
        raise SystemExit(2)
    return {**values, "enable_history": enabled, "enable_dashboard": dashboard}


def main(argv=None):
    arguments = parse_arguments(list(sys.argv[1:] if argv is None else argv))
    try:
        configuration = load_api_configuration(**arguments)
        from .composition import create_local_app
        import uvicorn

        uvicorn.run(create_local_app(configuration), host="127.0.0.1", port=8000,
                    workers=1, reload=False, proxy_headers=False, forwarded_allow_ips="",
                    access_log=False, log_config=None, log_level="critical")
    except ApiConfigurationError as error:
        sys.stderr.write(str(error) + "\n")
        return 2
    except KeyboardInterrupt:
        return 0
    except (Exception, SystemExit):
        # ASGI/server startup exceptions can embed paths or credentials. No raw
        # exception or traceback crosses the process presentation boundary.
        sys.stderr.write("Local API could not start. Check configuration and whether port 8000 is available.\n")
        return 1
    return 0
