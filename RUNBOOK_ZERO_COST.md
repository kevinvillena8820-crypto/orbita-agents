# 🚀 Orbita - Runbook de Configuración (COSTE CERO)

## Quick Start

```bash
# 1. Copiar configuración
cp .env.example .env

# 2. Instalar dependencias
pip install -r requirements.txt
pip install beautifulsoup4 requests python-dotenv jinja2

# 3. Iniciar dashboard
python3 app.py

# 4. Verificar endpoints
curl http://localhost:8000/api/config/diagnose
```

---

## Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/estado` | GET | Estado del sistema + stats de DB |
| `/api/leads` | GET | Leads desde JSON (archivos) |
| `/api/leads/db` | GET | Leads desde SQLite |
| `/api/config/diagnose` | GET | Diagnóstico de configuración |
| `/api/scraping/lanzar` | POST | Iniciar scraping |
| `/api/enriquecimiento/lanzar` | POST | Iniciar enrichment |
| `/api/qa/lanzar` | POST | Iniciar QA (scoring) |
| `/api/outreach/lanzar` | POST | Iniciar outreach (mensajes) |

---

## Pipeline Completo (Zero Cost)

### Paso 1: Scraping (sin Apify)

```bash
# Modo gratuito: lista manual de URLs
# Crear archivo data/urls.txt con una URL por línea
mkdir -p data
echo "https://example.com" > data/urls.txt

# O usar agent_scraping con fuente manual
python3 agent_scraping.py --fuente manual --limite 50
```

### Paso 2: Enrichment (gratuito)

```bash
# Ya implementado: scraping de páginas de contacto
python3 agent_enrichment.py --limite 50
```

### Paso 3: QA (scoring)

```bash
# Scoring basado en reglas (sin LLM)
python3 agent_qa.py --limite 100
```

### Paso 4: Outreach (templates)

```bash
# Mensajes deterministas (sin LLM)
python3 agent_outreach.py --limite 50
```

---

## Testing Checklist

```bash
# Smoke tests
curl -s http://localhost:8000/ | head -20
curl -s http://localhost:8000/api/estado
curl -s http://localhost:8000/api/config/diagnose

# Verificar leads en SQLite
python3 orbita_db.py
```

---

## Configuración Avanzada

### SQLite como Storage

```bash
# Los leads se guardan automáticamente en orbita.db
# Ver stats:
python3 -c "from orbita_db import get_stats; print(get_stats())"
```

### Ollama (LLM Local)

```bash
# Instalar Ollama para enrichment con IA local
brew install ollama  # macOS
# o: curl -fsSL https://ollama.com/install.sh | sh

# Iniciar Ollama
ollama serve &
ollama pull llama2

# Configurar en .env
OLLAMA_URL=http://localhost:11434
```

---

## Límites y Handling

| Recurso | Límite | Cómo manejarlo |
|---------|--------|-----------------|
| Web scraping | 1 req/segundo | Rate limiting automático |
| Notion API | 3 req/segundo | Si no hay token → SQLite |
| Ollama | RAM del VPS | Solo si hay recursos |
| SQLite | Tamaño archivo | Limpiar leads antiguos |

---

## Solución de Problemas

### "No hay archivos de leads"
```bash
# Crear directorio outputs
mkdir -p outputs

# O ejecutar scraping primero
python3 agent_scraping.py --dry-run
```

### "Module not found"
```bash
pip install -r requirements.txt
pip install beautifulsoup4 requests python-dotenv jinja2
```

### "Port already in use"
```bash
# Matar proceso anterior
pkill -f "python3 app.py"
# O usar otro puerto
PORT=8001 python3 app.py
```

---

## Archivos Creados

```
orbita-agents/
├── .env.example              # Plantilla de configuración
├── orbita_config.py          # Detección automática de modo
├── orbita_db.py              # SQLite fallback storage
├── agent_qa.py               # Scoring basado en reglas
├── agent_outreach.py         # Mensajes con templates
├── app.py                    # API actualizada con nuevos endpoints
└── ZERO_COST_PLAN.json       # Plan de implementación
```

---

## Próximos Pasos

1. **Probar endpoints**: `curl http://localhost:8000/api/config/diagnose`
2. **Ejecutar pipeline completo**: Scraping → Enrichment → QA → Outreach
3. **Verificar SQLite**: `python3 orbita_db.py`
4. **Opcional**: Instalar Ollama para enrichment con IA local