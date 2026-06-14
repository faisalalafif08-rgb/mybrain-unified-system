#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full SQLite Database Initializer for the unified AI system.

Creates all approved database files:
- C:\\unified_ai_system\\02_data_warehouse\\databases\\*.db
- C:\\Amal.X\\z3eem_GPT\\database\\project_factory.db

Rules:
- review_required = 1
- gold_write = 0
- no direct execution policy is represented in the registry/policy tables
- all operational records default to pending/pending_review
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

UNIFIED_ROOT = Path(r"C:\unified_ai_system")
Z3EEM_ROOT = Path(r"C:\Amal.X\z3eem_GPT")
DB_DIR = UNIFIED_ROOT / "02_data_warehouse" / "databases"
Z3EEM_DB_DIR = Z3EEM_ROOT / "database"
REPORT_DIR = UNIFIED_ROOT / "07_runtime" / "database_init" / "reports"

COMMON_PRAGMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA encoding = 'UTF-8';
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 30000;
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.executescript(COMMON_PRAGMA)
    return con


def apply_schema(db_path: Path, schema: str) -> dict:
    con = connect(db_path)
    try:
        con.executescript(schema)
        con.commit()
        tables = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name"
            ).fetchall()
        ]
        return {"database": str(db_path), "status": "ok", "objects": tables, "count": len(tables)}
    finally:
        con.close()


SYSTEM_LIGHT_CORE_SQL = """
CREATE TABLE IF NOT EXISTS raw_inputs (
    input_id TEXT PRIMARY KEY,
    input_type TEXT NOT NULL,
    raw_text TEXT,
    file_path TEXT,
    source_id TEXT,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS input_registry (
    registry_id TEXT PRIMARY KEY,
    input_id TEXT NOT NULL,
    detected_type TEXT,
    routing_status TEXT DEFAULT 'pending',
    payload_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(input_id) REFERENCES raw_inputs(input_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS processing_queue (
    queue_id TEXT PRIMARY KEY,
    input_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 100,
    attempts INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(input_id) REFERENCES raw_inputs(input_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS extraction_results (
    result_id TEXT PRIMARY KEY,
    input_id TEXT NOT NULL,
    extracted_text TEXT,
    extracted_json TEXT,
    confidence REAL DEFAULT 0.0,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(input_id) REFERENCES raw_inputs(input_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS word_inventory (
    word_id TEXT PRIMARY KEY,
    language_code TEXT DEFAULT 'ar',
    original_word TEXT NOT NULL,
    normalized_word TEXT,
    search_key TEXT,
    seq_2 TEXT,
    seq_3 TEXT,
    seq_4 TEXT,
    source_id TEXT,
    review_status TEXT DEFAULT 'pending_review',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS input_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_id TEXT NOT NULL,
    word_id TEXT NOT NULL,
    position_index INTEGER,
    surface_form TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(input_id) REFERENCES raw_inputs(input_id) ON DELETE CASCADE,
    FOREIGN KEY(word_id) REFERENCES word_inventory(word_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS word_meanings (
    meaning_id TEXT PRIMARY KEY,
    word_id TEXT NOT NULL,
    meaning_text TEXT NOT NULL,
    meaning_source TEXT,
    confidence REAL DEFAULT 0.0,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(word_id) REFERENCES word_inventory(word_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS phrase_patterns (
    pattern_id TEXT PRIMARY KEY,
    language_code TEXT DEFAULT 'ar',
    pattern_text TEXT NOT NULL,
    intent_label TEXT,
    example_text TEXT,
    review_status TEXT DEFAULT 'pending_review',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS source_registry (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_type TEXT,
    source_path TEXT,
    trusted_level TEXT DEFAULT 'unknown',
    review_status TEXT DEFAULT 'pending_review',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS review_queue (
    review_id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    reviewer TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS correction_rules (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT,
    match_text TEXT NOT NULL,
    replacement_text TEXT,
    language_code TEXT DEFAULT 'ar',
    confidence REAL DEFAULT 0.0,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS memory_candidates (
    candidate_id TEXT PRIMARY KEY,
    source_item_type TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    memory_layer TEXT DEFAULT 'bronze',
    payload_json TEXT,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
DROP VIEW IF EXISTS light_core_status_view;
CREATE VIEW light_core_status_view AS
SELECT
    ri.input_id,
    ri.input_type,
    COALESCE(i.routing_status, 'not_registered') AS routing_status,
    COALESCE(p.status, 'not_queued') AS processing_status,
    CASE
        WHEN rq.review_id IS NOT NULL THEN 'needs_review'
        WHEN er.result_id IS NOT NULL THEN 'extracted'
        WHEN p.status = 'completed' THEN 'processed'
        ELSE 'entered'
    END AS system_status,
    ri.review_status,
    ri.gold_write,
    ri.created_at
FROM raw_inputs ri
LEFT JOIN input_registry i ON i.input_id = ri.input_id
LEFT JOIN processing_queue p ON p.input_id = ri.input_id
LEFT JOIN extraction_results er ON er.input_id = ri.input_id
LEFT JOIN review_queue rq ON rq.item_id = ri.input_id;
CREATE INDEX IF NOT EXISTS idx_word_inventory_search ON word_inventory(search_key, seq_2, seq_3, seq_4);
"""


