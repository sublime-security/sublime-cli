"""Sublime command line Interface."""

import logging
import sys

import click
import structlog
from click_default_group import DefaultGroup
from click_repl import register_repl

from sublime.cli import subcommand


def configure_logging():
    """Configure logging."""
    logging.basicConfig(stream=sys.stderr, format="%(message)s", level=logging.CRITICAL)
    logging.getLogger("sublime").setLevel(logging.WARNING)
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@click.group(
    cls=DefaultGroup,
    # default="query",
    default_if_no_args=False,
    context_settings={"help_option_names": ("-h", "--help")},
)
def main():
    """Sublime CLI."""
    configure_logging()


SUBCOMMAND_FUNCTIONS = [
    subcommand_function
    for subcommand_function in vars(subcommand).values()
    if isinstance(subcommand_function, click.Command)
]

for subcommand_function in SUBCOMMAND_FUNCTIONS:
    main.add_command(subcommand_function)

SUBCOMMAND_GROUPS = []
for sub in ():
    SUBCOMMAND_GROUPS.extend(
        subcommand_group
        for subcommand_group in vars(sub).values()
        if isinstance(subcommand_group, click.Group)
    )

for subcommand_group in SUBCOMMAND_GROUPS:
    main.add_command(subcommand_group)

register_repl(main)
main()
