#!/bin/bash
# ============================================================
# ORBITA — Setup inicial del sistema de agentes
# Ejecutar UNA sola vez desde la terminal de VSCode
# ============================================================

echo "🚀 Configurando Orbita Agent OS..."

# 1. Verificar Node.js
if ! command -v node &> /dev/null; then
  echo "❌ Node.js no instalado. Descárgalo en https://nodejs.org (versión 18+)"
  exit 1
fi
echo "✅ Node.js: $(node --version)"

# 2. Verificar Python
if ! command -v python3 &> /dev/null; then
  echo "❌ Python no instalado. Descárgalo en https://python.org (versión 3.9+)"
  exit 1
fi
echo "✅ Python: $(python3 --version)"

# 3. Instalar Claude Code (CLI global)
echo "📦 Instalando Claude Code..."
npm install -g @anthropic-ai/claude-code

# 4. Instalar dependencias Python del agente
echo "📦 Instalando dependencias Python..."
pip3 install requests python-dotenv notion-client

# 5. Crear archivo .env si no existe
if [ ! -f .env ]; then
  cat > .env << 'EOF'
# ============================================================
# ORBITA — Variables de entorno
# NUNCA subas este archivo a GitHub (.gitignore ya lo excluye)
# ============================================================

# API Key de Apify (ve a console.apify.com → Settings → Integrations)
APIFY_API_KEY=pega_aqui_tu_nueva_api_key

# API Key de Anthropic (para Claude Code)
ANTHROPIC_API_KEY=pega_aqui_tu_api_key_de_anthropic

# Notion Integration Token (ve a notion.so/my-integrations)
NOTION_TOKEN=pega_aqui_tu_notion_token

# ID de tu base de datos de leads en Notion
NOTION_LEADS_DB=1ac85a64-4afd-42d3-9b12-2d1550d819d4
EOF
  echo "✅ Archivo .env creado — RELLÉNALO antes de continuar"
else
  echo "✅ Archivo .env ya existe"
fi

# 6. Crear .gitignore
cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
node_modules/
.DS_Store
outputs/
EOF
echo "✅ .gitignore creado (el .env está protegido)"

# 7. Crear carpeta de outputs
mkdir -p outputs logs

echo ""
echo "============================================================"
echo "✅ Setup completado. Próximos pasos:"
echo ""
echo "  1. Abre el archivo .env y rellena tus API keys"
echo "  2. Ejecuta: python3 agent_scraping.py"
echo "  3. O con Claude Code: claude"
echo "============================================================"
