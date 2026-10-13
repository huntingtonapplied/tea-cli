"""tea livestreams — discover livestreams across platforms."""

import click
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


def _extract(data):
    """Livestream endpoints return either a list or {data|items|livestreams: [...]}."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "items", "livestreams", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _render(ctx, items):
    if is_structured(ctx):
        print_structured(ctx, items)
        return
    console = get_console(ctx)
    if not items:
        click.echo("No livestreams found.")
        return
    table = Table(show_edge=False, box=None, padding=(0, 1, 0, 1))
    table.add_column("Title")
    table.add_column("Platform")
    table.add_column("Viewers", justify="right")
    table.add_column("Live", justify="center")
    for s in items:
        live = s.get("is_live", s.get("live"))
        table.add_row(
            (s.get("title") or s.get("name") or "")[:45],
            str(s.get("platform") or ""),
            str(s.get("viewer_count") or s.get("viewers") or ""),
            "●" if live else "",
        )
    console.print(table)


@click.group()
def livestreams():
    """Discover livestreams (all / live / trending)."""


@livestreams.command("list")
@click.option("--limit", type=int, default=25, help="Max results")
@click.option("--platform", default=None, help="Filter by platform")
@click.pass_context
def list_streams(ctx, limit, platform):
    """List available livestreams."""
    client = _client(ctx)
    params = {"limit": limit}
    if platform:
        params["platform"] = platform
    try:
        _render(ctx, _extract(client.list_livestreams(params)))
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)


@livestreams.command("live")
@click.option("--limit", type=int, default=25, help="Max results")
@click.pass_context
def live_streams(ctx, limit):
    """List currently-live streams."""
    client = _client(ctx)
    try:
        _render(ctx, _extract(client.live_livestreams({"limit": limit})))
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)


@livestreams.command("trending")
@click.option("--limit", type=int, default=25, help="Max results")
@click.pass_context
def trending_streams(ctx, limit):
    """List trending streams."""
    client = _client(ctx)
    try:
        _render(ctx, _extract(client.trending_livestreams({"limit": limit})))
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)
