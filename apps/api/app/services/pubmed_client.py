from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx
from fastapi import Request

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _parse_articles(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    articles = []
    for article_el in root.findall(".//PubmedArticle"):
        citation = article_el.find(".//MedlineCitation")
        if citation is None:
            continue

        pmid_el = citation.find("PMID")
        pmid = pmid_el.text if pmid_el is not None and pmid_el.text else ""

        art = citation.find("Article")
        title = ""
        abstract = ""
        authors: list[str] = []
        pub_date = ""

        if art is not None:
            title_el = art.find("ArticleTitle")
            title = title_el.text if title_el is not None and title_el.text else ""

            abstract_texts = art.findall(".//AbstractText")
            abstract = " ".join(
                (at.text or "") for at in abstract_texts
            ).strip()

            for author in art.findall(".//Author"):
                last = author.find("LastName")
                fore = author.find("ForeName")
                if last is not None and last.text:
                    name = last.text
                    if fore is not None and fore.text:
                        name += " " + fore.text
                    authors.append(name)

            pub_date_el = art.find(".//PubDate")
            if pub_date_el is not None:
                year = pub_date_el.find("Year")
                month = pub_date_el.find("Month")
                parts = []
                if year is not None and year.text:
                    parts.append(year.text)
                if month is not None and month.text:
                    parts.append(month.text)
                pub_date = " ".join(parts)

        articles.append({
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "pub_date": pub_date,
        })

    return articles


class PubMedClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def search(self, query: str, max_results: int = 20) -> list[dict]:
        try:
            esearch_resp = await self._client.get(
                f"{BASE_URL}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                },
            )
            esearch_resp.raise_for_status()
            data = esearch_resp.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return []

            efetch_resp = await self._client.get(
                f"{BASE_URL}/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "xml",
                },
            )
            efetch_resp.raise_for_status()
            return _parse_articles(efetch_resp.text)
        except httpx.HTTPError:
            return []

    async def fetch_by_pmid(self, pmid: str) -> dict | None:
        resp = await self._client.get(
            f"{BASE_URL}/efetch.fcgi",
            params={"db": "pubmed", "id": pmid, "retmode": "xml"},
        )
        resp.raise_for_status()
        articles = _parse_articles(resp.text)
        return articles[0] if articles else None


def get_pubmed_client(request: Request) -> PubMedClient:
    return PubMedClient(request.app.state.http_client)
