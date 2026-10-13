"""tea bookmarks — manage livestream bookmarks."""

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


def _render(ctx, items):
    if is_structured(ctx):
        print_structured(ctx, items)
        return
    console = get_console(ctx)
    if not items:
        click.echo("No bookmarks found.")
        return
    table = Table(show_edge=False, box=None, padding=(0, 1, 0, 1))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title")
    table.add_column("Platform")
    table.add_column("URL", style="cyan")
    for b in items:
        table.add_row(
            str(b.get("id", ""))[:8],
            (b.get("title") or b.get("name") or "")[:40],
            str(b.get("platform") or ""),
            (b.get("url") or "")[:50],
        )
    console.print(table)


@click.group()
def bookmarks():
    """List, add, search, and remove bookmarks."""


@bookmarks.command("list")
@click.option("--limit", type=int, default=50, help="Max results (applied client-side)")
@click.option("--platform", default=None, help="Filter by platform")
@click.pass_context
def list_bookmarks(ctx, limit, platform):
    """List your bookmarks."""
    client = _client(ctx)
    # GET /v1/bookmarks/ has no server-side pagination; slice client-side.
    params = {}
    if platform:
        params["platform"] = platform
    try:
        items = client.list_bookmarks(params)
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)
    if limit and limit > 0:
        items = items[:limit]
    _render(ctx, items)


@bookmarks.command("search")
@click.argument("query")
@click.option("--limit", type=int, default=50, help="Max results")
@click.pass_context
def search_bookmarks(ctx, query, limit):
    """Search your bookmarks by text."""
    client = _client(ctx)
    try:
        _render(ctx, client.search_bookmarks(query, {"limit": limit}))
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)


@bookmarks.command("add")
@click.argument("url")
@click.option("--title", default=None, help="Bookmark title")
@click.option("--platform", default=None, help="Platform (youtube, twitch, ...)")
@click.pass_context
def add_bookmark(ctx, url, title, platform):
    """Add a bookmark by stream URL."""
    client = _client(ctx)
    payload = {"url": url}
    if title:
        payload["title"] = title
    if platform:
        payload["platform"] = platform
    try:
        created = client.create_bookmark(payload)
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)
    if is_structured(ctx):
        print_structured(ctx, created)
    else:
        click.echo(f"✓ Added bookmark {str(created.get('id', ''))[:8]} — {created.get('url', url)}")


@bookmarks.command("delete")
@click.argument("bookmark_id")
@click.pass_context
def delete_bookmark(ctx, bookmark_id):
    """Delete a bookmark by ID."""
    client = _client(ctx)
    try:
        client.delete_bookmark(bookmark_id)
    except APIError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_GENERAL)
    click.echo(f"✓ Deleted bookmark {bookmark_id}")
