"""Tests standard tap features using the built-in SDK tests library."""


import os

from singer_sdk.testing import get_tap_test_class

from tap_userflow.tap import TapUserFlow

SAMPLE_CONFIG = {"auth_token": os.environ["TAP_USERFLOW_AUTH_TOKEN"], "limit": 1}


# Run standard built-in tap tests from the SDK:
TestTapUserFlow = get_tap_test_class(
    tap_class=TapUserFlow,
    config=SAMPLE_CONFIG,
)
