import requests

def fetch_page(url: str) -> str:
    """
    Fetch the HTML content of a webpage.

    Args:
        url: The URL to retrieve.

    Returns:
        The HTML content as a string.

    Raises:
        requests.exceptions.RequestException:
            If the HTTP request fails.
    """

    response = requests.get(url, timeout=10)  # Set a timeout for the request
    response.raise_for_status()  # Raise an error for bad responses

    if "Incapsula incident ID" in response.text:
        raise RuntimeError("Website blocked automated access")

    return response.text