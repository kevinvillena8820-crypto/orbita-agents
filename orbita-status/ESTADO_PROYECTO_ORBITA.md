# 📊 Estado del Proyecto Orbita

**Fecha:** 23 de Marzo de 2026  
**Actualizado por:** Kilo Code (AI Assistant)

---

## 🌐 Estado del VPS

| Propiedad | Valor |
|-----------|-------|
| **IP del VPS** | 187.77.74.47 |
| **Puerto** | 8000 |
| **Estado del contenedor** | ✅ RUNNING |
| **Uptime** | 5 días |
| **URL** | http://187.77.74.47:8000/ |

---

## 📁 Archivos del Proyecto (GitHub)

El proyecto está en: `https://github.com/kevinvillena8820-crypto/orbita-agents`

```
orbita-agents/
├── app.py                    # API FastAPI + Dashboard
├── orchestrator.py           # Orquestador principal
├── agent_scraping.py         # Agente de Scraping (Apify → Notion)
├── agent_enrichment.py       # Agente de Enriquecimiento
├── agent_qa.py               # Agente de Scoring (ZERO-COST)
├── agent_outreach.py         # Agente de Mensajes (ZERO-COST)
├── orbita_config.py          # Detección automática de configuración
├── orbita_db.py              # SQLite fallback
├── orbita-dashboard.html     # Frontend del dashboard
├── requirements.txt          # Dependencias Python
├── Dockerfile               # Imagen Docker
├── setup.sh                  # Script de setup inicial
├── CLAUDE.md                 # Instrucciones para Claude
├── RUNBOOK_ZERO_COST.md      # Manual de modo zero-cost
├── ZERO_COST_PLAN.json       # Plan de implementación
└── .env.example              # Template de variables de entorno
```

---

## 🤖 Estado de los Agentes

### ✅ Agentes Funcionales

| Agente | Estado | Descripción |
|--------|--------|-------------|
| **app.py** | ✅ Funcional | API FastAPI corriendo en puerto 8000 |
| **orbita_config.py** | ✅ Funcional | Detección automática de configuración |
| **orbita_db.py** | ✅ Funcional | SQLite fallback para almacenamiento |
| **agent_qa.py** | ✅ Funcional | Scoring de leads (modo zero-cost) |
| **agent_outreach.py** | ✅ Funcional | Generación de mensajes (modo zero-cost) |

### ⚠️ Agentes con API Keys (modo de pago)

| Agente | Estado | Descripción |
|--------|--------|-------------|
| **orchestrator.py** | ⚠️ Requiere config | Orquestador - necesita variables de entorno |
| **agent_scraping.py** | ⚠️ Requiere Apify | Scraping con Apify - necesita API keys |
| **agent_enrichment.py** | ⚠️ Requiere config | Enriquecimiento - modo zero-cost disponible |

---

## 🔑 Modos de Operación

### Modo Zero-Cost (sin API keys)
No requiere ninguna API key. El sistema usa:
- Scraping manual (importar URLs)
- Enriquecimiento HTTP (scrapping de páginas de contacto)
- Scoring basado en reglas
- Mensajes basados en plantillas

```bash
# No necesita .env para modo zero-cost
```

### Modo de Pago (requiere API keys)
```bash
# API de Apify (scraping)
APIFY_API_KEY=tu_api_key_de_apify

# Notion (base de datos de leads)
NOTION_TOKEN=tu_notion_token
NOTION_LEADS_DB=1ac85a64-4afd-42d3-9b12-2d1550d819d4

# Anthropic (para Claude)
ANTHROPIC_API_KEY=tu_api_key_de_anthropic
```

---

