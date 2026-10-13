"""tea login — authenticate and store an API key."""

import click
from rich.panel import Panel

from tea_cli.config import save_config, load_config, get_api_url
from tea_cli.api import TeaClient
from tea_cli.output import get_console
from tea_cli.exit_codes import EXIT_VALIDATION


@click.command()
@click.option("--key", default=None, help="Your Tea API key (skips the wizard)")
@click.option("--url", default=None, help="API URL (default: https://api.goodtea.world)")
@click.pass_context
def login(ctx, key: str, url: str):
    """Authenticate with the Tea platform.

    \b
    Examples:
        tea login                    # interactive wizard
        tea login --key tea_abc123   # non-interactive
    """
    console = get_console(ctx)
    ci_mode = ctx.obj.get("ci", False) if ctx.obj else False

    if not key and ci_mode:
        click.echo("✗ --key is required in CI mode", err=True)
        raise SystemExit(EXIT_VALIDATION)

    if not key:
        click.echo("  Welcome to Tea!")
        click.echo("  Create an API key in the product app: Account › Developer › New key")
        key = click.prompt("  API Key", hide_input=True)
        if not url:
            if click.confirm("  Use a custom API URL?", default=False):
                url = click.prompt("  API URL", default="https://api.goodtea.world")

    key = key.strip()
    config = load_config()
    config["api_key"] = key
    if url:
        config["api_url"] = url.strip()
    save_config(config)

    resolved_url = url or get_api_url()
    click.echo("✓ API key saved to ~/.tea/config.yaml")
    click.echo(f"  API URL: {resolved_url}")

    # Verify the key against the backend.
    try:
        client = TeaClient(api_key=key, api_url=resolved_url)
        user = client.me()
        name = user.get("email") or user.get("name") or user.get("id") or "user"
        console.print(Panel(
            f"✓ Authenticated as [bold]{name}[/bold]\n\n"
            "  [dim]tea status[/dim]       account + platform overview\n"
            "  [dim]tea bookmarks[/dim]    manage your bookmarks\n"
            "  [dim]tea livestreams[/dim]  discover live streams",
            title="Connected",
            border_style="green",
            expand=False,
        ))
    except Exception as e:
        click.echo(f"⚠ Key saved but verification failed: {e}", err=True)
