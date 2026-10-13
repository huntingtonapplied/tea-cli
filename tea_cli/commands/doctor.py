"""tea doctor — diagnose connectivity and configuration."""

import click

from tea_cli.config import CONFIG_FILE, get_api_key, get_api_url, load_config, validate_config
from tea_cli.api import TeaClient, APIError
from tea_cli.output import get_console, is_json, print_json


@click.command()
@click.pass_context
def doctor(ctx):
    """Check configuration, connectivity, and authentication."""
    checks = []

    api_url = get_api_url()
    api_key = get_api_key()

    checks.append(("config file", CONFIG_FILE.exists(),
                   str(CONFIG_FILE) if CONFIG_FILE.exists() else "not created (run: tea login)"))
    checks.append(("api_url", True, api_url))
    checks.append(("api_key", bool(api_key),
                   "set" if api_key else "missing (run: tea login)"))

    for w in validate_config(load_config()):
        checks.append(("config warning", False, w))

    # Backend reachability (no auth needed).
    reachable = False
    try:
        TeaClient(require_auth=False).health()
        reachable = True
        checks.append(("backend reachable", True, api_url))
    except APIError as e:
        checks.append(("backend reachable", False, str(e).splitlines()[0]))
    except Exception as e:
        checks.append(("backend reachable", False, str(e)))

    # Authentication (only if a key is present and backend is up).
    if api_key and reachable:
        try:
            user = TeaClient().me()
            who = user.get("email") or user.get("id") or "ok"
            checks.append(("authentication", True, who))
        except Exception as e:
            checks.append(("authentication", False, str(e).splitlines()[0]))

    if is_json(ctx):
        print_json([
            {"check": name, "ok": ok, "detail": detail} for name, ok, detail in checks
        ])
        return

    console = get_console(ctx)
    for name, ok, detail in checks:
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        console.print(f"{icon} {name}: [dim]{detail}[/dim]")
