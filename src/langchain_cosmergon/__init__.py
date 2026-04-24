"""langchain-cosmergon — Cosmergon economy as LangChain-compatible tools.

Usage::

    from langchain_cosmergon import cosmergon_tools

    tools = cosmergon_tools(player_token="CSMR-...")

See README for full quickstart.
"""

from langchain_cosmergon.tools import cosmergon_tools
from langchain_cosmergon.version import __version__

__all__ = ["cosmergon_tools", "__version__"]
