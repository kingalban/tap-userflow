"""REST client handling, including UserFlowStream base class."""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs

import requests
from singer_sdk.authenticators import BearerTokenAuthenticator
from singer_sdk.helpers._typing import TypeConformanceLevel
from singer_sdk.pagination import JSONPathPaginator
from singer_sdk.streams import RESTStream

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")
API_VERSION = "2020-01-03"
MAX_PAGE_SIZE = 100


class StartingAfterPaginator(JSONPathPaginator):
    """Paginate over 'starting_after' in responses."""

    def __init__(
        self,
        jsonpath: str,
        limit: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create a new paginator.

        Args:
            jsonpath: A JSONPath expression.
            limit: Stop paginating after this limit. Useful for testing.
            args: Paginator positional arguments for base class.
            kwargs: Paginator keyword arguments for base class.
        """
        self.limit = limit
        super().__init__(jsonpath, *args, **kwargs)

    def get_next(self, response: requests.Response) -> str | None:
        """Get the next page token.

        Args:
            response: API response object.

        Returns:
            The next page token.
        """
        resp_json = response.json()

        if not resp_json.get("has_more") or (self.limit and self.count > self.limit):
            return None

        next_path = resp_json.get("next_page_url")
        return parse_qs(next_path)["starting_after"][0]


class UserFlowStream(RESTStream):
    """UserFlow stream class."""

    is_sorted = True
    check_sorted = False  # streams are sorted by date, but not by replication_key.
    records_jsonpath = "$.data[*]"
    next_page_token_jsonpath = "$.next_page_url"  # noqa: S105

    url_base = "https://api.userflow.com"

    sorting_key = "created_at"
    primary_keys = ("id",)
    replication_key = "id"
    expand = None

    # the 'attributes' property contains arbitrary keys
    TYPE_CONFORMANCE_LEVEL = TypeConformanceLevel.ROOT_ONLY

    @property
    def schema_filepath(self) -> Path | None:
        """Get path to schema file.

        Returns:
            Path to a schema file for the stream or `None` if n/a.
        """
        return SCHEMAS_DIR / f"{self.name}.schema.json"

    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return BearerTokenAuthenticator.create_for_stream(
            self,
            token=self.config.get("auth_token", ""),
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        headers = {"Userflow-Version": API_VERSION}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_new_paginator(self) -> StartingAfterPaginator:
        """Create a new pagination helper instance.

        If the source API can make use of the `next_page_token_jsonpath`
        attribute, or it contains a `X-Next-Page` header in the response
        then you can remove this method.

        If you need custom pagination that uses page numbers, "next" links, or
        other approaches, please read the guide:
        https://sdk.meltano.com/en/v0.25.0/guides/pagination-classes.html.

        Returns:
            A pagination helper instance.
        """
        return StartingAfterPaginator(
            self.next_page_token_jsonpath, self.config.get("limit")
        )

    def get_starting_replication_key_value(
        self,
        context: dict | None,
    ) -> Any | None:  # noqa: ANN401
        """Get the latest key from the state or None."""
        state = self.get_context_state(context)
        return state.get("starting_replication_value")

    def get_url_params(
        self,
        context: dict | None,
        next_page_token: Any | None,  # noqa: ANN401
    ) -> dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The next page index or value
                (as returned by get_new_paginator().current_value)

        Returns:
            A dictionary of URL query parameters.
        """
        params: dict = {}

        if next_page_token:
            params["starting_after"] = next_page_token
        else:
            params["starting_after"] = self.get_starting_replication_key_value(context)

        if self.sorting_key:
            key = "order_by[]" if isinstance(self.sorting_key, (tuple, list)) else "order_by"
            params["sort"] = "asc"
            params[key] = self.sorting_key

        params["limit"] = MAX_PAGE_SIZE

        if self.config.get("limit") and self.config.get("limit") <= MAX_PAGE_SIZE:
            params["limit"] = self.config.get("limit")

        if self.expand:
            key = "expand[]" if isinstance(self.expand, (list, tuple)) else "expand"
            params[key] = self.expand

        return params

    def response_error_message(self, response: requests.Response) -> str:
        """Build an error message from the response, including detailed message."""
        detailed_message = ""

        for key in ("code", "message"):
            with contextlib.suppress(requests.exceptions.JSONDecodeError, KeyError):
                detailed_message += f"{key}={response.json()['error'][key]!r}, "

        detailed_message += f"url: {response.url!r}"

        super_message = super().response_error_message(response)
        return f"{super_message} ({detailed_message})"
