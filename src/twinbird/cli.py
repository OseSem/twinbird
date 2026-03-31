from __future__ import annotations

from typing import Annotated

import typer

from twinbird import instance as inst

app = typer.Typer(
    name="twinbird",
    help="Manage multiple NetBird instances with isolated configs and interfaces.",
)


@app.command()
def up(
    name: str = typer.Argument(help="Instance name"),
    management_url: str = typer.Option(
        ...,
        "--management-url",
        envvar="TWINBIRD_MANAGEMENT_URL",
        help="NetBird management URL",
    ),
    setup_key: Annotated[
        str | None,
        typer.Option(
            "--setup-key",
            envvar="TWINBIRD_SETUP_KEY",
            help="NetBird setup key (omit for OAuth login)",
        ),
    ] = None,
    interface_name: Annotated[
        str | None,
        typer.Option("--interface-name", help="Override WireGuard interface name"),
    ] = None,
    daemon_addr: Annotated[
        str | None,
        typer.Option("--daemon-addr", help="Override daemon address"),
    ] = None,
) -> None:
    """Start a named NetBird instance."""
    inst.up(
        name=name,
        management_url=management_url,
        setup_key=setup_key,
        interface_name=interface_name,
        daemon_addr=daemon_addr,
    )


@app.command()
def down(
    name: str = typer.Argument(help="Instance name"),
) -> None:
    """Stop a named NetBird instance."""
    inst.down(name)


@app.command()
def status(
    name: Annotated[
        str | None, typer.Argument(help="Instance name (omit for all)")
    ] = None,
) -> None:
    """Show status of one or all instances."""
    inst.status(name)


@app.command(name="list")
def list_cmd() -> None:
    """List all known instances and their state."""
    inst.list_all()
