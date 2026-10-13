"""tea status — show account and platform overview."""

import click
from rich.panel import Panel

from tea_cli.api import TeaClient, AuthError, APIError
from tea_cli.output import get_console, is_json, print_json
from tea_cli.exit_codes import EXIT_AUTH


@click.command()
@click.pass_context
def status(ctx):
    """Show your account and a snapshot of platform activity."""
    try:
        client = TeaClient()
    except AuthError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(EXIT_AUTH)

    user = None
    try:
        user = client.me()
    except APIError as e:
        if not is_json(ctx):
            click.echo(f"⚠ Could not load account: {e}", err=True)

    metrics = None
    try:
        metrics = client.public_metrics()
    except APIError:
        pass

    if is_json(ctx):
        print_json({"user": user, "metrics": metrics})
        return

    console = get_console(ctx)

    if user:
        name = user.get("email") or user.get("name") or user.get("id") or "unknown"
        tier = user.get("tier") or user.get("subscription_tier") or "—"
        console.print(Panel(
            f"Account: [bold]{name}[/bold]\n"
            f"Tier:    {tier}\n"
            f"API URL: [dim]{client.api_url}[/dim]",
            title="Account",
            expand=False,
        ))
    else:
        console.print(Panel("Not signed in — run [dim]tea login[/dim]", expand=False))

    if metrics:
        lines = "\n".join(
            f"{k.replace('_', ' ').title()}: [bold]{v}[/bold]"
            for k, v in metrics.items()
            if isinstance(v, (int, float, str))
        )
        if lines:
            click.echo()
            console.print(Panel(lines, title="Platform", expand=False))