## 🎯 Endpoints de la API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/estado` | GET | Estado del sistema y conteo de leads |
| `/api/leads` | GET | Lista de leads |
| `/api/leads/importar` | POST | Importar leads desde URLs (modo zero-cost) |
| `/api/leads/db` | GET | Leads desde SQLite |
| `/api/scraping/lanzar` | POST | Iniciar scraping |
| `/api/enriquecimiento/lanzar` | POST | Iniciar enrichment |
| `/api/qa/lanzar` | POST | Iniciar QA |
| `/api/outreach/lanzar` | POST | Iniciar outreach |
| `/api/config/diagnose` | GET | Diagnóstico de configuración |

---

## 🔧 Estado de las Integraciones MCP

| Servicio | Estado | Descripción |
|----------|--------|-------------|
| **Hostinger VPS** | ✅ Conectado | MCP server funcionando |
| **Notion** | ⚠️ Parcial | API disponible pero BD no compartida |
| **Supabase** | ❌ Sin token | Requiere SUPABASE_ACCESS_TOKEN |

---

## 📋 Tareas Pendientes

1. **Configurar API Keys** en el VPS
   - APIFY_API_KEY
   - NOTION_TOKEN
   - ANTHROPIC_API_KEY

2. **Hacer funcionar agent_scraping.py**
   - Conectar con Apify
   - Conectar con Notion

3. **Hacer funcionar agent_enrichment.py**
   - Testing de enriquecimiento de emails

4. **Crear agent_outreach.py** (nuevo)
   - Generación de mensajes con Claude

5. **Crear agent_qa.py** (nuevo)
   - Validación de calidad de leads

6. **Mejorar dashboard**
   - Añadir gráficos
   - Mejores visualizaciones

---

## 🛠️ Herramientas Disponibles (Skills)

Tenemos acceso a skills de Claude Code que pueden ayudar:

| Skill | Uso |
|-------|-----|
| **mcp-builder** | Crear servidores MCP |
| **skill-creator** | Crear nuevos skills |
| **web-artifacts-builder** | Mejorar dashboard |
| **frontend-design** | Diseño UI |
| **webapp-testing** | Testing automático |

---

## 📝 Prompts de Sistema para Agentes (PRODUCTION)

### Prompt Base (SYSTEM) - Para TODOS los agentes LLM

```system
You are Orbita Agent, a production-grade AI worker.
Goals: accuracy, structured output, and safe automation.
Rules:

Always output valid JSON only (no markdown).

Never hallucinate data; if missing, set fields to null and add a "needs" list.

Follow the provided JSON schema exactly.

Prefer short, actionable text.

If uncertain, ask for the minimal missing input in "questions".

Keep language: Spanish for user-facing text, English for code/dev notes.
```

### 1. Prompt para orchestrator.py (Planificador + Dispatcher)

```json
{
  "task": "Decide next actions for Orbita pipeline.",
  "context": {
    "env_present": ["APIFY_API_KEY", "NOTION_TOKEN", "NOTION_LEADS_DB", "ANTHROPIC_API_KEY"],
    "env_missing": ["SUPABASE_ACCESS_TOKEN"],
    "agents": {
      "scraping": "configured=false",
      "enrichment": "configured=false",
      "outreach": "missing",
      "qa": "missing"
    },
    "constraints": {
      "max_cost": "low",
      "max_steps": 6
    }
  },
  "schema": {
    "type": "object",
    "properties": {
      "plan": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "step": { "type": "integer" },
            "agent": { "type": "string", "enum": ["scraping", "enrichment", "outreach", "qa", "ops"] },
            "priority": { "type": "string", "enum": ["P0", "P1", "P2"] },
            "action": { "type": "string" },
            "payload": { "type": "object" },
            "success_criteria": { "type": "array", "items": { "type": "string" } },
            "risks": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["step", "agent", "priority", "action", "payload", "success_criteria", "risks"]
        }
      },
      "questions": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["plan", "questions"]
  }
}
```

**Resultado:** El orchestrator ya no "piensa en texto", sino que escupe un plan ejecutable.

### 2. Prompt para agent_scraping.py (Apify → Normalización → Notion)

