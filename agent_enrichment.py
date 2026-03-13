#!/usr/bin/env python3
"""
============================================================
ORBITA — Agente de Enriquecimiento GRATUITO (Agente #2)
Sin APIs de pago. Encuentra emails directamente en las webs.

Estrategia (en orden):
  1. Scraping web del lead (homepage + /contacto + /contact + etc.)
  2. Regex en HTML para encontrar emails y enlaces mailto:
  3. Fallback: búsqueda Google sin API key

Uso:
  python3 agent_enrichment.py                        # JSON más reciente
  python3 agent_enrichment.py --fuente outputs/leads_google_maps_20260312_203251.json
  python3 agent_enrichment.py --limite 50
  python3 agent_enrichment.py --dry-run
============================================================
"""

import os, sys, re, json, time, glob, argparse, random
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN    = os.getenv("NOTION_TOKEN")
NOTION_LEADS_DB = os.getenv("NOTION_LEADS_DB")

RUTAS_CONTACTO = [
    "/contacto", "/contact", "/contactar",
    "/sobre-nosotros", "/about", "/quienes-somos",
    "/aviso-legal", "/legal",
]

EMAIL_BLACKLIST = [
    "example.com", "tudominio.com", "correo.com",
    "noreply@", "no-reply@", "wordpress@", "webmaster@",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

class C:
    G="\033[92m"; Y="\033[93m"; R="\033[91m"; B="\033[94m"; W="\033[0m"; BOLD="\033[1m"

def log(msg, t="info"):
    hora = datetime.now().strftime("%H:%M:%S")
    ico  = {"info":"ℹ️ ","ok":"✅","warn":"⚠️ ","error":"❌","run":"🔄"}
    col  = {"info":C.B,"ok":C.G,"warn":C.Y,"error":C.R,"run":C.B}
    print(f"{col.get(t,C.W)}[{hora}] {ico.get(t,' ')} {msg}{C.W}")

def extraer_emails(texto):
    patron = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    encontrados = re.findall(patron, texto)
    limpios = []
    for e in encontrados:
        e = e.lower().strip(".")
        if any(b in e for b in EMAIL_BLACKLIST): continue
        if len(e) > 6 and "." in e.split("@")[1]: limpios.append(e)
    vistos = set()
    return [x for x in limpios if not (x in vistos or vistos.add(x))]

def normalizar_url(web):
    if not web: return ""
    web = web.strip()
    if not web.startswith("http"): web = "https://" + web
    return web

def get_html(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout,
                         allow_redirects=True, verify=False)
        if r.status_code == 200: return r.text
    except: pass
    return ""

def buscar_en_web(web):
    if not web: return "", ""
    base = normalizar_url(web)
    dominio = urlparse(base).netloc.replace("www.", "")
    urls = [base] + [base.rstrip("/") + r for r in RUTAS_CONTACTO]

    for url in urls:
        html = get_html(url)
        if not html: continue

        # mailto: links (más fiables)
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                if a["href"].startswith("mailto:"):
                    email = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
                    if "@" in email and not any(b in email for b in EMAIL_BLACKLIST):
                        return email, f"mailto ({url.split('/')[-1] or 'home'})"
        except: pass

        # Regex en HTML completo
        emails = extraer_emails(html)
        mismo_dom = [e for e in emails if dominio in e]
        otros = [e for e in emails if e not in mismo_dom]
        candidatos = mismo_dom + otros
        if candidatos:
            ruta = url.split("/")[-1] or "home"
            return candidatos[0], f"scraping ({ruta})"

    return "", ""

def buscar_en_google(nombre, dominio):
    if not dominio: return "", ""
    query = f'"{nombre}" email contacto site:{dominio}'
    url = f"https://www.google.es/search?q={requests.utils.quote(query)}&num=5&hl=es"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            emails = extraer_emails(r.text)
            if emails: return emails[0], "google_search"
    except: pass
    return "", ""

def actualizar_notion(nombre, email, fuente):
    if not NOTION_TOKEN or not NOTION_LEADS_DB: return False
    h = {"Authorization": f"Bearer {NOTION_TOKEN}",
         "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    r = requests.post(f"https://api.notion.com/v1/databases/{NOTION_LEADS_DB}/query",
        headers=h, json={"filter": {"property": "Nombre", "title": {"equals": nombre}}})
    if r.status_code != 200: return False
    results = r.json().get("results", [])
    if not results: return False
    page_id = results[0]["id"]
    r2 = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=h,
        json={"properties": {
            "Email": {"email": email},
            "Notas": {"rich_text": [{"text": {"content": f"Email via {fuente}"}}]}
        }})
    return r2.status_code == 200

