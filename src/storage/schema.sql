PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS papers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  normalized_title TEXT NOT NULL,
  abstract TEXT,
  authors TEXT,
  journal TEXT,
  publication_date TEXT,
  year INTEGER,
  doi TEXT,
  pmid TEXT,
  pmcid TEXT,
  language TEXT NOT NULL DEFAULT 'unknown',
  region_relevance TEXT NOT NULL DEFAULT 'unknown',
  discovery_status TEXT NOT NULL DEFAULT 'discovered',
  abstract_status TEXT NOT NULL DEFAULT 'not_checked',
  fulltext_status TEXT NOT NULL DEFAULT 'not_checked',
  parse_status TEXT NOT NULL DEFAULT 'not_started',
  analysis_status TEXT NOT NULL DEFAULT 'not_started',
  evidence_level TEXT NOT NULL DEFAULT 'unknown',
  reference_value TEXT NOT NULL DEFAULT 'unknown',
  review_status TEXT NOT NULL DEFAULT 'needs_review',
  fulltext_source TEXT,
  pdf_url TEXT,
  xml_url TEXT,
  landing_page_url TEXT,
  license TEXT,
  oa_status TEXT,
  manual_upload INTEGER NOT NULL DEFAULT 0,
  manual_override INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_checked_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi_unique
ON papers(doi)
WHERE doi IS NOT NULL AND doi != '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_pmid_unique
ON papers(pmid)
WHERE pmid IS NOT NULL AND pmid != '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_pmcid_unique
ON papers(pmcid)
WHERE pmcid IS NOT NULL AND pmcid != '';

CREATE INDEX IF NOT EXISTS idx_papers_normalized_title
ON papers(normalized_title);

CREATE TABLE IF NOT EXISTS paper_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  source_record_id TEXT,
  query_keyword TEXT,
  source_url TEXT,
  raw_json_path TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(paper_id, source, source_record_id)
);

CREATE TABLE IF NOT EXISTS paper_fulltexts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,
  source_url TEXT,
  local_path TEXT,
  file_type TEXT,
  sha256_hash TEXT,
  license TEXT,
  downloaded_at TEXT,
  parse_quality TEXT,
  raw_text_path TEXT,
  parsed_json_path TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(paper_id, sha256_hash)
);

CREATE TABLE IF NOT EXISTS paper_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  evidence_type TEXT NOT NULL,
  evidence_level TEXT NOT NULL,
  evidence_sentence TEXT NOT NULL,
  section_name TEXT,
  model_name TEXT,
  model_type TEXT,
  target TEXT,
  disease_area TEXT,
  application_scenario TEXT,
  institution TEXT,
  country_or_region TEXT,
  confidence_score REAL,
  needs_review INTEGER NOT NULL DEFAULT 1,
  source_type TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(paper_id, evidence_type, evidence_sentence)
);

CREATE TABLE IF NOT EXISTS paper_keyword_hits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  keyword TEXT NOT NULL,
  keyword_group TEXT NOT NULL,
  matched_text TEXT NOT NULL,
  matched_field TEXT NOT NULL,
  evidence_sentence TEXT,
  source_config TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(paper_id, keyword, keyword_group, matched_field, evidence_sentence)
);

CREATE INDEX IF NOT EXISTS idx_paper_keyword_hits_keyword
ON paper_keyword_hits(keyword);

CREATE INDEX IF NOT EXISTS idx_paper_keyword_hits_group
ON paper_keyword_hits(keyword_group);

CREATE TABLE IF NOT EXISTS paper_external_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  link_type TEXT NOT NULL,
  url TEXT NOT NULL,
  source TEXT,
  is_open_access INTEGER,
  license TEXT,
  link_status TEXT NOT NULL DEFAULT 'unchecked',
  user_opened INTEGER NOT NULL DEFAULT 0,
  user_note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(paper_id, link_type, url)
);

CREATE TABLE IF NOT EXISTS manual_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  note TEXT NOT NULL,
  reviewer TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_status_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  changed_by TEXT NOT NULL DEFAULT 'system',
  change_source TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