LANGUAGE_CORE_SQL = """
CREATE TABLE IF NOT EXISTS Arabic_Words (
    Arabic_word_ID TEXT PRIMARY KEY,
    original_word TEXT NOT NULL,
    normalized_word TEXT,
    search_key_strict TEXT,
    search_key_loose TEXT,
    seq_2 TEXT,
    seq_3 TEXT,
    seq_4 TEXT,
    word_status TEXT DEFAULT 'pending_review',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS Arabic_Word_Meanings (
    Arabic_meaning_ID TEXT PRIMARY KEY,
    Arabic_word_ID TEXT NOT NULL,
    meaning_short_ar TEXT,
    meaning_full_ar TEXT,
    source_id TEXT,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    FOREIGN KEY(Arabic_word_ID) REFERENCES Arabic_Words(Arabic_word_ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Arabic_Word_Features (
    feature_id TEXT PRIMARY KEY,
    Arabic_word_ID TEXT NOT NULL,
    word_type TEXT DEFAULT 'غير معروف',
    gender TEXT DEFAULT 'غير معروف',
    number_value TEXT DEFAULT 'غير معروف',
    root TEXT,
    pattern TEXT,
    morphology TEXT,
    review_status TEXT DEFAULT 'pending_review',
    FOREIGN KEY(Arabic_word_ID) REFERENCES Arabic_Words(Arabic_word_ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Arabic_Grammar_Rules (
    rule_id TEXT PRIMARY KEY,
    rule_name_ar TEXT NOT NULL,
    rule_category TEXT,
    condition_text_ar TEXT,
    effect_text_ar TEXT,
    examples_ar TEXT,
    priority INTEGER DEFAULT 100,
    review_status TEXT DEFAULT 'pending_review'
);
CREATE TABLE IF NOT EXISTS Arabic_Word_Grammar_Rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Arabic_word_ID TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    relation_type TEXT DEFAULT 'applies_to',
    confidence REAL DEFAULT 0.0,
    FOREIGN KEY(Arabic_word_ID) REFERENCES Arabic_Words(Arabic_word_ID) ON DELETE CASCADE,
    FOREIGN KEY(rule_id) REFERENCES Arabic_Grammar_Rules(rule_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Arabic_Word_Sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Arabic_word_ID TEXT NOT NULL,
    source_id TEXT,
    source_ref TEXT,
    FOREIGN KEY(Arabic_word_ID) REFERENCES Arabic_Words(Arabic_word_ID) ON DELETE CASCADE
);
DROP VIEW IF EXISTS Arabic_Word_Cards_View;
CREATE VIEW Arabic_Word_Cards_View AS
SELECT w.Arabic_word_ID, w.original_word, w.normalized_word, f.word_type, f.gender, f.number_value, f.root, f.pattern, m.meaning_short_ar, w.word_status
FROM Arabic_Words w
LEFT JOIN Arabic_Word_Features f ON f.Arabic_word_ID = w.Arabic_word_ID
LEFT JOIN Arabic_Word_Meanings m ON m.Arabic_word_ID = w.Arabic_word_ID;

CREATE TABLE IF NOT EXISTS English_Words (
    English_word_ID TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    normalized_word TEXT,
    search_key_strict TEXT,
    search_key_loose TEXT,
    seq_2 TEXT,
    seq_3 TEXT,
    seq_4 TEXT,
    word_status TEXT DEFAULT 'pending_review',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS English_Word_Meanings (
    English_meaning_ID TEXT PRIMARY KEY,
    English_word_ID TEXT NOT NULL,
    definition_short_en TEXT,
    definition_full_en TEXT,
    source_id TEXT,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    FOREIGN KEY(English_word_ID) REFERENCES English_Words(English_word_ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS English_Word_Features (
    feature_id TEXT PRIMARY KEY,
    English_word_ID TEXT NOT NULL,
    part_of_speech TEXT DEFAULT 'unknown',
    number_value TEXT DEFAULT 'unknown',
    morphology TEXT,
    review_status TEXT DEFAULT 'pending_review',
    FOREIGN KEY(English_word_ID) REFERENCES English_Words(English_word_ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS English_Grammar_Rules (
    rule_id TEXT PRIMARY KEY,
    rule_name_en TEXT NOT NULL,
    rule_category TEXT,
    condition_text_en TEXT,
    effect_text_en TEXT,
    examples_en TEXT,
    priority INTEGER DEFAULT 100,
    review_status TEXT DEFAULT 'pending_review'
);
CREATE TABLE IF NOT EXISTS English_Word_Grammar_Rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    English_word_ID TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    relation_type TEXT DEFAULT 'applies_to',
    confidence REAL DEFAULT 0.0,
    FOREIGN KEY(English_word_ID) REFERENCES English_Words(English_word_ID) ON DELETE CASCADE,
    FOREIGN KEY(rule_id) REFERENCES English_Grammar_Rules(rule_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS English_Word_Sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    English_word_ID TEXT NOT NULL,
    source_id TEXT,
    source_ref TEXT,
    FOREIGN KEY(English_word_ID) REFERENCES English_Words(English_word_ID) ON DELETE CASCADE
);
DROP VIEW IF EXISTS English_Word_Cards_View;
CREATE VIEW English_Word_Cards_View AS
SELECT w.English_word_ID, w.word, w.normalized_word, f.part_of_speech, f.number_value, f.morphology, m.definition_short_en, w.word_status
FROM English_Words w
LEFT JOIN English_Word_Features f ON f.English_word_ID = w.English_word_ID
LEFT JOIN English_Word_Meanings m ON m.English_word_ID = w.English_word_ID;

CREATE TABLE IF NOT EXISTS French_Words (
    French_word_ID TEXT PRIMARY KEY,
    mot TEXT NOT NULL,
    forme_normalisee TEXT,
    search_key_strict TEXT,
    search_key_loose TEXT,
    seq_2 TEXT,
    seq_3 TEXT,
    seq_4 TEXT,
    statut TEXT DEFAULT 'pending_review',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS French_Word_Meanings (
    French_meaning_ID TEXT PRIMARY KEY,
    French_word_ID TEXT NOT NULL,
    definition_courte_fr TEXT,
    definition_complete_fr TEXT,
    source_id TEXT,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    FOREIGN KEY(French_word_ID) REFERENCES French_Words(French_word_ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS French_Word_Features (
    feature_id TEXT PRIMARY KEY,
    French_word_ID TEXT NOT NULL,
    categorie TEXT DEFAULT 'inconnu',
    genre TEXT DEFAULT 'inconnu',
    nombre TEXT DEFAULT 'inconnu',
    morphologie TEXT,
    review_status TEXT DEFAULT 'pending_review',
    FOREIGN KEY(French_word_ID) REFERENCES French_Words(French_word_ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS French_Grammar_Rules (
    rule_id TEXT PRIMARY KEY,
    rule_name_fr TEXT NOT NULL,
    rule_category TEXT,
    condition_text_fr TEXT,
    effect_text_fr TEXT,
    examples_fr TEXT,
    priority INTEGER DEFAULT 100,
    review_status TEXT DEFAULT 'pending_review'
);
CREATE TABLE IF NOT EXISTS French_Word_Grammar_Rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    French_word_ID TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    relation_type TEXT DEFAULT 'applies_to',
    confidence REAL DEFAULT 0.0,
    FOREIGN KEY(French_word_ID) REFERENCES French_Words(French_word_ID) ON DELETE CASCADE,
    FOREIGN KEY(rule_id) REFERENCES French_Grammar_Rules(rule_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS French_Word_Sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    French_word_ID TEXT NOT NULL,
    source_id TEXT,
    source_ref TEXT,
    FOREIGN KEY(French_word_ID) REFERENCES French_Words(French_word_ID) ON DELETE CASCADE
);
DROP VIEW IF EXISTS French_Word_Cards_View;
CREATE VIEW French_Word_Cards_View AS
SELECT w.French_word_ID, w.mot, w.forme_normalisee, f.categorie, f.genre, f.nombre, f.morphologie, m.definition_courte_fr, w.statut
FROM French_Words w
LEFT JOIN French_Word_Features f ON f.French_word_ID = w.French_word_ID
LEFT JOIN French_Word_Meanings m ON m.French_word_ID = w.French_word_ID;

CREATE TABLE IF NOT EXISTS Word_Translation_Links (
    link_id TEXT PRIMARY KEY,
    source_language TEXT NOT NULL,
    source_word_id TEXT NOT NULL,
    target_language TEXT NOT NULL,
    target_word_id TEXT NOT NULL,
    link_type TEXT DEFAULT 'translation_candidate',
    confidence REAL DEFAULT 0.0,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS Sentence_Meaning (
    sentence_meaning_id TEXT PRIMARY KEY,
    language_code TEXT NOT NULL,
    sentence_text TEXT NOT NULL,
    meaning_text TEXT,
    source_id TEXT,
    review_status TEXT DEFAULT 'deferred',
    gold_write INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS Language_Review_Queue (
    review_id TEXT PRIMARY KEY,
    language_code TEXT,
    item_type TEXT,
    item_id TEXT,
    reason TEXT,
    status TEXT DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS Language_Source_Map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code TEXT,
    word_id TEXT,
    source_id TEXT,
    source_ref TEXT
);
CREATE INDEX IF NOT EXISTS idx_ar_search ON Arabic_Words(search_key_loose, seq_2, seq_3, seq_4);
CREATE INDEX IF NOT EXISTS idx_en_search ON English_Words(search_key_loose, seq_2, seq_3, seq_4);
CREATE INDEX IF NOT EXISTS idx_fr_search ON French_Words(search_key_loose, seq_2, seq_3, seq_4);
"""


