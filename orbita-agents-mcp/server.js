#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Orbita API Configuration
const ORBITA_API_URL = process.env.ORBITA_API_URL || "http://187.77.74.47:8000";

class OrbitaServer {
  constructor() {
    this.server = new Server(
      {
        name: "orbita-agents",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupTools();
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "orbita_get_status",
            description: "Obtiene el estado actual de todos los agentes de Orbita (scraping, enrichment, qa, outreach)",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "orbita_get_leads",
            description: "Obtiene los leads desde la base de datos de Orbita",
            inputSchema: {
              type: "object",
              properties: {
                limit: {
                  type: "number",
                  description: "Número máximo de leads a obtener (default: 10)",
                  default: 10,
                },
              },
            },
          },
          {
            name: "orbita_launch_scraping",
            description: "Lanza el agente de scraping para obtener nuevos leads",
            inputSchema: {
              type: "object",
              properties: {
                objetivo: {
                  type: "string",
                  description: "Objetivo de búsqueda (ej: 'inmobiliarias Valencia')",
                  default: "inmobiliarias Valencia España",
                },
                fuente: {
                  type: "string",
                  description: "Fuente de datos (google_maps, linkedin, product_hunt)",
                  default: "google_maps",
                },
                limite: {
                  type: "number",
                  description: "Número máximo de leads a obtener",
                  default: 100,
                },
              },
            },
          },
          {
            name: "orbita_launch_enrichment",
            description: "Lanza el agente de enriquecimiento para buscar emails de los leads",
            inputSchema: {
              type: "object",
              properties: {
                limite: {
                  type: "number",
                  description: "Número máximo de leads a enriquecer",
                  default: 50,
                },
                dry_run: {
                  type: "boolean",
                  description: "Si true, solo simula sin guardar resultados",
                  default: false,
                },
              },
            },
          },
          {
            name: "orbita_launch_qa",
            description: "Lanza el agente de QA para validar y priorizar leads",
            inputSchema: {
              type: "object",
              properties: {
                limite: {
                  type: "number",
                  description: "Número máximo de leads a procesar",
                  default: 50,
                },
              },
            },
          },
          {
            name: "orbita_launch_outreach",
            description: "Lanza el agente de outreach para enviar emails personalizados",
            inputSchema: {
              type: "object",
              properties: {
                limite: {
                  type: "number",
                  description: "Número máximo de leads a contactar",
                  default: 20,
                },
              },
            },
          },
          {
            name: "orbita_get_config_diagnosis",
            description: "Obtiene el diagnóstico de configuración de Orbita (API keys, conexiones)",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "orbita_get_status":
            return await this.getStatus();
          case "orbita_get_leads":
            return await this.getLeads(args.limit || 10);
          case "orbita_launch_scraping":
            return await this.launchScraping(args);
          case "orbita_launch_enrichment":
            return await this.launchEnrichment(args);
          case "orbita_launch_qa":
            return await this.launchQA(args);
          case "orbita_launch_outreach":
            return await this.launchOutreach(args);
          case "orbita_get_config_diagnosis":
            return await this.getConfigDiagnosis();
          default:
            throw new Error(`Herramienta desconocida: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async apiCall(endpoint, method = "GET", body = null) {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${ORBITA_API_URL}${endpoint}`, options);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getStatus() {
    const data = await this.apiCall("/api/estado");
    
    const statusText = `
🎯 Estado de Orbita Agents

📊 Leads totales: ${data.leads_total}

🤖 Agentes:
• Scraping: ${data.agentes.scraping}
• Enrichment: ${data.agentes.enrichment}
• QA: ${data.agentes.qa}
• Outreach: ${data.agentes.outreach}

⏰ Última actualización: ${new Date(data.ts).toLocaleString('es-ES')}
    `.trim();

    return {
      content: [
        {
          type: "text",
          text: statusText,
        },
        {
          type: "text",
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  async getLeads(limit) {
    try {
      // First try SQLite endpoint
      const data = await this.apiCall(`/api/leads/db?limit=${limit}`);
      
      if (data.leads && data.leads.length > 0) {
        return this.formatLeads(data.leads, data.total);
      }
    } catch (e) {
      console.error('SQLite error, trying JSON files:', e.message);
    }
    
    // Fallback to JSON files
    try {
      const data = await this.apiCall(`/api/leads`);
      return this.formatLeads(data.leads || [], data.total || 0);
    } catch (e) {
      return {
        content: [
          {
            type: "text",
            text: `Error obtaining leads: ${e.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  formatLeads(leads, total) {
    const leadsText = `\n📋 Leads en base de datos: ${total}\n\n${leads.slice(0, 10).map((lead, i) => `
${i + 1}. ${lead.company_name || lead.name || 'Sin nombre'}
   • Web: ${lead.website || lead.domain || 'N/A'}
   • Email: ${lead.email || 'Pendiente'}
   • Teléfono: ${lead.phone || lead.telephone || 'N/A'}
   • Score: ${lead.score || 'N/A'}
   • Estado: ${lead.status || lead.estado || 'Nuevo'}
`).join('')}\n    `.trim();

    return {
      content: [
        {
          type: "text",
          text: leadsText,
        },
      ],
    };
  }

  async launchScraping(args) {
    const data = await this.apiCall("/api/scraping/lanzar", "POST", {
      objetivo: args.objetivo || "inmobiliarias Valencia España",
      fuente: args.fuente || "google_maps",
      limite: args.limite || 100,
      dry_run: false,
    });

    return {
      content: [
        {
          type: "text",
          text: `✅ Scraping iniciado\n\n${data.msg}\n\nObjetivo: ${args.objetivo}\nFuente: ${args.fuente}\nLímite: ${args.limite}`,
        },
      ],
    };
  }

  async launchEnrichment(args) {
    const data = await this.apiCall("/api/enriquecimiento/lanzar", "POST", {
      limite: args.limite || 50,
      dry_run: args.dry_run || false,
    });

    return {
      content: [
        {
          type: "text",
          text: `✅ Enriquecimiento iniciado\n\nLímite: ${args.limite || 50}\nDry run: ${args.dry_run || false}`,
        },
      ],
    };
  }

  async launchQA(args) {
    const data = await this.apiCall("/api/qa/lanzar", "POST", {
      limite: args.limite || 50,
      dry_run: false,
    });

    return {
      content: [
        {
          type: "text",
          text: `✅ QA agent iniciado\n\n${data.msg}\n\nLímite: ${args.limite || 50}`,
        },
      ],
    };
  }

  async launchOutreach(args) {
    const data = await this.apiCall("/api/outreach/lanzar", "POST", {
      limite: args.limite || 20,
      dry_run: false,
    });

    return {
      content: [
        {
          type: "text",
          text: `✅ Outreach iniciado\n\n${data.msg}\n\nLímite: ${args.limite || 20}`,
        },
      ],
    };
  }

  async getConfigDiagnosis() {
    const data = await this.apiCall("/api/config/diagnose");
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Orbita MCP Server running on stdio");
  }
}

const server = new OrbitaServer();
server.start().catch(console.error);