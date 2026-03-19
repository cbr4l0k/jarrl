from jarrl.bot import (
    format_add_result,
    format_error_response,
    is_allowed_user,
    is_http_url,
)


def test_format_add_result_created():
    assert format_add_result(
        created=True, title="Example title", url="https://example.com/article"
    ) == "Added: Example title"


def test_format_error_response():
    assert format_error_response("parse failed") == "Could not add URL: parse failed"


def test_is_http_url():
    assert is_http_url("https://example.com/article") is True
    assert is_http_url("ftp://example.com/article") is False


def test_is_allowed_user():
    assert is_allowed_user(sender_user_id=123, allowed_user_id=123) is True
    assert is_allowed_user(sender_user_id=123, allowed_user_id=456) is False
    assert is_allowed_user(sender_user_id=None, allowed_user_id=123) is False