QURAN_ARABIC_CORE_SQL = """
CREATE TABLE IF NOT EXISTS Quran_Ayahs (
    ayah_id TEXT PRIMARY KEY,
    surah_id INTEGER,
    surah_name_ar TEXT,
    ayah_number INTEGER,
    ayah_text_original TEXT NOT NULL,
    ayah_text_normalized TEXT,
    juz INTEGER,
    hizb INTEGER,
    page_number INTEGER,
    source_id TEXT,
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS Quran_Tafsir (
    tafsir_id TEXT PRIMARY KEY,
    ayah_id TEXT NOT NULL,
    tafsir_source TEXT NOT NULL,
    tafsir_text_ar TEXT NOT NULL,
    language_code TEXT DEFAULT 'ar',
    review_status TEXT DEFAULT 'pending_review',
    gold_write INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ayah_id) REFERENCES Quran_Ayahs(ayah_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Quran_Word_Map (
    map_id TEXT PRIMARY KEY,
    ayah_id TEXT NOT NULL,
    word_position INTEGER,
    quran_word_text TEXT NOT NULL,
    Arabic_word_ID TEXT,
    confidence REAL DEFAULT 0.0,
    review_status TEXT DEFAULT 'pending_review',
    FOREIGN KEY(ayah_id) REFERENCES Quran_Ayahs(ayah_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Quran_Page_Map (
    page_map_id TEXT PRIMARY KEY,
    page_number INTEGER,
    juz INTEGER,
    hizb INTEGER,
    surah_id INTEGER,
    surah_name_ar TEXT,
    ayah_start INTEGER,
    ayah_end INTEGER,
    review_status TEXT DEFAULT 'pending_review'
);
CREATE TABLE IF NOT EXISTS Arabic_Sentence_Meaning (
    sentence_meaning_id TEXT PRIMARY KEY,
    ayah_id TEXT,
    sentence_text TEXT NOT NULL,
    meaning_text_ar TEXT,
    source TEXT,
    review_status TEXT DEFAULT 'deferred',
    gold_write INTEGER DEFAULT 0,
    FOREIGN KEY(ayah_id) REFERENCES Quran_Ayahs(ayah_id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS Quran_Review_Queue (
    review_id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    sensitivity_level TEXT DEFAULT 'quran_sensitive',
    reason TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_quran_ayah ON Quran_Ayahs(surah_id, ayah_number);
CREATE INDEX IF NOT EXISTS idx_quran_word_map ON Quran_Word_Map(ayah_id, quran_word_text);
"""


