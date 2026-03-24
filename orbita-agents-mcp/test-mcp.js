#!/usr/bin/env node

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["/Users/kevinubeda/Documents/orbita-agents-mcp/server.js"],
    env: {}
  });

  const client = new Client({
    name: "orbita-test",
    version: "1.0.0"
  }, {
    capabilities: {}
  });

  await client.connect(transport);
  
  console.log("✅ Connected to Orbita MCP");
  
  // List tools
  const tools = await client.listTools();
  console.log("📋 Available tools:", tools.tools.map(t => t.name));
  
  // Get status
  try {
    const result = await client.callTool({
      name: "orbita_get_status",
      arguments: {}
    });
    console.log("📊 Status:", result.content[0].text);
  } catch (e) {
    console.log("❌ Error:", e.message);
  }
  
  // Get leads
  try {
    const result = await client.callTool({
      name: "orbita_get_leads",
      arguments: { limit: 3 }
    });
    console.log("📋 Leads:", result.content[0].text);
  } catch (e) {
    console.log("❌ Error getting leads:", e.message);
  }
  
  await client.close();
}

main().catch(console.error);