```json
{
  "task": "Normalize raw scraped items into Orbita lead objects for Notion.",
  "input": {
    "source": "apify",
    "items": [
      {
        "company_name": "Example Co",
        "website": "https://example.com",
        "instagram": "https://instagram.com/example",
        "country": "ES",
        "notes": "Found via directory X"
      }
    ]
  },
  "rules": [
    "Do not invent emails/phones.",
    "Derive domain from website if possible.",
    "If website missing but instagram exists, keep instagram and set domain=null.",
    "Output must be deduplicable: include a dedupe_key using normalized website domain OR instagram handle."
  ],
  "schema": {
    "type": "object",
    "properties": {
      "leads": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "company_name": { "type": "string" },
            "domain": { "type": ["string", "null"] },
            "website": { "type": ["string", "null"] },
            "instagram": { "type": ["string", "null"] },
            "country": { "type": ["string", "null"] },
            "lead_source": { "type": "string" },
            "dedupe_key": { "type": "string" },
            "confidence": { "type": "number" },
            "needs": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["company_name", "domain", "website", "instagram", "country", "lead_source", "dedupe_key", "confidence", "needs"]
        }
      }
    },
    "required": ["leads"]
  }
}
```

**Tip clave:** `dedupe_key` te salva de meter basura duplicada en Notion.

### 3. Prompt para agent_enrichment.py (Enriquecimiento sin alucinar)

```json
{
  "task": "Enrich lead with contact info using provided evidence only.",
  "lead": {
    "company_name": "Example Co",
    "domain": "example.com",
    "website": "https://example.com",
    "instagram": null
  },
  "evidence": {
    "web_snippets": [
      { "url": "https://example.com/contact", "text": "Contact us at hello@example.com" }
    ],
    "provider_results": [
      { "provider": "hunter", "emails": ["hello@example.com"], "confidence": 0.86 }
    ]
  },
  "schema": {
    "type": "object",
    "properties": {
      "enriched": {
        "type": "object",
        "properties": {
          "emails": { "type": "array", "items": { "type": "string" } },
          "phones": { "type": "array", "items": { "type": "string" } },
          "contacts": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": ["string", "null"] },
                "role": { "type": ["string", "null"] },
                "email": { "type": ["string", "null"] },
                "confidence": { "type": "number" },
                "evidence_url": { "type": ["string", "null"] }
              },
              "required": ["name", "role", "email", "confidence", "evidence_url"]
            }
          },
          "notes": { "type": "string" },
          "needs": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["emails", "phones", "contacts", "notes", "needs"]
      }
    },
    "required": ["enriched"]
  }
}
```

**Resultado:** Evita "emails inventados" y deja trazabilidad (`evidence_url`).

### 4. Prompt para agent_outreach.py (Mensajes hiper personalizados)

```json
{
  "task": "Generate personalized outreach messages for Orbita Agency.",
  "lead": {
    "company_name": "Example Co",
    "industry": "restauración",
    "city": "Madrid",
    "instagram_handle": "@example",
    "observations": [
      "Publican reels 3-4 veces/semana",
      "Buen producto pero la edición es básica",
      "No hay llamada a reservar clara"
    ]
  },
  "offer": {
    "positioning": "Órbita Agency - crecimiento en redes con contenido + sistema de captación",
    "promise": "Más reservas/leads con creatividades y automatización",
    "proof": ["Caso: +32% reservas en 21 días", "Caso: 4.2x leads con DM automation"]
  },
  "constraints": {
    "tone": "directo, premium, cero humo",
    "length": {
      "ig_dm": "max 450 chars",
      "email": "max 1400 chars",
      "whatsapp": "max 650 chars"
    }
  },
  "schema": {
    "type": "object",
    "properties": {
      "ig_dm": { "type": "string" },
      "whatsapp": { "type": "string" },
      "email": {
        "type": "object",
        "properties": {
          "subject": { "type": "string" },
          "body": { "type": "string" }
        },
        "required": ["subject", "body"]
      },
      "personalization_hooks": { "type": "array", "items": { "type": "string" } },
      "cta": { "type": "string" }
    },
    "required": ["ig_dm", "whatsapp", "email", "personalization_hooks", "cta"]
  }
}
```

