from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Protocol

from src.utils.http import HttpClient
from src.utils.normalizers import normalize_doi, normalize_pmcid, normalize_pmid


EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class TextHttpClient(Protocol):
    def get_text(self, url: str, params: dict[str, object | None]) -> str:
        ...


@dataclass(frozen=True)
class PubMedResult:
    papers: list[dict[str, object]]
    pmids: list[str]


class PubMedCollector:
    def __init__(
        self,
        *,
        email: str | None = None,
        api_key: str | None = None,
        tool: str = "paper_analysis",
        http_client: TextHttpClient | None = None,
    ) -> None:
        self.email = email or os.getenv("PUBMED_EMAIL")
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self.tool = tool
        self.http_client = http_client or HttpClient()

    def collect_by_keyword(self, query: str, *, limit: int = 20) -> PubMedResult:
        pmids = self.search_pmids(query, limit=limit)
        if not pmids:
            return PubMedResult(papers=[], pmids=[])
        xml_text = self.fetch_articles(pmids)
        return PubMedResult(papers=parse_pubmed_articles(xml_text), pmids=pmids)

    def search_pmids(self, query: str, *, limit: int = 20) -> list[str]:
        xml_text = self.http_client.get_text(
            f"{EUTILS_BASE_URL}/esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "xml",
                "retmax": limit,
                "sort": "pub date",
                "tool": self.tool,
                "email": self.email,
                "api_key": self.api_key,
            },
        )
        root = ET.fromstring(xml_text)
        return [
            pmid
            for pmid in (normalize_pmid(node.text) for node in root.findall("./IdList/Id"))
            if pmid is not None
        ]

    def fetch_articles(self, pmids: list[str]) -> str:
        return self.http_client.get_text(
            f"{EUTILS_BASE_URL}/efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "tool": self.tool,
                "email": self.email,
                "api_key": self.api_key,
            },
        )


def parse_pubmed_articles(xml_text: str) -> list[dict[str, object]]:
    root = ET.fromstring(xml_text)
    articles = []
    for article_node in root.findall(".//PubmedArticle"):
        article = article_node.find("./MedlineCitation/Article")
        citation = article_node.find("./MedlineCitation")
        if article is None or citation is None:
            continue

        title = _text(article.find("./ArticleTitle"))
        if not title:
            continue

        pmid = normalize_pmid(_text(citation.find("./PMID")))
        journal = _text(article.find("./Journal/Title")) or _text(article.find("./Journal/ISOAbbreviation"))
        publication_date, year = _publication_date(article)
        doi, pmcid = _article_ids(article_node)

        articles.append(
            {
                "title": title,
                "abstract": _abstract_text(article),
                "authors": _authors(article),
                "affiliations": _affiliations(article),
                "journal": journal,
                "publication_date": publication_date,
                "year": year,
                "doi": doi,
                "pmid": pmid,
                "pmcid": pmcid,
                "language": _language(article),
                "abstract_status": "fetched" if _abstract_text(article) else "missing",
            }
        )
    return articles


def _article_ids(article_node: ET.Element) -> tuple[str | None, str | None]:
    doi = None
    pmcid = None
    for id_node in article_node.findall("./PubmedData/ArticleIdList/ArticleId"):
        id_type = (id_node.attrib.get("IdType") or "").casefold()
        if id_type == "doi":
            doi = normalize_doi(id_node.text)
        elif id_type == "pmc":
            pmcid = normalize_pmcid(id_node.text)
    return doi, pmcid


def _abstract_text(article: ET.Element) -> str | None:
    parts = []
    for node in article.findall("./Abstract/AbstractText"):
        label = node.attrib.get("Label")
        text = _text(node)
        if not text:
            continue
        parts.append(f"{label}: {text}" if label else text)
    return "\n".join(parts) if parts else None


def _authors(article: ET.Element) -> str | None:
    names = []
    for author in article.findall("./AuthorList/Author"):
        collective = _text(author.find("./CollectiveName"))
        if collective:
            names.append(collective)
            continue
        last_name = _text(author.find("./LastName"))
        initials = _text(author.find("./Initials"))
        if last_name and initials:
            names.append(f"{last_name} {initials}")
        elif last_name:
            names.append(last_name)
    return "; ".join(names) if names else None


def _affiliations(article: ET.Element) -> str | None:
    affiliations = []
    for node in article.findall(".//AffiliationInfo/Affiliation"):
        value = _text(node)
        if value and value not in affiliations:
            affiliations.append(value)
    return " | ".join(affiliations) if affiliations else None


def _publication_date(article: ET.Element) -> tuple[str | None, int | None]:
    date_node = article.find("./Journal/JournalIssue/PubDate")
    if date_node is None:
        return None, None
    year_text = _text(date_node.find("./Year"))
    medline_date = _text(date_node.find("./MedlineDate"))
    year = _parse_year(year_text or medline_date)
    month = _text(date_node.find("./Month"))
    day = _text(date_node.find("./Day"))
    parts = [part for part in (year_text, month, day) if part]
    return (" ".join(parts) if parts else medline_date, year)


def _parse_year(value: str | None) -> int | None:
    if not value:
        return None
    for token in value.replace("-", " ").split():
        if token.isdigit() and len(token) == 4:
            return int(token)
    return None


def _language(article: ET.Element) -> str:
    language = (_text(article.find("./Language")) or "").casefold()
    if language == "eng":
        return "en"
    if language in {"chi", "zho"}:
        return "zh"
    return "unknown"


def _text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    text = "".join(node.itertext()).strip()
    return " ".join(text.split()) if text else None
