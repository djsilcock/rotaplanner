import rotaplanner.database.commands as db_commands

import click


@click.group()
def cli():
    pass


cli.add_command(db_commands.db)


@cli.command("run-webview")
def run_webview():
    from rotaplanner.webview_version import main as webview_main

    webview_main()
