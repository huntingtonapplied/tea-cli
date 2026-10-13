"""Tea CLI entry point."""

import os
import signal
import sys

import click

from tea_cli import __version__
from tea_cli.log import setup_logging, logger
from tea_cli.exit_codes import EXIT_GENERAL, EXIT_SIGINT, EXIT_SIGTERM
from tea_cli.config import load_config, validate_config
from tea_cli.commands.login import login
from tea_cli.commands.status import status
from tea_cli.commands.bookmarks import bookmarks
from tea_cli.commands.livestreams import livestreams
from tea_cli.commands.keys import keys
from tea_cli.commands.doctor import doctor
from tea_cli.commands.completion import completion


@click.group()
@click.version_option(version=__version__, prog_name="tea")
@click.option("--output", "-o", type=click.Choice(["table", "json", "yaml"]), default="table",
              help="Output format (default: table)")
@click.option("--no-color", is_flag=True, default=False, envvar="NO_COLOR",
              help="Disable colored output")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Show informational messages (INFO level)")
@click.option("--debug", is_flag=True, default=False,
              help="Show debug messages including HTTP requests")
@click.option("--ci", is_flag=True, default=False,
              help="CI mode: no color, no interactive prompts")
@click.pass_context
def cli(ctx, output, no_color, verbose, debug, ci):
    """Tea CLI — control the Tea multi-livestream platform from your terminal."""
    if not ci and (os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("GITLAB_CI")):
        ci = True
    if ci:
        no_color = True

    ctx.ensure_object(dict)
    ctx.obj["output"] = output
    ctx.obj["no_color"] = no_color
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug
    ctx.obj["ci"] = ci
    setup_logging(verbose=verbose, debug=debug)

    config = load_config()
    if config:
        for w in validate_config(config):
            click.echo(f"Warning: {w}", err=True)


cli.add_command(login)
cli.add_command(status)
cli.add_command(bookmarks)
cli.add_command(livestreams)
cli.add_command(keys)
cli.add_command(doctor)
cli.add_command(completion)


def _safe_stdio():
    """Never crash on a non-UTF-8 locale (LANG=C / env -i => ascii stdout).

    Output uses glyphs like the check/cross marks; under an ascii stream they would
    raise UnicodeEncodeError. Keep the stream's encoding but replace unencodable
    characters instead of failing (LAUNCH-CLI-SWEEP, mirrors chief R-chief-12)."""
    for stream in (sys.stdout, sys.stderr):
        enc = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        if enc in ("utf8", "utf16", "utf32"):
            continue
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass


def main():
    """Entry point with top-level signal and exception handling."""
    _safe_stdio()
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(EXIT_SIGTERM))
    try:
        cli(standalone_mode=False)
    except click.exceptions.Exit as e:
        raise SystemExit(e.exit_code)
    except click.ClickException as e:
        e.show()
        raise SystemExit(e.exit_code)
    except (KeyboardInterrupt, click.Abort):
        raise SystemExit(EXIT_SIGINT)
    except SystemExit:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise SystemExit(EXIT_GENERAL)


if __name__ == "__main__":
    main()