PDF_EXTRACTION_CORRECTION_SQL = """
CREATE TABLE IF NOT EXISTS pdf_sources (source_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT, source_mode TEXT DEFAULT 'reference_only_no_copy', review_status TEXT DEFAULT 'pending_review', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pdf_jobs (job_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, job_type TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(source_id) REFERENCES pdf_sources(source_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pdf_outputs (output_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, raw_text_path TEXT, normalized_text_path TEXT, corrected_text_path TEXT, report_path TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0, FOREIGN KEY(job_id) REFERENCES pdf_jobs(job_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pdf_pages (page_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, page_number INTEGER NOT NULL, raw_text TEXT, normalized_text TEXT, image_path TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(source_id) REFERENCES pdf_sources(source_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pdf_quality_checks (check_id TEXT PRIMARY KEY, job_id TEXT, page_id TEXT, check_type TEXT, check_result TEXT, score REAL, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pdf_review_queue (review_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, reason TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pdf_error_capture_runs (run_id TEXT PRIMARY KEY, source_id TEXT, run_name TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pdf_error_capture_cycles (cycle_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, cycle_number INTEGER, comparison_source TEXT, status TEXT DEFAULT 'pending', FOREIGN KEY(run_id) REFERENCES pdf_error_capture_runs(run_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pdf_error_word_positions (position_id TEXT PRIMARY KEY, page_id TEXT NOT NULL, word_text TEXT, normalized_word TEXT, word_index INTEGER, line_number INTEGER, x0 REAL, y0 REAL, x1 REAL, y1 REAL, FOREIGN KEY(page_id) REFERENCES pdf_pages(page_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pdf_error_observations (observation_id TEXT PRIMARY KEY, position_id TEXT NOT NULL, error_type TEXT, wrong_text TEXT, expected_text TEXT, evidence_source TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0, FOREIGN KEY(position_id) REFERENCES pdf_error_word_positions(position_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pdf_error_repeat_patterns (pattern_id TEXT PRIMARY KEY, error_type TEXT, wrong_pattern TEXT, corrected_pattern TEXT, repeat_count INTEGER DEFAULT 0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pdf_no_error_signals (signal_id TEXT PRIMARY KEY, position_id TEXT NOT NULL, signal_text TEXT DEFAULT 'no_error_here', confidence REAL DEFAULT 0.0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(position_id) REFERENCES pdf_error_word_positions(position_id) ON DELETE CASCADE);
DROP VIEW IF EXISTS pdf_word_error_matrix_view;
CREATE VIEW pdf_word_error_matrix_view AS
SELECT p.page_number, wp.line_number, wp.word_index, wp.word_text, e.error_type, e.wrong_text, e.expected_text, e.review_status
FROM pdf_error_word_positions wp
JOIN pdf_pages p ON p.page_id = wp.page_id
LEFT JOIN pdf_error_observations e ON e.position_id = wp.position_id;
"""


