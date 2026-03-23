#!/usr/bin/env python3
"""
===========================================================
ORBITA DB - SQLite Storage Fallback
Alternativa gratuita a Notion para guardar leads
===========================================================
"""

import sqlite3, os, json, sys
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = "orbita.db"

def init_db():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabla de leads
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            domain TEXT,
            website TEXT,
            instagram TEXT,
            country TEXT,
            industry TEXT,
            lead_source TEXT,
            dedupe_key TEXT UNIQUE,
            score_total INTEGER,
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
    """)
    
    # Tabla de enrichment
    c.execute("""
        CREATE TABLE IF NOT EXISTS enrichment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            emails TEXT,
            phones TEXT,
            contacts TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    
    # Tabla de outreach
    c.execute("""
        CREATE TABLE IF NOT EXISTS outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            ig_dm TEXT,
            whatsapp TEXT,
            email_subject TEXT,
            email_body TEXT,
            sent_at TEXT,
            response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    
    conn.commit()
    return conn

def get_conn():
    """Obtiene conexión a la DB"""
    if not os.path.exists(DB_PATH):
        return init_db()
    return sqlite3.connect(DB_PATH)

def save_lead(lead: dict, conn=None) -> int:
    """Guarda un lead en la DB"""
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    
    c = conn.cursor()
    
    # Verificar duplicado
    dedupe_key = lead.get("dedupe_key") or lead.get("domain") or lead.get("instagram", "").lower()
    
    try:
        c.execute("SELECT id FROM leads WHERE dedupe_key = ?", (dedupe_key,))
        existing = c.fetchone()
        
        if existing:
            # Update
            lead_id = existing[0]
            c.execute("""
                UPDATE leads SET
                    company_name = ?, domain = ?, website = ?, instagram = ?,
                    country = ?, industry = ?, lead_source = ?, score_total = ?,
                    updated_at = CURRENT_TIMESTAMP, raw_data = ?
                WHERE id = ?
            """, (
                lead.get("company_name"), lead.get("domain"), lead.get("website"),
                lead.get("instagram"), lead.get("country"), lead.get("industry"),
                lead.get("lead_source"), lead.get("qa", {}).get("score_total"),
                json.dumps(lead), lead_id
            ))
        else:
            # Insert
            c.execute("""
                INSERT INTO leads (company_name, domain, website, instagram, country,
                    industry, lead_source, dedupe_key, score_total, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.get("company_name"), lead.get("domain"), lead.get("website"),
                lead.get("instagram"), lead.get("country"), lead.get("industry"),
                lead.get("lead_source"), dedupe_key,
                lead.get("qa", {}).get("score_total"), json.dumps(lead)
            ))
            lead_id = c.lastrowid
        
        conn.commit()
        
        if close_conn:
            conn.close()
        
        return lead_id
        
    except Exception as e:
        print(f"Error saving lead: {e}")
        if close_conn:
            conn.close()
        return None

def save_enrichment(lead_id: int, enrichment: dict, conn=None):
    """Guarda datos de enrichment"""
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    
    c = conn.cursor()
    c.execute("""
        INSERT INTO enrichment (lead_id, emails, phones, contacts, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        lead_id,
        json.dumps(enrichment.get("emails", [])),
        json.dumps(enrichment.get("phones", [])),
        json.dumps(enrichment.get("contacts", [])),
        enrichment.get("notes", "")
    ))
    conn.commit()
    
    if close_conn:
        conn.close()

def save_outreach(lead_id: int, outreach: dict, conn=None):
    """Guarda mensajes de outreach"""
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    
    c = conn.cursor()
    c.execute("""
        INSERT INTO outreach (lead_id, ig_dm, whatsapp, email_subject, email_body)
        VALUES (?, ?, ?, ?, ?)
    """, (
        lead_id,
        outreach.get("ig_dm", ""),
        outreach.get("whatsapp", ""),
        outreach.get("email", {}).get("subject", ""),
        outreach.get("email", {}).get("body", "")
    ))
    conn.commit()
    
    if close_conn:
        conn.close()

def get_leads(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Obtiene leads de la DB"""
    conn = get_conn()
    c = conn.cursor()
    
    if status:
        c.execute("SELECT * FROM leads WHERE status = ? ORDER BY score_total DESC LIMIT ?", (status, limit))
    else:
        c.execute("SELECT * FROM leads ORDER BY score_total DESC LIMIT ?", (limit,))
    
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    conn.close()
    
    results = []
    for row in rows:
        lead = dict(zip(columns, row))
        if lead.get("raw_data"):
            try:
                lead.update(json.loads(lead["raw_data"]))
            except:
                pass
        results.append(lead)
    
    return results

def get_stats() -> dict:
    """Obtiene estadísticas de la DB"""
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'")
    nuevos = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM leads WHERE score_total >= 60")
    qualify = c.fetchone()[0]
    
    c.execute("SELECT AVG(score_total) FROM leads WHERE score_total IS NOT NULL")
    avg_score = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_leads": total,
        "new_leads": nuevos,
        "ready_for_outreach": qualify,
        "avg_score": round(avg_score, 1)
    }

def bulk_save_leads(leads: list) -> int:
    """Guarda múltiples leads"""
    conn = get_conn()
    count = 0
    for lead in leads:
        if save_lead(lead, conn):
            count += 1
    conn.close()
    return count

if __name__ == "__main__":
    # Test
    init_db()
    print("DB initialized:", DB_PATH)
    print(json.dumps(get_stats(), indent=2))