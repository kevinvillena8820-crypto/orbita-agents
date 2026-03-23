#!/usr/bin/env python3
"""
===========================================================
ORBITA — Agente Outreach (Agente #5) - Mensajes personalizados
Sin LLM: usa templates deterministas + opcional enhancement
===========================================================
Schema output:
{
  "ig_dm": "...",
  "whatsapp": "...",
  "email": { "subject": "...", "body": "..." },
  "personalization_hooks": [],
  "cta": "..."
}
===========================================================
"""

import os, sys, json, glob, argparse, random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# COLORES
# ============================================================
class C:
    G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; B = "\033[94m"; W = "\033[0m"; BOLD = "\033[1m"

def log(msg, t="info"):
    h = datetime.now().strftime("%H:%M:%S")
    ico = {"info": "ℹ️ ", "ok": "✅", "warn": "⚠️ ", "error": "❌", "run": "🔄"}
    col = {"info": C.B, "ok": C.G, "warn": C.Y, "error": C.R, "run": C.B}
    print(f"{col.get(t, C.W)}[{h}] {ico.get(t, '  ')} {msg}{C.W}")

# ============================================================
# TEMPLATES DE MENSAJES
# ============================================================

# Posicionamiento de Orbita Agency
POSITIONING = "Órbita Agency - crecimiento en redes con contenido + sistema deCaptación"
PROMISE = "Más reservas/leads con creatividades y automatización"
PROOF = ["Caso: +32% reservas en 21 días", "Caso: 4.2x leads con DM automation"]

# Tonos disponibles
TONES = {
    "directo": "directo, premium, cero humo",
    "amigable": "cercano, profesional pero cercano",
    "formal": "formal, corporativo"
}

# Hooks de personalización por industria
HOOKS_BY_INDUSTRY = {
    "restauración": [
        "Veo que ofrecen comida excelente pero podría llegar a más clientes",
        "Su presentación en Instagram es	top notch pero el sistema de reservas puede mejorar"
    ],
    "gimnasio": [
        "Tienen buena comunidad pero podría estar más nutrida",
        "El contenido que comparten conecta bien"
    ],
    "belleza": [
        "Su trabajo merece más visibilidad",
        "El resultado de sus tratamientos es profesional"
    ],
    "default": [
        "Vi su perfil y me interesó su proyecto",
        "Su negocio tiene potencial de crecimiento"
    ]
}

# CTAs disponibles
CTAS = [
    "¿We chat?",
    "¿Hablamos?",
    "¿Te parece sichar?",
    "¿Tienes 5 minutos?",
    "Te paso mi disponibilidad"
]

def get_hooks(industry: str) -> list:
    """Obtiene hooks relevantes para la industria"""
    industry_lower = industry.lower() if industry else ""
    for key, hooks in HOOKS_BY_INDUSTRY.items():
        if key in industry_lower:
            return hooks
    return HOOKS_BY_INDUSTRY["default"]

def get_cta() -> str:
    """Obtiene un CTA aleatorio"""
    return random.choice(CTAS)

def generate_ig_dm(lead: dict, hook: str, tone: str = "directo") -> str:
    """Genera mensaje para Instagram DM (máx 450 chars)"""
    company = lead.get("company_name", "tu negocio")
    industry = lead.get("industry", "sector")
    
    # Obtener Instagram handle
    instagram = lead.get("instagram", "")
    if instagram:
        if instagram.startswith("@"):
            handle = instagram
        elif instagram.startswith("http"):
            handle = instagram.split("/")[-1]
            if not handle.startswith("@"):
                handle = "@" + handle
        else:
            handle = "@" + instagram
    else:
        handle = ""
    
    template = f"""Hola{", "+handle if handle else ""}! 👋

{hook}

En Órbita Agencyhelamos a negocios como {company} a duplicar sus reservas con contenido que vende solo.

{sample_proof()}

¿We chat?"""
    
    if len(template) > 450:
        template = template[:447] + "..."
    
    return template.strip()

