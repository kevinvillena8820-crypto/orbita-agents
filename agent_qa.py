#!/usr/bin/env python3
"""
===========================================================
ORBITA — Agente QA (Agente #4) - Scoring de Leads
Sin LLM requerido. Scoring basado en reglas.
===========================================================
Schema output:
{
  "score_total": 0-100,
  "subscores": { "fit": 0-25, "intent": 0-25, "reachability": 0-25, "opportunity": 0-25 },
  "verdict": "outreach_now" | "enrich_more" | "discard",
  "reasons": [],
  "next_actions": []
}
===========================================================
"""

import os, sys, json, glob, argparse
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
# RUBRICA DE SCORING
# ============================================================

# Industrias objetivo (alta puntuación)
TARGET_INDUSTRIES = {
    "restauración": 10, "restaurante": 10, "hostelería": 10, "hotel": 10,
    "cafetería": 9, "bar": 9, "pub": 8,
    "gimnasio": 9, "fitness": 9, "deporte": 8,
    "belleza": 9, "peluquería": 9, "estética": 9, "salón": 8,
    "tienda": 7, "comercio": 7, "retail": 7,
    "sauna": 8, "spa": 8, "wellness": 8,
}

# Países objetivo
TARGET_COUNTRIES = ["ES", "MX", "CO", "AR", "CL", "PT"]

def score_fit(lead: dict) -> int:
    """Score de ajuste (fit) - máx 25 puntos"""
    score = 0
    
    # Industry match
    industry = lead.get("industry", "").lower()
    if industry:
        score += TARGET_INDUSTRIES.get(industry, 5)
    
    # Country match
    country = lead.get("country", "")
    if country in TARGET_COUNTRIES:
        score += 10
    elif country == "":
        score += 5  # Desconocido = posibilidad
    
    # Website existe
    if lead.get("website"):
        score += 5
    
    return min(score, 25)

def score_intent(lead: dict) -> int:
    """Score de intención - máx 25 puntos"""
    score = 0
    
    # Social media activo
    if lead.get("instagram"):
        score += 10
    
    # Posting frequency (si está disponible en signals)
    signals = lead.get("signals", {})
    posting_freq = signals.get("posting_frequency_per_week", 0)
    if posting_freq >= 4:
        score += 10
    elif posting_freq >= 2:
        score += 5
    
    # Followers (proxy de tamaño)
    followers = signals.get("followers", 0)
    if followers >= 5000:
        score += 5
    
    return min(score, 25)

def score_reachability(lead: dict) -> int:
    """Score de alcanzabilidad - máx 25 puntos"""
    score = 0
    
    # Email válido
    if lead.get("enriched", {}).get("emails"):
        score += 10
    
    # Teléfono válido
    if lead.get("enriched", {}).get("phones"):
        score += 10
    
    # Instagram DM disponible
    if lead.get("instagram"):
        score += 5
    
    return min(score, 25)

def score_opportunity(lead: dict) -> int:
    """Score de oportunidad - máx 25 puntos"""
    score = 0
    
    signals = lead.get("signals", {})
    
    # No tiene link de reservas
    if not signals.get("has_booking_link"):
        score += 8
    
    # Calidad de contenido media/baja (espacio para mejorar)
    cq = signals.get("content_quality", "unknown")
    if cq in ["low", "medium"]:
        score += 7
    
    # No tiene sistema de captación
    if not lead.get("funnel"):
        score += 10
    
    return min(score, 25)

def evaluate_lead(lead: dict) -> dict:
    """Evalúa un lead y devuelve resultado"""
    
    fit = score_fit(lead)
    intent = score_intent(lead)
    reach = score_reachability(lead)
    opp = score_opportunity(lead)
    
    total = fit + intent + reach + opp
    
    # Verdict
    if total >= 60:
        verdict = "outreach_now"
    elif total >= 40 or reach >= 15:
        verdict = "enrich_more"
    else:
        verdict = "discard"
    
    # Reasons
    reasons = []
    if fit >= 15:
        reasons.append("Industria y geografía objetivo")
    if intent >= 10:
        reasons.append("Perfil activo en redes")
    if reach >= 15:
        reasons.append("Contacto disponible")
    if opp >= 10:
        reasons.append("Espacio claro para mejorar")
    if total < 40:
        reasons.append("Perfil no alineado con criterios")
    
    # Next actions
    next_actions = []
    if verdict == "outreach_now":
        next_actions = ["Generar mensajes personalizados", "Enviar primer contacto"]
    elif verdict == "enrich_more":
        next_actions = ["Intentar más enriquecimiento", "Revisar señales adicionales"]
    else:
        next_actions = ["Archivar lead", "No contactar"]
    
    return {
        "score_total": total,
        "subscores": {
            "fit": fit,
            "intent": intent,
            "reachability": reach,
            "opportunity": opp
        },
        "verdict": verdict,
        "reasons": reasons,
        "next_actions": next_actions,
        "needs": [],
        "questions": []
    }

def process_leads(leads: list, dry_run: bool = False) -> list:
    """Procesa lista de leads"""
    log(f"Evaluando {len(leads)} leads...", "run")
    
    results = []
    for i, lead in enumerate(leads):
        eval_result = evaluate_lead(lead)
        lead["qa"] = eval_result
        results.append(lead)
        
        if i < 3:  # Log primeros 3
            log(f"  {lead.get('company_name', 'Unknown')}: {eval_result['score_total']}pts → {eval_result['verdict']}", "ok")
    
    # Stats
    veredictes = {"outreach_now": 0, "enrich_more": 0, "discard": 0}
    for r in results:
        veredictes[r["qa"]["verdict"]] += 1
    
    log(f"Resultados: {veredictes}", "info")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Orbita QA Agent")
    parser.add_argument("--fuente", type=str, default=None, help="Archivo JSON de leads")
    parser.add_argument("--limite", type=int, default=100, help="Máximo leads a procesar")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    # Cargar leads
    if args.fuente:
        with open(args.fuente) as f:
            leads = json.load(f)
    else:
        # Buscar último archivo
        archivos = sorted(glob.glob("outputs/leads_*.json"), key=os.path.getmtime, reverse=True)
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
        output = f"outputs/leads_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("outputs", exist_ok=True)
        with open(output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        log(f"Guardado: {output}", "ok")
    
    print(json.dumps({"leads": results[:5], "total": len(results)}, indent=2))

if __name__ == "__main__":
    main()