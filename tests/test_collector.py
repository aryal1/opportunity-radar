from unittest.mock import Mock, patch

import pytest
import requests

from opportunity_radar.collector import fetch_page


def test_fetch_page_returns_html():
    mock_response = Mock()
    mock_response.text = "<html>Hello World</html>"

    with patch(
        "opportunity_radar.collector.requests.get",
        return_value=mock_response,
    ) as mock_get:
        result = fetch_page("https://example.com")

    assert result == "<html>Hello World</html>"
    mock_get.assert_called_once_with(
        "https://example.com",
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once()

def test_fetch_page_raises_on_http_error():
    mock_response = Mock()
    mock_response.text = "<html>Hello World</html>"

    with pytest.raises(requests.exceptions.HTTPError), patch(
        "opportunity_radar.collector.requests.get",
        return_value=mock_response,
    ):
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        fetch_page("https://example.com")