def generate_whatsapp(lead: dict, hook: str) -> str:
    """Genera mensaje para WhatsApp (máx 650 chars)"""
    company = lead.get("company_name", "tu negocio")
    
    template = f"""Hola! 👋

{hook}

Nosotros ayudamos a negocios como {company} a conseguir más clientes durch contenido en redes + automatización.

{sample_proof()}

¿Tienes 5 minutos para charlar?"""
    
    if len(template) > 650:
        template = template[:647] + "..."
    
    return template.strip()

def generate_email(lead: dict, hook: str) -> dict:
    """Genera email"""
    company = lead.get("company_name", "negocio")
    name = lead.get("contact_name", "dueño")
    
    subject = f"Cómo {company} puede duplicar reservas (sin invertir más en ads)"
    
    body = f"""Hola{name if name else ""},

{hook}

En Órbita Agencyayudamos a negocios locales a crecer con:
- Contenido que genera demanda orgánica
- Sistema de captación automatizado
- Clientela que vuelve y recomienda

{PROOF[0]}
{PROOF[1]}

¿Te parece si charlamos 10 minutos? Mi disponibilidad: [link calendly]

Saludos,
Equipo Órbita

PD: Si no es el momento, no hay problema, puedo volver a contactar en unas semanas."""

    return {"subject": subject, "body": body}

def sample_proof() -> str:
    return random.choice(PROOF)

def generate_outreach(lead: dict) -> dict:
    """Genera mensajes de outreach para un lead"""
    industry = lead.get("industry", "")
    hooks = get_hooks(industry)
    hook = random.choice(hooks)
    
    # Personalization hooks
    personalization_hooks = [
        f"Industria: {industry}" if industry else "Industria: unknown",
        f"País: {lead.get('country', 'ES')}",
        f"Instagram: {'Sí' if lead.get('instagram') else 'No'}"
    ]
    
    return {
        "ig_dm": generate_ig_dm(lead, hook),
        "whatsapp": generate_whatsapp(lead, hook),
        "email": generate_email(lead, hook),
        "personalization_hooks": personalization_hooks,
        "cta": get_cta(),
        "needs": [],
        "questions": []
    }

def process_leads(leads: list, dry_run: bool = False) -> list:
    """Procesa lista de leads y genera mensajes"""
    log(f"Generando mensajes para {len(leads)} leads...", "run")
    
    results = []
    for i, lead in enumerate(leads):
        # Solo generar para leads con verdict "outreach_now"
        qa = lead.get("qa", {})
        if qa.get("verdict") != "outreach_now":
            # Still add empty outreach
            lead["outreach"] = {"ig_dm": "", "whatsapp": "", "email": {}, "skipped": "not_ready"}
            results.append(lead)
            continue
        
        # Generar mensajes
        outreach = generate_outreach(lead)
        lead["outreach"] = outreach
        results.append(lead)
        
        if i < 2:
            log(f"  {lead.get('company_name')}: mensaje generado", "ok")
    
    # Stats
    con_mensajes = sum(1 for r in results if r.get("outreach", {}).get("ig_dm"))
    log(f"Leads con mensajes: {con_mensajes}/{len(results)}", "info")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Orbita Outreach Agent")
    parser.add_argument("--fuente", type=str, default=None, help="Archivo JSON de leads")
    parser.add_argument("--limite", type=int, default=100, help="Máximo leads a procesar")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    # Cargar leads
    if args.fuente:
        with open(args.fuente) as f:
            leads = json.load(f)
    else:
        # Buscar último archivo con QA
        archivos = sorted(glob.glob("outputs/leads_*_*.json"), key=os.path.getmtime, reverse=True)
        if not archivos:
            log("No hay archivos de leads", "error")
            return
        with open(archivos[0]) as f:
            leads = json.load(f)
    
    leads = leads[:args.limite]
    
    # Procesar
    results = process_leads(leads, args.dry_run)
    
    # Guardar
    if not args.dry_run:
        output = f"outputs/leads_outreach_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("outputs", exist_ok=True)
        with open(output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        log(f"Guardado: {output}", "ok")
    
    # Mostrar ejemplo
    for r in results:
        if r.get("outreach", {}).get("ig_dm"):
            print(json.dumps(r["outreach"], indent=2, ensure_ascii=False))
            break

if __name__ == "__main__":
    main()