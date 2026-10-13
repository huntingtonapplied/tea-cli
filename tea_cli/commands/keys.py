"""tea keys — manage developer API keys."""

import click
from rich.panel import Panel
from rich.table import Table

from tea_cli.api import TeaClient, AuthError, APIError
from tea_cli.output import get_console, is_structured, print_structured
from tea_cli.exit_codes import EXIT_AUTH, EXIT_GENERAL


def _client(ctx):
    try:
        return TeaClient()
    except AuthError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_AUTH)


@click.group()
def keys():
    """List, create, and revoke developer API keys."""


@keys.command("list")
@click.pass_context
def list_keys(ctx):
    """List your API keys (secrets are never shown)."""
    client = _client(ctx)
    try:
        data = client.list_keys()
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)

    items = data.get("keys", data) if isinstance(data, dict) else data
    if is_structured(ctx):
        print_structured(ctx, data)
        return
    console = get_console(ctx)
    if not items:
        click.echo("No API keys. Create one with: tea keys create <name>")
        return
    table = Table(show_edge=False, box=None, padding=(0, 1, 0, 1))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("Prefix", style="cyan")
    table.add_column("Requests", justify="right")
    table.add_column("Active", justify="center")
    for k in items:
        table.add_row(
            str(k.get("id", ""))[:8],
            k.get("name", ""),
            k.get("key_prefix", ""),
            str(k.get("request_count", 0)),
            "✓" if k.get("is_active", True) else "✗",
        )
    console.print(table)


@keys.command("create")
@click.argument("name")
@click.option("--scope", "scopes", multiple=True, help="Scope (repeatable). Default: read:bookmarks")
@click.option("--expires-in-days", type=int, default=None, help="Days until expiry (default: never)")
@click.pass_context
def create_key(ctx, name, scopes, expires_in_days):
    """Create a new API key. The secret is shown ONCE."""
    client = _client(ctx)
    payload = {"name": name}
    if scopes:
        payload["scopes"] = list(scopes)
    if expires_in_days is not None:
        payload["expires_in_days"] = expires_in_days
    try:
        created = client.create_key(payload)
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)

    if is_structured(ctx):
        print_structured(ctx, created)
        return
    console = get_console(ctx)
    console.print(Panel(
        f"[bold]{created.get('key', '')}[/bold]\n\n"
        "[yellow]Save this key now — it will not be shown again.[/yellow]\n"
        f"[dim]tea login --key {created.get('key', '<key>')}[/dim]",
        title=f"API key '{created.get('name', name)}' created",
        border_style="green",
        expand=False,
    ))


@keys.command("delete")
@click.argument("key_id")
@click.pass_context
def delete_key(ctx, key_id):
    """Revoke an API key by ID."""
    client = _client(ctx)
    try:
        client.delete_key(key_id)
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)
    click.echo(f"✓ Revoked API key {key_id}")