WAREHOUSE_MEMORY_SQL = """
CREATE TABLE IF NOT EXISTS warehouse_batches (batch_id TEXT PRIMARY KEY, batch_name TEXT, source_path TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS warehouse_items (item_id TEXT PRIMARY KEY, batch_id TEXT, item_type TEXT, item_path TEXT, item_hash TEXT, review_status TEXT DEFAULT 'pending_review', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(batch_id) REFERENCES warehouse_batches(batch_id) ON DELETE SET NULL);
CREATE TABLE IF NOT EXISTS warehouse_file_cards (card_id TEXT PRIMARY KEY, item_id TEXT NOT NULL, file_name TEXT, extension TEXT, size_bytes INTEGER, payload_json TEXT, FOREIGN KEY(item_id) REFERENCES warehouse_items(item_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS warehouse_classification (classification_id TEXT PRIMARY KEY, item_id TEXT NOT NULL, primary_type TEXT, domain TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(item_id) REFERENCES warehouse_items(item_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS warehouse_relations (relation_id TEXT PRIMARY KEY, source_item_id TEXT, target_item_id TEXT, relation_type TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS warehouse_versions (version_id TEXT PRIMARY KEY, item_id TEXT NOT NULL, version_label TEXT, parent_version_id TEXT, conflict_status TEXT DEFAULT 'none', FOREIGN KEY(item_id) REFERENCES warehouse_items(item_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS warehouse_integrity_checks (check_id TEXT PRIMARY KEY, item_id TEXT NOT NULL, check_type TEXT, check_result TEXT, hash_value TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(item_id) REFERENCES warehouse_items(item_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS memory_bronze (bronze_id TEXT PRIMARY KEY, source_item_id TEXT, content_ref TEXT, payload_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS memory_silver (silver_id TEXT PRIMARY KEY, bronze_id TEXT, structured_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS memory_gold_candidates (candidate_id TEXT PRIMARY KEY, silver_id TEXT, candidate_reason TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS memory_gold (gold_id TEXT PRIMARY KEY, candidate_id TEXT, approved_by TEXT, decision_id TEXT, payload_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS memory_decisions (decision_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, decision TEXT CHECK(decision IN ('approve','reject','review','rerun')), reason TEXT, decided_by TEXT DEFAULT 'general_mind', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


AGENTS_PERSONAS_SQL = """
CREATE TABLE IF NOT EXISTS agents (agent_id TEXT PRIMARY KEY, agent_name_ar TEXT NOT NULL, agent_name_en TEXT, active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS agent_profiles (profile_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, role_description TEXT, personality_traits TEXT, default_style TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS agent_dialects (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL, dialect_id TEXT, strength REAL DEFAULT 0.5, FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS agent_voice_profiles (voice_profile_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, voice_id TEXT, voice_settings_json TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS agent_memory_private (memory_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, memory_text TEXT, memory_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0, FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS agent_skills (skill_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, skill_name TEXT, skill_level REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS agent_task_assignments (assignment_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, task_id TEXT, task_type TEXT, status TEXT DEFAULT 'pending', FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS agent_outputs (output_id TEXT PRIMARY KEY, agent_id TEXT, task_id TEXT, output_type TEXT, output_text TEXT, output_json TEXT, review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS agent_feedback (feedback_id TEXT PRIMARY KEY, output_id TEXT, feedback_text TEXT, rating REAL, reviewer TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS agent_learning_events (event_id TEXT PRIMARY KEY, agent_id TEXT, event_text TEXT, event_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS agent_review_queue (review_id TEXT PRIMARY KEY, agent_id TEXT, item_type TEXT, item_id TEXT, reason TEXT, status TEXT DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS agent_to_general_mind_reports (report_id TEXT PRIMARY KEY, agent_id TEXT, report_text TEXT, report_json TEXT, decision_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


DIALECT_STYLE_SQL = """
CREATE TABLE IF NOT EXISTS dialects (dialect_id TEXT PRIMARY KEY, dialect_name_ar TEXT NOT NULL, language_code TEXT DEFAULT 'ar', active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS dialect_regions (region_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, country TEXT, region_name TEXT, notes TEXT, FOREIGN KEY(dialect_id) REFERENCES dialects(dialect_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialect_word_map (map_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, source_word TEXT NOT NULL, dialect_word TEXT NOT NULL, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(dialect_id) REFERENCES dialects(dialect_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialect_phrase_map (map_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, source_phrase TEXT NOT NULL, dialect_phrase TEXT NOT NULL, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(dialect_id) REFERENCES dialects(dialect_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialect_syntax_rules (rule_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, rule_text TEXT, example_before TEXT, example_after TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(dialect_id) REFERENCES dialects(dialect_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialect_particles (particle_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, particle_text TEXT, meaning TEXT, usage_note TEXT, FOREIGN KEY(dialect_id) REFERENCES dialects(dialect_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialect_negation_rules (rule_id TEXT PRIMARY KEY, dialect_id TEXT, source_negation TEXT, dialect_negation TEXT, examples TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS dialect_question_rules (rule_id TEXT PRIMARY KEY, dialect_id TEXT, source_question TEXT, dialect_question TEXT, examples TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS dialect_intensity_rules (rule_id TEXT PRIMARY KEY, dialect_id TEXT, source_intensity TEXT, dialect_intensity TEXT, examples TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS style_transform_rules (rule_id TEXT PRIMARY KEY, persona_id TEXT, rule_scope TEXT, input_pattern TEXT, output_style TEXT, example_before TEXT, example_after TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS style_transform_runs (run_id TEXT PRIMARY KEY, input_text TEXT, output_text TEXT, dialect_id TEXT, persona_id TEXT, status TEXT DEFAULT 'pending_review', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS transformed_text_segments (segment_id TEXT PRIMARY KEY, run_id TEXT, segment_order INTEGER, source_text TEXT, transformed_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS dialect_review_queue (review_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, reason TEXT, status TEXT DEFAULT 'pending');
"""


VOICE_DIALECT_CORE_SQL = """
CREATE TABLE IF NOT EXISTS audio_sources (audio_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT, source_type TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS speech_segments (segment_id TEXT PRIMARY KEY, audio_id TEXT NOT NULL, start_ms INTEGER, end_ms INTEGER, segment_path TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(audio_id) REFERENCES audio_sources(audio_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS transcripts (transcript_id TEXT PRIMARY KEY, segment_id TEXT, transcript_text TEXT, asr_engine TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(segment_id) REFERENCES speech_segments(segment_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialect_profiles (dialect_id TEXT PRIMARY KEY, dialect_name_ar TEXT, language_code TEXT DEFAULT 'ar', region TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pronunciation_lexicon (entry_id TEXT PRIMARY KEY, dialect_id TEXT, word_text TEXT, pronunciation_text TEXT, phonetic TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS speaker_profiles (speaker_id TEXT PRIMARY KEY, speaker_label TEXT, gender_label TEXT, tone_label TEXT, embedding_path TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS voice_style_rules (rule_id TEXT PRIMARY KEY, voice_id TEXT, style_name TEXT, rule_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS tts_runs (tts_run_id TEXT PRIMARY KEY, input_text TEXT, voice_id TEXT, output_audio_path TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS asr_runs (asr_run_id TEXT PRIMARY KEY, audio_id TEXT, output_text TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS voice_quality_checks (check_id TEXT PRIMARY KEY, run_id TEXT, check_type TEXT, score REAL, result_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS voice_errors (error_id TEXT PRIMARY KEY, run_id TEXT, error_type TEXT, wrong_text TEXT, corrected_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS voice_review_queue (review_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, reason TEXT, status TEXT DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS pronunciation_profiles (pronunciation_profile_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, profile_name_ar TEXT, description_ar TEXT);
CREATE TABLE IF NOT EXISTS letter_pronunciation_rules (rule_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT, source_letter TEXT, spoken_form TEXT, condition_ar TEXT, example_word TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS phoneme_rules (rule_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT, source_unit TEXT, phoneme TEXT, condition_ar TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS word_pronunciation_lexicon (entry_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT, word_text TEXT, spoken_form TEXT, phonetic TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pronunciation_exceptions (exception_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT, word_text TEXT, exception_pronunciation TEXT, reason TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS diacritics_rules (rule_id TEXT PRIMARY KEY, language_code TEXT DEFAULT 'ar', rule_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS stress_rules (rule_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT, rule_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pause_rules (rule_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT, rule_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS tts_voice_profiles (voice_id TEXT PRIMARY KEY, voice_name_ar TEXT, speed REAL DEFAULT 1.0, pitch TEXT DEFAULT 'medium', emotion TEXT DEFAULT 'neutral', tts_engine TEXT DEFAULT 'local_or_later', review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pronunciation_runs (run_id TEXT PRIMARY KEY, input_text TEXT, output_pronunciation TEXT, profile_id TEXT, status TEXT DEFAULT 'pending_review', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pronunciation_review_queue (review_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, reason TEXT, status TEXT DEFAULT 'pending');
"""


STUDIO_VISION_CORE_SQL = """
CREATE TABLE IF NOT EXISTS video_sources (video_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT, duration_ms INTEGER, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS image_sources (image_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT, width INTEGER, height INTEGER, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS frames (frame_id TEXT PRIMARY KEY, video_id TEXT, frame_number INTEGER, timestamp_ms INTEGER, image_path TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS scene_segments (scene_id TEXT PRIMARY KEY, video_id TEXT, start_ms INTEGER, end_ms INTEGER, description TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS detected_objects (object_id TEXT PRIMARY KEY, frame_id TEXT, label TEXT, confidence REAL, bbox_json TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS detected_people (person_id TEXT PRIMARY KEY, frame_id TEXT, person_label TEXT, face_bbox_json TEXT, confidence REAL, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pose_detections (pose_id TEXT PRIMARY KEY, frame_id TEXT, person_id TEXT, keypoints_json TEXT, confidence REAL, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS scene_descriptions (description_id TEXT PRIMARY KEY, scene_id TEXT, description_text TEXT, source_engine TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS prompt_blueprints (prompt_id TEXT PRIMARY KEY, scene_id TEXT, prompt_text TEXT, negative_prompt TEXT, model_target TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS generation_jobs (job_id TEXT PRIMARY KEY, job_type TEXT, prompt_id TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS generation_outputs (output_id TEXT PRIMARY KEY, job_id TEXT, output_path TEXT, output_type TEXT, metadata_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS video_quality_checks (check_id TEXT PRIMARY KEY, target_type TEXT, target_id TEXT, check_type TEXT, score REAL, result_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS studio_review_queue (review_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, reason TEXT, status TEXT DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS studio_decisions (decision_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, decision TEXT, decided_by TEXT DEFAULT 'general_mind', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


CHAT_MULTIMODAL_CORE_SQL = """
CREATE TABLE IF NOT EXISTS conversations (conversation_id TEXT PRIMARY KEY, title TEXT, mode_id TEXT, review_status TEXT DEFAULT 'pending_review', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS chat_messages (message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, sender_type TEXT NOT NULL, sender_id TEXT, input_type TEXT, text_content TEXT, detected_intent TEXT, review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS message_parts (part_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, part_type TEXT NOT NULL, text_value TEXT, file_path TEXT, metadata_json TEXT, FOREIGN KEY(message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS message_status_events (event_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, status TEXT, event_text TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS message_attachments (attachment_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, attachment_type TEXT, file_path TEXT, file_hash TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS message_actions (action_id TEXT PRIMARY KEY, message_id TEXT NOT NULL, action_type TEXT, action_payload_json TEXT, status TEXT DEFAULT 'pending', FOREIGN KEY(message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE);
"""


VIDEO_UNDERSTANDING_CORE_SQL = """
CREATE TABLE IF NOT EXISTS video_sources (video_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT, duration_ms INTEGER, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS video_frames (frame_id TEXT PRIMARY KEY, video_id TEXT, frame_number INTEGER, timestamp_ms INTEGER, image_path TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS scene_segments (scene_id TEXT PRIMARY KEY, video_id TEXT, start_ms INTEGER, end_ms INTEGER, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS audio_tracks (audio_track_id TEXT PRIMARY KEY, video_id TEXT, audio_path TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS speech_transcripts (transcript_id TEXT PRIMARY KEY, audio_track_id TEXT, start_ms INTEGER, end_ms INTEGER, transcript_text TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS ocr_text_regions (region_id TEXT PRIMARY KEY, frame_id TEXT, text_value TEXT, bbox_json TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS visual_descriptions (description_id TEXT PRIMARY KEY, scene_id TEXT, description_text TEXT, source_engine TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS timeline_events (event_id TEXT PRIMARY KEY, video_id TEXT, start_ms INTEGER, end_ms INTEGER, event_type TEXT, event_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS video_analysis_reports (report_id TEXT PRIMARY KEY, video_id TEXT, report_text TEXT, report_json TEXT, review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
"""


TRANSLATION_VOICE_CORE_SQL = """
CREATE TABLE IF NOT EXISTS translation_jobs (job_id TEXT PRIMARY KEY, source_language TEXT, target_language TEXT, input_text TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS translated_segments (segment_id TEXT PRIMARY KEY, job_id TEXT, segment_order INTEGER, source_text TEXT, translated_text TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS subtitle_segments (subtitle_id TEXT PRIMARY KEY, media_id TEXT, start_ms INTEGER, end_ms INTEGER, language_code TEXT, subtitle_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS voice_profiles (voice_id TEXT PRIMARY KEY, voice_name TEXT, dialect_id TEXT, speed REAL DEFAULT 1.0, pitch TEXT DEFAULT 'medium', emotion TEXT DEFAULT 'neutral', review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS tts_jobs (tts_job_id TEXT PRIMARY KEY, input_text TEXT, voice_id TEXT, output_audio_path TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS asr_jobs (asr_job_id TEXT PRIMARY KEY, input_audio_path TEXT, transcript_text TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS pronunciation_maps (map_id TEXT PRIMARY KEY, language_code TEXT, source_text TEXT, pronunciation_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS audio_outputs (audio_output_id TEXT PRIMARY KEY, job_id TEXT, audio_path TEXT, metadata_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
"""


PERSONA_PERFORMANCE_CORE_SQL = """
CREATE TABLE IF NOT EXISTS agents (agent_id TEXT PRIMARY KEY, agent_name_ar TEXT NOT NULL, agent_name_en TEXT, active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS persona_profiles (profile_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, base_identity_ar TEXT NOT NULL, base_tone_ar TEXT, speaking_style_ar TEXT, default_dialect_id TEXT, default_voice_id TEXT, review_status TEXT DEFAULT 'pending_review', FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS performance_layers (layer_id TEXT PRIMARY KEY, layer_name TEXT NOT NULL, layer_name_ar TEXT NOT NULL, layer_type TEXT NOT NULL, description_ar TEXT);
CREATE TABLE IF NOT EXISTS agent_performance_bindings (binding_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, layer_id TEXT NOT NULL, strength REAL DEFAULT 0.5, priority INTEGER DEFAULT 5, enabled INTEGER DEFAULT 1, notes_ar TEXT, FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE, FOREIGN KEY(layer_id) REFERENCES performance_layers(layer_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dialects (dialect_id TEXT PRIMARY KEY, dialect_name_ar TEXT NOT NULL, region_ar TEXT, language_code TEXT DEFAULT 'ar', description_ar TEXT, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS agent_dialect_bindings (binding_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, dialect_id TEXT NOT NULL, default_strength REAL DEFAULT 0.5, enabled INTEGER DEFAULT 1, FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE, FOREIGN KEY(dialect_id) REFERENCES dialects(dialect_id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS style_rules (rule_id TEXT PRIMARY KEY, agent_id TEXT, layer_id TEXT, rule_scope TEXT, input_pattern TEXT, output_style_ar TEXT NOT NULL, example_before TEXT, example_after TEXT, priority INTEGER DEFAULT 5, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS dialect_word_map (map_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, source_word TEXT NOT NULL, dialect_word TEXT NOT NULL, confidence REAL DEFAULT 0.7, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS dialect_phrase_map (map_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, source_phrase TEXT NOT NULL, dialect_phrase TEXT NOT NULL, confidence REAL DEFAULT 0.7, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS pronunciation_profiles (pronunciation_profile_id TEXT PRIMARY KEY, dialect_id TEXT NOT NULL, profile_name_ar TEXT NOT NULL, description_ar TEXT);
CREATE TABLE IF NOT EXISTS letter_pronunciation_rules (rule_id TEXT PRIMARY KEY, pronunciation_profile_id TEXT NOT NULL, source_letter TEXT NOT NULL, spoken_form TEXT NOT NULL, condition_ar TEXT, example_word TEXT, confidence REAL DEFAULT 0.5, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS voice_profiles (voice_id TEXT PRIMARY KEY, voice_name_ar TEXT NOT NULL, gender_label TEXT, default_speed REAL DEFAULT 1.0, default_pitch TEXT DEFAULT 'medium', default_emotion TEXT DEFAULT 'neutral', tts_engine TEXT DEFAULT 'local_or_later', review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS runtime_tasks (task_id TEXT PRIMARY KEY, source TEXT DEFAULT 'chat', input_type TEXT NOT NULL, target_output TEXT NOT NULL, input_text TEXT, requested_agent_id TEXT, requested_dialect_id TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS runtime_task_assignments (assignment_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, agent_id TEXT NOT NULL, layer_id TEXT NOT NULL, dialect_id TEXT, voice_id TEXT, status TEXT DEFAULT 'planned');
CREATE TABLE IF NOT EXISTS runtime_outputs (output_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, agent_id TEXT, layer_id TEXT, output_type TEXT NOT NULL, output_text TEXT, output_json TEXT, review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS review_queue (review_id TEXT PRIMARY KEY, task_id TEXT, output_id TEXT, review_type TEXT NOT NULL, reason_ar TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


SYSTEM_REGISTRY_SQL = """
CREATE TABLE IF NOT EXISTS components (component_id TEXT PRIMARY KEY, component_name TEXT NOT NULL, component_type TEXT, root_path TEXT, status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS component_versions (version_id TEXT PRIMARY KEY, component_id TEXT, version_label TEXT, hash_value TEXT, status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS routes (route_id TEXT PRIMARY KEY, route_name TEXT NOT NULL, input_type TEXT, output_type TEXT, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS route_steps (step_id TEXT PRIMARY KEY, route_id TEXT, step_order INTEGER, component_id TEXT, step_name TEXT, policy_id TEXT);
CREATE TABLE IF NOT EXISTS policies (policy_id TEXT PRIMARY KEY, policy_group TEXT, rule_text TEXT NOT NULL, enforcement_level TEXT DEFAULT 'hard', active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS runtime_events (event_id TEXT PRIMARY KEY, event_type TEXT, payload_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS runtime_reports (report_id TEXT PRIMARY KEY, report_type TEXT, report_text TEXT, report_json TEXT, review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS decision_log (decision_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, decision TEXT, reason TEXT, decided_by TEXT DEFAULT 'general_mind', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS review_policies (review_policy_id TEXT PRIMARY KEY, item_type TEXT, policy_text TEXT, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS gold_approval_log (approval_id TEXT PRIMARY KEY, candidate_id TEXT, decision_id TEXT, approved_by TEXT DEFAULT 'general_mind', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS blocked_items (blocked_id TEXT PRIMARY KEY, item_type TEXT, item_ref TEXT, reason TEXT, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS external_references (reference_id TEXT PRIMARY KEY, reference_type TEXT, reference_path TEXT, source_mode TEXT DEFAULT 'reference_only_no_copy', review_status TEXT DEFAULT 'pending_review');
INSERT OR IGNORE INTO policies(policy_id, policy_group, rule_text, enforcement_level) VALUES
('POL-NO-DIRECT-RUN','execution','لا تشغيل مباشر لأي ZIP أو مشروع أو سكربت خام.','hard'),
('POL-NO-GOLD','memory','لا Gold مباشر؛ الاعتماد بقرار العقل العام فقط.','hard'),
('POL-REVIEW-REQUIRED','review','كل المخرجات الحساسة تمر بالمراجعة.','hard');
"""


PROJECT_FACTORY_SQL = """
CREATE TABLE IF NOT EXISTS source_projects (project_id TEXT PRIMARY KEY, project_name TEXT, source_path TEXT, project_hash TEXT, review_status TEXT DEFAULT 'pending_review', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS source_project_files (file_id TEXT PRIMARY KEY, project_id TEXT, file_path TEXT, file_hash TEXT, extension TEXT, size_bytes INTEGER, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS code_symbols (symbol_id TEXT PRIMARY KEY, file_id TEXT, symbol_type TEXT, symbol_name TEXT, line_start INTEGER, line_end INTEGER, payload_json TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS code_imports (import_id TEXT PRIMARY KEY, file_id TEXT, import_name TEXT, import_type TEXT, source_line TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS code_relations (relation_id TEXT PRIMARY KEY, source_symbol_id TEXT, target_symbol_id TEXT, relation_type TEXT, confidence REAL DEFAULT 0.0, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS project_capabilities (capability_id TEXT PRIMARY KEY, project_id TEXT, capability_name TEXT, capability_description TEXT, input_contract TEXT, output_contract TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS project_contracts (contract_id TEXT PRIMARY KEY, capability_id TEXT, input_json TEXT, output_json TEXT, errors_json TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS project_fusion_plans (fusion_plan_id TEXT PRIMARY KEY, plan_name TEXT, source_projects_json TEXT, fusion_strategy TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS project_conflicts (conflict_id TEXT PRIMARY KEY, fusion_plan_id TEXT, conflict_type TEXT, conflict_text TEXT, resolution_text TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS target_project_blueprints (blueprint_id TEXT PRIMARY KEY, fusion_plan_id TEXT, blueprint_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS generated_files (generated_file_id TEXT PRIMARY KEY, blueprint_id TEXT, file_path TEXT, content_hash TEXT, generation_reason TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS sandbox_runs (sandbox_run_id TEXT PRIMARY KEY, project_id TEXT, command_text TEXT, status TEXT DEFAULT 'pending', stdout_text TEXT, stderr_text TEXT, review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS test_runs (test_run_id TEXT PRIMARY KEY, sandbox_run_id TEXT, test_name TEXT, status TEXT DEFAULT 'pending', result_json TEXT, review_required INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS detected_errors (error_id TEXT PRIMARY KEY, source_ref TEXT, error_type TEXT, error_text TEXT, severity TEXT, review_status TEXT DEFAULT 'pending_review');
CREATE TABLE IF NOT EXISTS error_fixes (fix_id TEXT PRIMARY KEY, error_id TEXT, fix_text TEXT, patch_json TEXT, status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS code_reviews (review_id TEXT PRIMARY KEY, source_ref TEXT, review_text TEXT, reviewer TEXT DEFAULT 'rawan_or_general_mind', status TEXT DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS learning_reports (learning_report_id TEXT PRIMARY KEY, project_id TEXT, report_text TEXT, report_json TEXT, review_status TEXT DEFAULT 'pending_review', gold_write INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS factory_decisions (decision_id TEXT PRIMARY KEY, item_type TEXT, item_id TEXT, decision TEXT, reason TEXT, decided_by TEXT DEFAULT 'general_mind', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS code_operations (operation_id TEXT PRIMARY KEY, operation_type TEXT NOT NULL, source_project_id TEXT, requested_by TEXT DEFAULT 'chat', input_text TEXT, status TEXT DEFAULT 'pending', review_required INTEGER DEFAULT 1, gold_write INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS code_operation_steps (step_id TEXT PRIMARY KEY, operation_id TEXT NOT NULL, step_order INTEGER NOT NULL, step_name TEXT NOT NULL, assigned_agent_id TEXT, tool_name TEXT, input_json TEXT, output_json TEXT, status TEXT DEFAULT 'planned', error_text TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(operation_id) REFERENCES code_operations(operation_id) ON DELETE CASCADE);
"""


DATABASES = [
    (DB_DIR / "system_light_core.db", SYSTEM_LIGHT_CORE_SQL),
    (DB_DIR / "language_core.db", LANGUAGE_CORE_SQL),
    (DB_DIR / "quran_arabic_core.db", QURAN_ARABIC_CORE_SQL),
    (DB_DIR / "pdf_extraction_correction.db", PDF_EXTRACTION_CORRECTION_SQL),
    (DB_DIR / "warehouse_memory.db", WAREHOUSE_MEMORY_SQL),
    (DB_DIR / "agents_personas.db", AGENTS_PERSONAS_SQL),
    (DB_DIR / "dialect_style_core.db", DIALECT_STYLE_SQL),
    (DB_DIR / "voice_dialect_core.db", VOICE_DIALECT_CORE_SQL),
    (DB_DIR / "studio_vision_core.db", STUDIO_VISION_CORE_SQL),
    (DB_DIR / "chat_multimodal_core.db", CHAT_MULTIMODAL_CORE_SQL),
    (DB_DIR / "video_understanding_core.db", VIDEO_UNDERSTANDING_CORE_SQL),
    (DB_DIR / "translation_voice_core.db", TRANSLATION_VOICE_CORE_SQL),
    (DB_DIR / "persona_performance_core.db", PERSONA_PERFORMANCE_CORE_SQL),
    (DB_DIR / "system_registry.db", SYSTEM_REGISTRY_SQL),
    (Z3EEM_DB_DIR / "project_factory.db", PROJECT_FACTORY_SQL),
]


def seed_persona_performance() -> None:
    db_path = DB_DIR / "persona_performance_core.db"
    con = connect(db_path)
    try:
        cur = con.cursor()
        cur.executemany(
            "INSERT OR IGNORE INTO agents(agent_id, agent_name_ar, agent_name_en) VALUES(?,?,?)",
            [
                ("maya", "مايا", "Maya"),
                ("fno", "فنو", "FNO"),
                ("amal", "أمل", "Amal"),
                ("rawan", "روان", "Rawan"),
                ("lara", "لارا", "Lara"),
                ("dunia", "دنيا", "Dunia"),
            ],
        )
        cur.executemany(
            "INSERT OR IGNORE INTO dialects(dialect_id, dialect_name_ar, region_ar, language_code, description_ar) VALUES(?,?,?,?,?)",
            [
                ("msa", "فصحى مبسطة", "عام", "ar", "لغة عربية واضحة ومباشرة"),
                ("hijazi_light", "حجازية خفيفة", "الحجاز", "ar", "لهجة حجازية مفهومة بدون مبالغة"),
                ("lebanese_light", "لبنانية خفيفة", "لبنان", "ar", "لهجة لبنانية خفيفة"),
            ],
        )
        cur.executemany(
            "INSERT OR IGNORE INTO performance_layers(layer_id, layer_name, layer_name_ar, layer_type, description_ar) VALUES(?,?,?,?,?)",
            [
                ("chat_reply", "chat_reply", "رد شات", "chat", "إنتاج رد كتابي داخل المحادثة"),
                ("style_transform", "style_transform", "تحويل أسلوب", "style", "تحويل النص إلى أسلوب الشخصية"),
                ("dialect_transform", "dialect_transform", "تحويل لهجة", "dialect", "تحويل النص إلى لهجة معينة"),
                ("pronunciation_map", "pronunciation_map", "خريطة نطق", "voice", "تجهيز نطق الحروف والكلمات"),
                ("voice_performance", "voice_performance", "أداء صوتي", "voice", "تحديد النبرة والسرعة والعاطفة"),
                ("text_to_video_planning", "text_to_video_planning", "تخطيط نص إلى فيديو", "studio", "تحويل النص إلى مشاهد ولقطات"),
                ("video_to_text_analysis", "video_to_text_analysis", "تحليل فيديو إلى نص", "vision", "استخراج نص ووصف وترجمة من الفيديو"),
                ("translation", "translation", "ترجمة", "language", "ترجمة النصوص والمقاطع"),
                ("review", "review", "مراجعة", "review", "فحص الجودة والأخطاء"),
                ("reporting", "reporting", "تقارير", "report", "تلخيص النتائج وكتابة التقارير"),
            ],
        )
        cur.executemany(
            "INSERT OR IGNORE INTO voice_profiles(voice_id, voice_name_ar, gender_label, default_speed, default_pitch, default_emotion) VALUES(?,?,?,?,?,?)",
            [
                ("maya_hijazi_soft", "صوت مايا الحجازي الهادئ", "female", 0.92, "medium", "calm"),
                ("fno_cinematic", "صوت فنو السينمائي", "male_or_neutral", 1.02, "medium", "energetic"),
                ("amal_analysis", "صوت أمل التحليلي", "female", 0.94, "medium", "focused"),
                ("rawan_review", "صوت روان المراجع", "female", 0.95, "medium", "precise"),
                ("lara_editor", "صوت لارا التحريري", "female", 0.96, "medium", "clear"),
                ("dunia_report", "صوت دنيا التقاريري", "female", 0.98, "medium", "organized"),
            ],
        )
        con.commit()
    finally:
        con.close()


def main() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    Z3EEM_DB_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for db_path, schema in DATABASES:
        results.append(apply_schema(db_path, schema))

    seed_persona_performance()

    report = {
        "status": "ok",
        "created_at": utc_now(),
        "database_count": len(DATABASES),
        "rules": {
            "gold_write_default": 0,
            "review_required_default": 1,
            "quran_auto_correction": False,
            "direct_zip_execution": False,
            "final_decision_owner": "general_mind",
        },
        "results": results,
    }
    report_path = REPORT_DIR / "init_all_databases_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
