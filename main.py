import re
import requests
from bs4 import BeautifulSoup

URL = "https://justjoin.it/job-offers/krakow/testing"
TITLE_SELECTOR = "a.offer_list_offer_title_link"
MAX_OFFERS = 10


def get_salary(text):
    text = (
        text.replace("\xa0", " ")
            .replace("\u202f", " ")
            .replace("–", "-")
            .replace("—", "-")
    )
    text = re.sub(r"\s+", " ", text)

    amount = r"\d+(?:[ ]\d{3})*(?:[.,]\d+)?"

    # Przykłady: 70 - 85 PLN/h, 16 000 - 27 000 PLN/month
    match = re.search(
        rf"(?P<low>{amount})\s*-\s*(?P<high>{amount})"
        rf"\s*PLN\s*/\s*(?P<unit>h|month)\b",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return "brak podanej stawki"

    low = match.group("low").strip()
    high = match.group("high").strip()
    unit = match.group("unit").lower()

    return f"{low} - {high} PLN/{unit}"

def get_technologies(soup):
    container = soup.select_one("div.MuiBox-root.mui-lo8b6p")
    if not container:
        return []

    technologies = []
    for element in container.select("div.MuiBox-root"):
        name = element.get_text(strip=True)
        if name and name not in technologies:
            technologies.append(name)

    return technologies






headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(URL, headers=headers, timeout=20)
    response.raise_for_status()
except requests.RequestException as error:
    print(f"Nie udało się pobrać strony: {error}")
    raise SystemExit(1)

soup = BeautifulSoup(response.text, "html.parser")
title_links = soup.select(TITLE_SELECTOR)

if not title_links:
    print("Nie znaleziono ofert w HTML-u zwróconym przez serwer.")
    print("Strona może doładowywać oferty dopiero przez JavaScript.")
    print(f"Pobrany HTML ma {len(response.text)} znaków.")
    raise SystemExit(0)

print(f"Znaleziono w HTML-u {len(title_links)} linków do ofert.\n")

for number, link in enumerate(title_links[:MAX_OFFERS], start=1):
    title = link.get_text(" ", strip=True)

    # Znajdujemy wspólny kontener oferty, który zawiera także jej link.
    offer_card = None

    for parent in link.parents:
        if parent.select_one("a.offer-card"):
            offer_card = parent
            break

    # Zapasowy wariant oparty na strukturze podanego HTML-u.
    if offer_card is None:
        offer_card = link.parent.parent.parent.parent

    offer_text = offer_card.get_text(" ", strip=True)

    salary = get_salary(offer_text)
    technologies = get_technologies(soup)

    print(f"{number}. {title}")
    print(f"   Wynagrodzenie: {salary}")
    print(f"   Technologie: {technologies}\n")

