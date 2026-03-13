#!/usr/bin/env python3
"""
============================================================
ORBITA — Agente de Scraping (Agente #1)
Usa Apify para extraer leads y los guarda en Notion
============================================================
Uso:
  python3 agent_scraping.py
  python3 agent_scraping.py --objetivo "CTOs de startups SaaS en Madrid"
  python3 agent_scraping.py --fuente linkedin --limite 100
============================================================
"""

import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

APIFY_API_KEY     = os.getenv("APIFY_API_KEY")
NOTION_TOKEN      = os.getenv("NOTION_TOKEN")
NOTION_LEADS_DB   = os.getenv("NOTION_LEADS_DB")

# ============================================================
# ACTORES DE APIFY disponibles por tipo de fuente
# ============================================================
APIFY_ACTORS = {
    "linkedin":     "jungle-box~linkedin-company-scraper",   # LinkedIn Companies Scraper
    "google_maps":  "poidata~google-maps-scraper",   # Google Maps Scraper (poidata)
    "product_hunt": "dtrungtin~product-hunt-scraper",   # Product Hunt Scraper
    "web_custom":   "apify~website-content-crawler",   # Website Content Crawler
}

# ============================================================
# COLORES para la terminal
# ============================================================
class C:
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    BLUE   = "\033[94m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def log(msg, tipo="info"):
    hora = datetime.now().strftime("%H:%M:%S")
    iconos = {"info": "ℹ️ ", "ok": "✅", "warn": "⚠️ ", "error": "❌", "run": "🔄"}
    colores = {"info": C.BLUE, "ok": C.GREEN, "warn": C.YELLOW, "error": C.RED, "run": C.BLUE}
    color = colores.get(tipo, C.RESET)
    icono = iconos.get(tipo, "  ")
    print(f"{color}[{hora}] {icono}  {msg}{C.RESET}")


# ============================================================
# 1. LANZAR SCRAPING EN APIFY
# ============================================================
def lanzar_apify(actor_id: str, input_data: dict) -> str:
    """Lanza un actor de Apify y devuelve el run_id"""
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {APIFY_API_KEY}"}

    log(f"Lanzando actor Apify: {actor_id}", "run")
    resp = requests.post(url, json=input_data, headers=headers)
    resp.raise_for_status()

    run_id = resp.json()["data"]["id"]
    log(f"Run iniciado: {run_id}", "ok")
    return run_id


def esperar_apify(run_id: str, timeout: int = 300) -> list:
    """Espera a que termine el run y devuelve los resultados"""
    headers = {"Authorization": f"Bearer {APIFY_API_KEY}"}
    inicio = time.time()

    log("Esperando resultados de Apify...", "run")

    while True:
        # Verificar estado
        url_status = f"https://api.apify.com/v2/actor-runs/{run_id}"
        resp = requests.get(url_status, headers=headers)
        estado = resp.json()["data"]["status"]

        if estado == "SUCCEEDED":
            log("Scraping completado", "ok")
            break
        elif estado in ("FAILED", "ABORTED", "TIMED-OUT"):
            log(f"Error en Apify: {estado}", "error")
            return []

        elapsed = int(time.time() - inicio)
        log(f"Estado: {estado} ({elapsed}s)...", "run")

        if elapsed > timeout:
            log("Timeout esperando Apify", "error")
            return []

        time.sleep(8)

    # Descargar resultados
    dataset_id = requests.get(
        f"https://api.apify.com/v2/actor-runs/{run_id}",
        headers=headers
    ).json()["data"]["defaultDatasetId"]

    url_data = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
    items = requests.get(url_data, headers=headers).json()
    log(f"Descargados {len(items)} resultados crudos", "ok")
    return items


