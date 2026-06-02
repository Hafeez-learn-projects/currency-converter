"""Unit tests for currency_converter core logic."""

import pytest
from currency_converter import handle_error


def test_handle_error_success():
    assert handle_error({"result": "success"}) is False


def test_handle_error_failure():
    assert handle_error({"result": "error"}) is True


def test_handle_error_unknown():
    assert handle_error({}) is False