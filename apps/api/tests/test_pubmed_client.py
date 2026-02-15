from app.services.pubmed_client import _parse_articles

SAMPLE_XML = """<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345</PMID>
      <Article>
        <ArticleTitle>Test Article</ArticleTitle>
        <Abstract><AbstractText>Test abstract.</AbstractText></Abstract>
        <AuthorList>
          <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
          <Author><LastName>Doe</LastName><ForeName>Jane</ForeName></Author>
        </AuthorList>
        <Journal><JournalIssue><PubDate><Year>2024</Year><Month>Mar</Month></PubDate></JournalIssue></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""

STRUCTURED_ABSTRACT_XML = """<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>67890</PMID>
      <Article>
        <ArticleTitle>Structured Abstract Article</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Background text.</AbstractText>
          <AbstractText Label="METHODS">Methods text.</AbstractText>
          <AbstractText Label="RESULTS">Results text.</AbstractText>
        </Abstract>
        <AuthorList><Author><LastName>Lee</LastName></Author></AuthorList>
        <Journal><JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""

MISSING_FIELDS_XML = """<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999</PMID>
      <Article>
        <ArticleTitle></ArticleTitle>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


def test_parse_basic_article():
    results = _parse_articles(SAMPLE_XML)
    assert len(results) == 1
    art = results[0]
    assert art["pmid"] == "12345"
    assert art["title"] == "Test Article"
    assert art["authors"] == ["Smith John", "Doe Jane"]
    assert art["abstract"] == "Test abstract."
    assert art["pub_date"] == "2024 Mar"


def test_parse_structured_abstract():
    results = _parse_articles(STRUCTURED_ABSTRACT_XML)
    assert len(results) == 1
    assert results[0]["abstract"] == "Background text. Methods text. Results text."


def test_parse_missing_fields():
    results = _parse_articles(MISSING_FIELDS_XML)
    assert len(results) == 1
    art = results[0]
    assert art["pmid"] == "99999"
    assert art["title"] == ""
    assert art["authors"] == []
    assert art["abstract"] == ""
    assert art["pub_date"] == ""


def test_parse_empty_xml():
    assert _parse_articles("<PubmedArticleSet></PubmedArticleSet>") == []


def test_parse_invalid_xml():
    assert _parse_articles("not xml at all") == []