def main():
    import urllib3; urllib3.disable_warnings()

    p = argparse.ArgumentParser()
    p.add_argument("--fuente",  default="")
    p.add_argument("--limite",  type=int, default=0)
    p.add_argument("--pausa",   type=float, default=1.5)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sin-notion", action="store_true")
    args = p.parse_args()

    print(f"\n{C.BOLD}{'═'*55}{C.W}")
    print(f"{C.BOLD}  ✉️  ORBITA — Enriquecimiento GRATUITO{C.W}")
    print(f"{C.BOLD}  Web scraping + mailto + Google (sin API key){C.W}")
    print(f"{C.BOLD}{'═'*55}{C.W}\n")

    # Cargar leads
    if args.fuente:
        ruta = args.fuente
    else:
        archivos = [a for a in glob.glob("outputs/leads_*.json") if "enriquecido" not in a]
        if not archivos: log("No hay archivos en outputs/", "error"); sys.exit(1)
        ruta = max(archivos, key=os.path.getctime)
        log(f"Usando: {ruta}", "info")

    with open(ruta, encoding="utf-8") as f:
        leads = json.load(f)

    sin_email = [l for l in leads if not l.get("email")]
    con_web   = [l for l in sin_email if l.get("web")]

    log(f"Total: {len(leads)} | Sin email: {len(sin_email)} | Con web: {len(con_web)}", "info")

    a_procesar = con_web[:args.limite] if args.limite else con_web
    log(f"Procesando {len(a_procesar)} leads\n", "run")

    ok = 0; fail = 0; notion_ok = 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, lead in enumerate(a_procesar):
        nombre = lead.get("nombre", "?")
        web    = lead.get("web", "")
        dominio = urlparse(normalizar_url(web)).netloc.replace("www.", "")

        log(f"[{i+1:>3}/{len(a_procesar)}] {nombre[:45]}", "run")

        if args.dry_run:
            lead["email"] = f"info@{dominio}"; lead["email_fuente"] = "dry_run"
            log(f"   → DRY-RUN: info@{dominio}", "warn"); ok += 1
        else:
            # Estrategia 1: scraping web
            email, fuente = buscar_en_web(web)

            # Estrategia 2: Google
            if not email:
                time.sleep(0.5)
                email, fuente = buscar_en_google(nombre, dominio)

            if email:
                lead["email"] = email; lead["email_fuente"] = fuente
                log(f"   → {C.G}{email}{C.W}  [{fuente}]", "ok"); ok += 1
                if not args.sin_notion:
                    if actualizar_notion(nombre, email, fuente):
                        log(f"   → Notion ✓", "ok"); notion_ok += 1
            else:
                lead["email"] = ""; lead["email_fuente"] = ""
                log(f"   → Sin email", "warn"); fail += 1

            time.sleep(args.pausa + random.uniform(0, 0.6))

    # Guardar
    os.makedirs("outputs", exist_ok=True)
    archivo = f"outputs/leads_enriquecidos_{ts}.json"
    # Merge con leads originales
    idx = {l.get("nombre"): l for l in leads}
    for l in a_procesar: idx[l.get("nombre")] = l
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(list(idx.values()), f, ensure_ascii=False, indent=2)

    tasa = round(ok / len(a_procesar) * 100) if a_procesar else 0
    print(f"\n{C.BOLD}{'═'*55}{C.W}")
    print(f"  Procesados : {len(a_procesar)}")
    print(f"  {C.G}Emails OK : {ok}  ({tasa}%){C.W}")
    print(f"  {C.Y}Sin email : {fail}{C.W}")
    if notion_ok: print(f"  Notion OK  : {C.G}{notion_ok}{C.W}")
    print(f"  Guardado   : {archivo}")
    print(f"{C.BOLD}{'═'*55}{C.W}\n")

if __name__ == "__main__":
    main()
