"""Stream type classes for tap-userflow."""

from __future__ import annotations

from tap_userflow.client import UserFlowStream


class UsersStream(UserFlowStream):
    """User stream."""

    name = "users"
    path = "/users"
    expand = ("memberships",)


class GroupsStream(UserFlowStream):
    """Group stream."""

    name = "groups"
    path = "/groups"
    expand = ("memberships",)


class ContentsStream(UserFlowStream):
    """Content stream.

    Content is a common term for flows, checklists and launchers.
    """

    name = "content"
    path = "/content"
    expand = ("draft_version", "published_version")

    def get_child_context(self, record: dict, context: dict | None) -> dict | None:  # noqa: ARG002
        """This will be called for every record and a new child stream started with this context."""  # noqa: E501
        return {"content_id": record["id"]}


class ContentVersionsStream(UserFlowStream):
    """Content versions stream.

    This is a substream of Content
    """

    parent_stream_type = ContentsStream
    ignore_parent_replication_key = True
    sorting_keys = ("number",)
    name = "content_versions"
    path = "/content_versions?content_id={content_id}"
    expand = ("tasks", "questions")


class ContentSessionsStream(UserFlowStream):
    """Content Sessions stream.

    A session is a specific user's journey through a specific
    content object (flow, checklist or launcher).
    It tracks their progress and records survey answers they provide.

    Although it doesn't have to be, this stream is a child stream of ContentsStream.
    If your account has very many content_sessions,
    then the server may time out ang give HTTP 500.
    This was recommended by Userflow staff.
    """

    parent_stream_type = ContentsStream
    ignore_parent_replication_key = True

    name = "content_sessions"
    sorting_key = ("last_activity_at", "created_at")
    path = "/content_sessions?content_id={content_id}"
    expand = ("answers", "content", "group", "version")


class AttributeDefinitionsStream(UserFlowStream):
    """Attribute Definitions stream."""

    name = "attribute_definitions"
    path = "/attribute_definitions"


class EventDefinitionsStream(UserFlowStream):
    """Event Definitions stream."""

    name = "event_definitions"
    path = "/event_definitions"


STREAMS = [
    UsersStream,
    GroupsStream,
    ContentsStream,
    ContentVersionsStream,
    ContentSessionsStream,
    AttributeDefinitionsStream,
    EventDefinitionsStream,
]