# ============================================================
# 2. NORMALIZAR Y PUNTUAR LEADS
# ============================================================
def normalizar_lead(item: dict, fuente: str) -> dict:
    """Convierte el formato de Apify al formato de Orbita"""

    # Mapeo según la fuente
    if fuente == "linkedin":
        lead = {
            "nombre":   item.get("fullName") or item.get("name", "Sin nombre"),
            "empresa":  item.get("companyName") or item.get("company", ""),
            "cargo":    item.get("title") or item.get("jobTitle", ""),
            "email":    item.get("email", ""),
            "telefono": item.get("phone", ""),
            "web":      item.get("companyUrl") or item.get("website", ""),
            "linkedin": item.get("profileUrl") or item.get("url", ""),
            "pais":     item.get("location", "").split(",")[-1].strip() if item.get("location") else "",
            "ciudad":   item.get("location", "").split(",")[0].strip() if item.get("location") else "",
            "sector":   item.get("industry", ""),
            "fuente":   "LinkedIn",
        }
    elif fuente == "google_maps":
        lead = {
            "nombre":   item.get("name", "Sin nombre"),
            "empresa":  item.get("name", ""),
            "cargo":    "Propietario/Responsable",
            "email":    item.get("email", ""),
            "telefono": item.get("phone") or item.get("phoneUnformatted", ""),
            "web":      item.get("website", ""),
            "linkedin": "",
            "pais":     item.get("country_name") or item.get("country", "España"),
            "ciudad":   item.get("city", ""),
            "sector":   ", ".join(item.get("categories", [])[:1]),  # Primera categoría
            "fuente":   "Google Maps",
        }
    else:
        lead = {
            "nombre":   item.get("name") or item.get("title", "Sin nombre"),
            "empresa":  item.get("company") or item.get("organization", ""),
            "cargo":    item.get("role") or item.get("position", ""),
            "email":    item.get("email", ""),
            "telefono": item.get("phone", ""),
            "web":      item.get("url") or item.get("website", ""),
            "linkedin": item.get("linkedin", ""),
            "pais":     item.get("country", ""),
            "ciudad":   item.get("city", ""),
            "sector":   item.get("industry") or item.get("category", ""),
            "fuente":   "Web scraping",
        }

    # Calcular puntuación (0-10)
    puntos = 0
    if lead["email"]:    puntos += 3
    if lead["empresa"]:  puntos += 2
    if lead["cargo"]:    puntos += 2
    if lead["telefono"]: puntos += 1
    if lead["linkedin"]: puntos += 1
    if lead["web"]:      puntos += 1
    lead["puntuacion"] = puntos

    return lead


def filtrar_leads(leads: list) -> list:
    """Elimina duplicados y leads de baja calidad"""
    vistos = set()
    resultado = []

    for lead in leads:
        # Clave de deduplicación
        nombre = lead.get("nombre", "Sin nombre")
        clave = (lead.get("email") or lead.get("linkedin") or nombre).lower()

        if clave in vistos or clave == "sin nombre" or clave == "":
            continue

        # Solo leads con puntuación mínima de 1 (más permisivo para debugging)
        if lead["puntuacion"] < 1:
            continue

        vistos.add(clave)
        resultado.append(lead)

    log(f"Filtrado: {len(leads)} → {len(resultado)} leads únicos y válidos", "ok")

    # Debug: mostrar primer lead rechazado si existe
    if len(leads) > 0 and len(resultado) == 0:
        log("DEBUG - Primer lead crudo:", "warn")
        log(json.dumps(leads[0], indent=2, ensure_ascii=False), "warn")

    return resultado


# ============================================================
# 3. GUARDAR EN NOTION
# ============================================================
def guardar_en_notion(leads: list) -> int:
    """Guarda los leads en la base de datos de Notion"""
    headers = {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Content-Type":   "application/json",
        "Notion-Version": "2022-06-28",
    }

    guardados = 0
    hoy = datetime.now().strftime("%Y-%m-%d")

    for lead in leads:
        payload = {
            "parent": {"database_id": NOTION_LEADS_DB},
            "properties": {
                "Nombre": {
                    "title": [{"text": {"content": lead["nombre"][:100]}}]
                },
                "Empresa": {
                    "rich_text": [{"text": {"content": lead["empresa"][:100]}}]
                },
                "Cargo": {
                    "rich_text": [{"text": {"content": lead["cargo"][:100]}}]
                },
                "Email": {
                    "email": lead["email"] if lead["email"] else None
                },
                "Teléfono": {
                    "phone_number": lead["telefono"] if lead["telefono"] else None
                },
                "Web": {
                    "url": lead["web"] if lead["web"] else None
                },
                "LinkedIn": {
                    "url": lead["linkedin"] if lead["linkedin"] else None
                },
                "Fuente": {
                    "select": {"name": lead["fuente"]}
                },
                "Estado": {
                    "select": {"name": "Nuevo"}
                },
                "Puntuación": {
                    "number": lead["puntuacion"]
                },
                "País": {
                    "rich_text": [{"text": {"content": lead["pais"][:100]}}]
                },
                "Ciudad": {
                    "rich_text": [{"text": {"content": lead["ciudad"][:100]}}]
                },
                "Sector": {
                    "rich_text": [{"text": {"content": lead["sector"][:100]}}]
                },
                "Fecha scraping": {
                    "date": {"start": hoy}
                },
            }
        }

        # Limpiar propiedades None (Notion no acepta null en algunos campos)
        for key in ["Email", "Teléfono", "Web", "LinkedIn"]:
            if payload["properties"][key].get("email") is None and key == "Email":
                del payload["properties"][key]
            elif payload["properties"][key].get("phone_number") is None and key == "Teléfono":
                del payload["properties"][key]
            elif payload["properties"][key].get("url") is None and key in ("Web", "LinkedIn"):
                del payload["properties"][key]

        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload
        )

        if resp.status_code == 200:
            guardados += 1
        else:
            log(f"Error guardando '{lead['nombre']}': {resp.text[:100]}", "warn")

        time.sleep(0.35)  # Respetar rate limit de Notion (3 req/s)

    return guardados


