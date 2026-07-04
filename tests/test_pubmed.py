from __future__ import annotations

from src.cli import main
from src.collectors.pubmed import PubMedCollector, parse_pubmed_articles


PUBMED_SEARCH_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<eSearchResult>
  <IdList>
    <Id>12345678</Id>
  </IdList>
</eSearchResult>
"""


PUBMED_FETCH_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal>
          <Title>Example Journal</Title>
          <JournalIssue>
            <PubDate>
              <Year>2025</Year>
              <Month>Jan</Month>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>BRGSF mouse model from genOway</ArticleTitle>
        <Abstract>
          <AbstractText Label="Methods">The humanized mouse model was supplied by genOway.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Smith</LastName>
            <Initials>AB</Initials>
          </Author>
        </AuthorList>
        <Language>eng</Language>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1234/ABC.</ArticleId>
        <ArticleId IdType="pmc">PMC999999</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class FakePubMedHttpClient:
    def get_text(self, url, params):
        if url.endswith("esearch.fcgi"):
            return PUBMED_SEARCH_XML
        if url.endswith("efetch.fcgi"):
            return PUBMED_FETCH_XML
        raise AssertionError(f"unexpected URL: {url}")


def test_parse_pubmed_articles_maps_core_fields():
    papers = parse_pubmed_articles(PUBMED_FETCH_XML)

    assert papers == [
        {
            "title": "BRGSF mouse model from genOway",
            "abstract": "Methods: The humanized mouse model was supplied by genOway.",
            "authors": "Smith AB",
            "journal": "Example Journal",
            "publication_date": "2025 Jan",
            "year": 2025,
            "doi": "10.1234/abc",
            "pmid": "12345678",
            "pmcid": "PMC999999",
            "language": "en",
            "abstract_status": "fetched",
        }
    ]


def test_pubmed_collector_collects_by_keyword_without_network():
    collector = PubMedCollector(http_client=FakePubMedHttpClient())

    result = collector.collect_by_keyword("genOway", limit=1)

    assert result.pmids == ["12345678"]
    assert result.papers[0]["pmid"] == "12345678"
    assert result.papers[0]["doi"] == "10.1234/abc"


def test_collect_pubmed_cli_inserts_and_deduplicates(monkeypatch, tmp_path, capsys):
    db_path = tmp_path / "paper_analysis.sqlite"

    def fake_collector():
        return PubMedCollector(http_client=FakePubMedHttpClient())

    monkeypatch.setattr("src.cli.PubMedCollector", fake_collector)

    assert (
        main(
            [
                "--db",
                str(db_path),
                "collect",
                "abstracts",
                "--source",
                "pubmed",
                "--query",
                "genOway",
                "--limit",
                "1",
            ]
        )
        == 0
    )
    first_output = capsys.readouterr().out

    assert (
        main(
            [
                "--db",
                str(db_path),
                "collect",
                "abstracts",
                "--source",
                "pubmed",
                "--query",
                "genOway",
                "--limit",
                "1",
            ]
        )
        == 0
    )
    second_output = capsys.readouterr().out

    assert "created=1, updated=0" in first_output
    assert "created=0, updated=1" in second_output

    assert main(["--db", str(db_path), "status", "keywords", "--json"]) == 0
    keyword_output = capsys.readouterr().out
    assert '"keyword": "genOway"' in keyword_output
    assert '"keyword": "BRGSF"' in keyword_output
