#!/usr/bin/env python3
"""
============================================================
ORBITA — Orquestador principal
Coordina todos los agentes en secuencia
============================================================
Uso desde VSCode terminal:
  python3 orchestrator.py
  python3 orchestrator.py --objetivo "Founders B2B España" --limite 100
============================================================
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class C:
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    BLUE   = "\033[94m"
    PURPLE = "\033[95m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def banner():
    print(f"""
{C.PURPLE}{C.BOLD}
  ╔═══════════════════════════════════════════╗
  ║   ⬡  ORBITA — Orquestador de Agentes     ║
  ╚═══════════════════════════════════════════╝
{C.RESET}""")

def paso(num, total, nombre):
    print(f"\n{C.BLUE}{C.BOLD}[{num}/{total}] {nombre}{C.RESET}")
    print(f"{C.BLUE}{'─'*45}{C.RESET}")

def ok(msg):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"{C.GREEN}[{hora}] ✅  {msg}{C.RESET}")

def err(msg):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"{C.RED}[{hora}] ❌  {msg}{C.RESET}")

def run_agente(script: str, args: list = []) -> bool:
    """Ejecuta un agente y devuelve True si tuvo éxito"""
    cmd = [sys.executable, script] + args
    print(f"  → Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Orbita Orchestrator")
    parser.add_argument("--objetivo", type=str, default="CTOs startups SaaS España")
    parser.add_argument("--fuente",   type=str, default="linkedin")
    parser.add_argument("--limite",   type=int, default=50)
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()

    banner()
    inicio = datetime.now()

    print(f"  Objetivo : {C.BOLD}{args.objetivo}{C.RESET}")
    print(f"  Fuente   : {args.fuente}")
    print(f"  Límite   : {args.limite} leads")
    print(f"  Inicio   : {inicio.strftime('%d/%m/%Y %H:%M:%S')}")

    pasos_ok = []
    pasos_err = []

    # ─────────────────────────────────────────
    # PASO 1: Agente de Scraping
    # ─────────────────────────────────────────
    paso(1, 3, "Agente Scraping — Apify")
    args_scraping = [
        "--objetivo", args.objetivo,
        "--fuente", args.fuente,
        "--limite", str(args.limite),
    ]
    if args.dry_run:
        args_scraping.append("--dry-run")

    if run_agente("agent_scraping.py", args_scraping):
        ok("Scraping completado")
        pasos_ok.append("Scraping")
    else:
        err("Error en scraping — continuando con datos previos si existen")
        pasos_err.append("Scraping")

    # ─────────────────────────────────────────
    # PASO 2: Claude Code — Análisis con IA
    # (Aquí puedes añadir más agentes)
    # ─────────────────────────────────────────
    paso(2, 3, "Agente IA — Cualificación de leads")
    print(f"  → Próximamente: Claude Code analizará y puntuará cada lead con IA")
    print(f"  → Por ahora la puntuación básica se hace en el agente de scraping")
    pasos_ok.append("Cualificación")
    ok("Cualificación básica completada")

    # ─────────────────────────────────────────
    # PASO 3: Resumen final
    # ─────────────────────────────────────────
    paso(3, 3, "Resumen del ciclo")

    fin = datetime.now()
    duracion = (fin - inicio).seconds

    print(f"""
  {C.BOLD}Resumen del ciclo:{C.RESET}
  ✅ Pasos OK    : {', '.join(pasos_ok) if pasos_ok else 'ninguno'}
  ❌ Pasos error : {', '.join(pasos_err) if pasos_err else 'ninguno'}
  ⏱️  Duración    : {duracion}s
  📁 Outputs     : ./outputs/
  🗂️  Notion       : https://www.notion.so/321696f2f228815f9595ef6224bf3b60
    """)

    ok(f"Ciclo completado en {duracion} segundos")


if __name__ == "__main__":
    main()