# ============================================================
# 4. CONSTRUIR INPUT PARA APIFY SEGÚN OBJETIVO
# ============================================================
def construir_input_linkedin(objetivo: str, limite: int) -> dict:
    """Construye el input para el LinkedIn scraper de Apify"""
    return {
        "searchUrl": f"https://www.linkedin.com/search/results/people/?keywords={objetivo.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER",
        "maxResults": limite,
        "proxyConfiguration": {"useApifyProxy": True},
    }

def construir_input_google_maps(objetivo: str, limite: int) -> dict:
    """Construye el input para el Google Maps scraper (poidata)"""
    # Parse objetivo: "agencias inmobiliarias Valencia España"
    # Extraer término y ubicación
    partes = objetivo.split()
    # Últimas 2 palabras suelen ser la ubicación
    ubicacion = " ".join(partes[-2:]) if len(partes) >= 2 else "España"
    # El resto es el término de búsqueda
    termino = " ".join(partes[:-2]) if len(partes) > 2 else partes[0]

    return {
        "term": [termino],
        "location": ubicacion,
        "total": limite,
        "language": "es",
        "country": "es",
    }


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Orbita — Agente de Scraping")
    parser.add_argument("--objetivo", type=str, default="CTOs startups SaaS España",
                        help="Qué tipo de leads buscar")
    parser.add_argument("--fuente",   type=str, default="linkedin",
                        choices=["linkedin", "google_maps"],
                        help="Fuente de datos")
    parser.add_argument("--limite",   type=int, default=50,
                        help="Máximo de leads a extraer")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Simular sin guardar en Notion")
    args = parser.parse_args()

    # Verificar credenciales
    if not APIFY_API_KEY or APIFY_API_KEY == "pega_aqui_tu_nueva_api_key":
        log("APIFY_API_KEY no configurada en el .env", "error")
        sys.exit(1)
    if not args.dry_run and (not NOTION_TOKEN or not NOTION_LEADS_DB):
        log("NOTION_TOKEN o NOTION_LEADS_DB no configurados en el .env", "error")
        sys.exit(1)

    print(f"\n{C.BOLD}{'='*55}{C.RESET}")
    print(f"{C.BOLD}  ⬡  ORBITA — Agente de Scraping{C.RESET}")
    print(f"{C.BOLD}{'='*55}{C.RESET}")
    print(f"  Objetivo : {args.objetivo}")
    print(f"  Fuente   : {args.fuente}")
    print(f"  Límite   : {args.limite} leads")
    print(f"  Modo     : {'DRY RUN (sin guardar)' if args.dry_run else 'PRODUCCIÓN'}")
    print(f"{C.BOLD}{'='*55}{C.RESET}\n")

    # 1. Construir input para Apify
    actor_id = APIFY_ACTORS[args.fuente]
    if args.fuente == "linkedin":
        input_apify = construir_input_linkedin(args.objetivo, args.limite)
    else:
        input_apify = construir_input_google_maps(args.objetivo, args.limite)

    # 2. Lanzar scraping
    run_id = lanzar_apify(actor_id, input_apify)

    # 3. Esperar y descargar resultados
    items_crudos = esperar_apify(run_id)

    if not items_crudos:
        log("No se obtuvieron resultados", "warn")
        sys.exit(0)

    # 4. Normalizar y puntuar
    # Guardar datos crudos para debugging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_crudo = f"outputs/raw_{args.fuente}_{timestamp}.json"
    os.makedirs("outputs", exist_ok=True)
    with open(archivo_crudo, "w", encoding="utf-8") as f:
        json.dump(items_crudos, f, ensure_ascii=False, indent=2)
    log(f"Datos crudos guardados en: {archivo_crudo}", "ok")

    leads = [normalizar_lead(item, args.fuente) for item in items_crudos]
    leads = filtrar_leads(leads)

    # 5. Guardar en archivo local
    archivo = f"outputs/leads_{args.fuente}_{timestamp}.json"
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    log(f"Leads guardados en: {archivo}", "ok")

    # 6. Guardar en Notion
    if not args.dry_run:
        log(f"Guardando {len(leads)} leads en Notion...", "run")
        guardados = guardar_en_notion(leads)
        log(f"✅ {guardados}/{len(leads)} leads guardados en Notion", "ok")
    else:
        log("Modo dry-run: saltando Notion", "warn")
        print(f"\nPrimeros 3 leads:\n{json.dumps(leads[:3], indent=2, ensure_ascii=False)}")

    print(f"\n{C.GREEN}{C.BOLD}🎯 Ciclo completado: {len(leads)} leads procesados{C.RESET}\n")


if __name__ == "__main__":
    main()
