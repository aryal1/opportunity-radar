
from bs4 import BeautifulSoup


def extract_text(html: str) -> str:
    """
    Extract readable text from an HTML document.

    Args:
        html: Raw HTML content.

    Returns:
        Cleaned text extracted from the document.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that don't contain useful article content
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Extract text and remove unnecessary whitespace
    text = soup.get_text(separator=" ", strip=True)

    return text
