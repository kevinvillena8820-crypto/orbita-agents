#!/usr/bin/env python3
"""
===========================================================
ORBITA Config - Configuración centralizada
Detecta modo gratuito vs modo pago automáticamente
===========================================================
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class OrbitaConfig:
    """Configuración global de Orbita"""
    # Modo scraping
    scraping_mode: str  # "apify" | "http_local" | "manual_urls"
    
    # Storage
    storage_mode: str   # "notion" | "sqlite"
    notion_token: Optional[str]
    notion_db: Optional[str]
    
    # Enrichment
    enrichment_enabled: bool
    
    # LLM (opcional)
    llm_mode: str       # "anthropic" | "ollama" | "templates"
    anthropic_key: Optional[str]
    ollama_url: Optional[str]
    
    # Apollo (email enrichment)
    apollo_key: Optional[str]
    
    # Features habilitadas
    features: dict
    
def load_config() -> OrbitaConfig:
    """Carga configuración desde entorno"""
    
    # Scraping
    apiify_key = os.getenv("APIFY_API_KEY")
    if apiify_key:
        scraping_mode = "apify"
    else:
        scraping_mode = "http_local"  # Fallback gratuito
    
    # Storage
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db = os.getenv("NOTION_LEADS_DB")
    if notion_token and notion_db:
        storage_mode = "notion"
    else:
        storage_mode = "sqlite"  # Fallback gratuito
    
    # LLM
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    if anthropic_key:
        llm_mode = "anthropic"
    elif os.path.exists("/usr/local/bin/ollama") or os.path.exists(os.path.expanduser("~/.local/bin/ollama")):
        llm_mode = "ollama"
    else:
        llm_mode = "templates"  # Fallback sin LLM
    
    # Apollo (email enrichment)
    apollo_key = os.getenv("APOLLO_API_KEY")
    
    # Enrichment siempre disponible (ya es gratuito)
    enrichment_enabled = True
    
    # Features
    features = {
        "scraping": scraping_mode != "none",
        "storage": storage_mode in ["notion", "sqlite"],
        "enrichment": enrichment_enabled,
        "qa": True,  # Sin LLM requerido
        "outreach": llm_mode in ["anthropic", "ollama"],
        "llm_enhancement": llm_mode != "templates"
    }
    
    return OrbitaConfig(
        scraping_mode=scraping_mode,
        storage_mode=storage_mode,
        notion_token=notion_token,
        notion_db=notion_db,
        enrichment_enabled=enrichment_enabled,
        llm_mode=llm_mode,
        anthropic_key=anthropic_key,
        ollama_url=ollama_url,
        apollo_key=apollo_key,
        features=features
    )

def get_diagnosis() -> dict:
    """Devuelve diagnóstico de configuración"""
    config = load_config()
    
    return {
        "scraping_mode": config.scraping_mode,
        "storage_mode": config.storage_mode,
        "llm_mode": config.llm_mode,
        "apollo_enabled": bool(config.apollo_key),
        "features_enabled": config.features,
        "missing_env_vars": get_missing_vars(),
        "recommendations": get_recommendations(config)
    }

def get_missing_vars() -> list:
    """Lista variables de entorno faltantes"""
    required = ["NOTION_TOKEN", "NOTION_LEADS_DB"]
    optional = ["APIFY_API_KEY", "ANTHROPIC_API_KEY", "OLLAMA_URL", "SUPABASE_ACCESS_TOKEN", "APOLLO_API_KEY"]
    
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    return missing

def get_recommendations(config: OrbitaConfig) -> list:
    """Recomendaciones según configuración actual"""
    recs = []
    
    if config.scraping_mode == "http_local":
        recs.append("Sin Apify: usa listas manuales de URLs en data/urls.txt")
    
    if config.storage_mode == "sqlite":
        recs.append("SQLite: los leads se guardan localmente en orbita.db")
    
    if config.llm_mode == "templates":
        recs.append("Sin LLM: usa templates deterministas para outreach")
        recs.append("Opcional: instala Ollama para enrichment con IA local")
    
    if not config.notion_token:
        recs.append("Sin Notion: usa SQLite como storage gratuito")
    
    if not config.apollo_key:
        recs.append("Sin Apollo: usa scraping web gratuito para enrichment")
    
    return recs

if __name__ == "__main__":
    import json
    print(json.dumps(get_diagnosis(), indent=2))