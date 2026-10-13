"""tea completion — print a shell completion script."""

import click


_INSTRUCTIONS = {
    "bash": "eval \"$(_TEA_COMPLETE=bash_source tea)\"   # add to ~/.bashrc",
    "zsh": "eval \"$(_TEA_COMPLETE=zsh_source tea)\"     # add to ~/.zshrc",
    "fish": "_TEA_COMPLETE=fish_source tea | source     # add to ~/.config/fish/config.fish",
}


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """Print instructions to enable shell completion.

    \b
    Example:
        tea completion zsh
    """
    click.echo(f"# Enable tea completion for {shell}:")
    click.echo(_INSTRUCTIONS[shell])
