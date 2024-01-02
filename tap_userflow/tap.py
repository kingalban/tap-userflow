"""UserFlow tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_userflow import streams
import importlib.metadata


class TapUserFlow(Tap):
    """UserFlow tap class."""

    name = "tap-userflow"
    plugin_version = importlib.metadata.version("kingalban-tap-userflow")

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "user_agent",
            th.StringType,
            default="Singer.io Tap",
            description="The user agent to present to the API",
        ),
        th.Property(
            "limit",
            th.IntegerType,
            default=None,
            description="Limit items per stream",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.UserFlowStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [stream(self) for stream in streams.STREAMS]


if __name__ == "__main__":
    TapUserFlow.cli()
