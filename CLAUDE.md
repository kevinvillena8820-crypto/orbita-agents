# ORBITA — Instrucciones para Claude Code

Este archivo es leído automáticamente por Claude Code cuando ejecutas `claude` en esta carpeta.
Define el comportamiento y contexto del agente.

## Contexto del proyecto

Orbita es un sistema de agentes IA para generación y gestión de leads B2B.
El stack principal es Python + Apify (scraping) + Notion (base de datos de leads).

## Agentes disponibles

| Script              | Función                                      |
|---------------------|----------------------------------------------|
| `orchestrator.py`   | Orquestador principal — lanza todos los agentes |
| `agent_scraping.py` | Agente de scraping con Apify → Notion        |

## Variables de entorno necesarias (en .env)

- `APIFY_API_KEY` — API key de Apify
- `NOTION_TOKEN` — Integration token de Notion
- `NOTION_LEADS_DB` — ID de la base de datos de leads (1ac85a64-4afd-42d3-9b12-2d1550d819d4)
- `ANTHROPIC_API_KEY` — API key de Anthropic

## Comandos habituales

```bash
# Lanzar ciclo completo
python3 orchestrator.py --objetivo "CTOs SaaS España" --limite 50

# Solo scraping (sin Notion)
python3 agent_scraping.py --dry-run --objetivo "Founders Madrid"

# Scraping de negocios locales
python3 agent_scraping.py --fuente google_maps --objetivo "agencias marketing Barcelona" --limite 30
```

## Reglas para el agente Claude Code

1. NUNCA imprimas ni expongas las API keys en texto
2. Respeta el rate limit de Notion (0.35s entre requests)
3. Todos los outputs van a la carpeta `./outputs/`
4. Los logs van a `./logs/`
5. Si hay un error en Apify, guarda los datos parciales antes de salir
6. La puntuación de leads va de 0 a 10 (ver lógica en agent_scraping.py)

## Próximos agentes a implementar

- `agent_enrichment.py` — Enriquecer emails con Hunter.io o Apollo
- `agent_outreach.py` — Generar mensajes personalizados con Claude
- `agent_qa.py` — Validar calidad de leads antes de guardar en Notion