**Tip:** "personalization_hooks" permite auditar si el mensaje está realmente personalizado o genérico.

### 5. Prompt para agent_qa.py (Scoring de leads + decisión)

```json
{
  "task": "Score lead quality for outreach readiness.",
  "lead": {
    "company_name": "Example Co",
    "domain": "example.com",
    "instagram": "https://instagram.com/example",
    "industry": "restauración",
    "country": "ES",
    "enriched": {
      "emails": ["hello@example.com"],
      "phones": [],
      "contacts": []
    },
    "signals": {
      "posting_frequency_per_week": 4,
      "followers": 12000,
      "has_booking_link": false,
      "content_quality": "medium"
    }
  },
  "rubric": {
    "fit": ["industry match", "geography match", "ability to pay"],
    "intent": ["active posting", "recent campaigns", "hiring"],
    "reachability": ["valid email/phone", "dm open"],
    "opportunity": ["obvious funnel leaks", "content gaps"]
  },
  "schema": {
    "type": "object",
    "properties": {
      "score_total": { "type": "integer", "minimum": 0, "maximum": 100 },
      "subscores": {
        "type": "object",
        "properties": {
          "fit": { "type": "integer", "minimum": 0, "maximum": 25 },
          "intent": { "type": "integer", "minimum": 0, "maximum": 25 },
          "reachability": { "type": "integer", "minimum": 0, "maximum": 25 },
          "opportunity": { "type": "integer", "minimum": 0, "maximum": 25 }
        },
        "required": ["fit", "intent", "reachability", "opportunity"]
      },
      "verdict": { "type": "string", "enum": ["outreach_now", "enrich_more", "discard"] },
      "reasons": { "type": "array", "items": { "type": "string" } },
      "next_actions": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["score_total", "subscores", "verdict", "reasons", "next_actions"]
  }
}
```

**Resultado:** Un "gate" automático antes de gastar tiempo en outreach.

### 6. Prompt para mejorar el dashboard

```json
{
  "task": "Propose dashboard improvements for Orbita leads pipeline.",
  "current_endpoints": ["/api/estado", "/api/leads", "/api/scraping/lanzar", "/api/enriquecimiento/lanzar"],
  "available_fields_example": ["created_at", "country", "industry", "status", "score_total", "source", "has_email"],
  "schema": {
    "type": "object",
    "properties": {
      "widgets": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "title": { "type": "string" },
            "type": { "type": "string", "enum": ["kpi", "bar", "line", "pie", "table"] },
            "metric": { "type": "string" },
            "group_by": { "type": ["string", "null"] },
            "filters": { "type": "array", "items": { "type": "string" } },
            "why_it_matters": { "type": "string" }
          },
          "required": ["title", "type", "metric", "group_by", "filters", "why_it_matters"]
        }
      },
      "api_changes": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["widgets", "api_changes"]
  }
}
```

---

## 📝 Mini-reglas de Oro (Producción)

1. **Siempre JSON-only** (nada de markdown): evita que se rompa el parser del orchestrator
2. **Campos "needs" y "questions"**: el sistema se vuelve robusto y "debuggable"
3. **Deduplicación obligatoria** (domain/handle)
4. **Veredictos discretos** (outreach_now/enrich_more/discard) para automatizar

---

## Próximos Pasos Recomendados

1. **Inmediato:** Configurar las API keys en el VPS
2. **Corto plazo:** Testear agent_scraping y agent_enrichment
3. **Medio plazo:** Crear agent_outreach y agent_qa usando los prompts proporcionados
4. **Largo plazo:** Mejorar dashboard y añadir más features