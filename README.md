# ÖD-Gehaltsrechner & Brutto-Netto MCP Server (Model Context Protocol)

Offizieller Open-Source MCP-Server zur deterministischen Gehalts- und Besoldungsberechnung im deutschen Öffentlichen Dienst sowie universeller **Brutto-Netto-Rechner** für freie Gehälter nach dem offiziellen **Programmablaufplan (PAP) des Bundesfinanzministeriums (BMF)**.

[![Smithery](https://smithery.ai/badge/oed-gehaltsrechner)](https://smithery.ai/server/oed-gehaltsrechner)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Kompatibel mit **Google Antigravity**, **Claude Desktop**, **Cursor IDE**, **Windsurf** und autonomen KI-Agenten.

---

## 🛠 Enthaltene Tools

1. `get_public_sector_options`: Übersicht aller Dienstherren (Bund + 16 Länder) und Tarifverträge (TVöD, TV-L, etc.) mit Besoldungs- und Entgeltgruppen.
2. `get_salary_and_zulagen_options`: **Discovery** – Liefert Stufen mit Grundgehalt sowie alle wählbaren Stellenzulagen (Polizei, Justiz etc.), Amtszulagen und Familienzuschlags-Regeln für eine Gruppe.
3. `calculate_agent_salary`: **Vollständige ÖD-Berechnung & BMF-PAP** – Exaktes Brutto, Netto und jährliche Sonderzahlung mit ausgewählten Zulagen und bundeslandspezifischem Familienzuschlag (Ortsklasse, Mietenstufe) sowie steuerlichen Details nach BMF-PAP.
4. `calculate_standard_salary`: **Direktberechnung & Universeller Brutto-Netto-Rechner** – Schnelle Gehaltsauskunft aus Kerndaten (Besoldung & Tarif) **sowie freie Bruttobeträge** (`employment_type='sonstige'` mit `brutto_gehalt`). Berechnet Lohnsteuer, Solidaritätszuschlag, Kirchensteuer und alle Sozialabgaben (GKV, PKV, RV, AV, PV) exakt nach dem aktuellen **BMF-Programmablaufplan (PAP)**.

---

## ⚡ Installation & Einrichtung

### 1. Remote MCP (Cloud SSE – Empfohlen: Keine Python-Installation nötig!)

Verbinden Sie Claude Desktop, Cursor oder Ihren KI-Agenten direkt mit dem cloud-gehosteten Server:
- **Server URL:** `https://infos-oeffentlicher-dienst.de/mcp/sse`

**Konfiguration (Claude Desktop / Cursor SSE):**
```json
{
  "mcpServers": {
    "oed-gehaltsrechner": {
      "type": "sse",
      "url": "https://infos-oeffentlicher-dienst.de/mcp/sse?apiKey=IHR_API_KEY"
    }
  }
}
```

---

### 2. Installation via Smithery (1-Click)
```bash
npx @smithery/cli install oed-gehaltsrechner --client claude
```
Oder im Web-Interface von [Smithery.ai](https://smithery.ai):
- **Server ID:** `kio-dunker/oed-gehaltsrechner`
- **MCP Server URL:** `https://infos-oeffentlicher-dienst.de/mcp/sse`

---

### 2. Google Antigravity Einrichtung

Tragen Sie den Server in Ihre Antigravity MCP-Konfiguration ein (`~/.gemini/config/mcp_config.json`):

```json
{
  "mcpServers": {
    "staatsdienst-rechner": {
      "command": "python",
      "args": ["/Pfad/zu/oed-gehaltsrechner-mcp/server.py"],
      "env": {
        "OED_INFOPORTAL_API_KEY": "IHR_API_KEY",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

### 3. Claude Desktop Einrichtung

Fügen Sie folgenden Block in Ihre `claude_desktop_config.json` ein:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oed-gehaltsrechner": {
      "command": "python",
      "args": ["/Pfad/zu/oed-gehaltsrechner-mcp/server.py"],
      "env": {
        "OED_INFOPORTAL_API_KEY": "IHR_API_KEY",
        "OED_API_BASE_URL": "https://infos-oeffentlicher-dienst.de"
      }
    }
  }
}
```

> **API-Key:** Einen kostenlosen API-Key erhalten Sie sofort unter [infos-oeffentlicher-dienst.de/api](https://infos-oeffentlicher-dienst.de/api) oder [infos-oeffentlicher-dienst.de/mcp](https://infos-oeffentlicher-dienst.de/mcp).

---

### 4. Cursor IDE Einrichtung

Erstellen Sie in Ihrem Projekt die Datei `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "oed-gehaltsrechner": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "OED_INFOPORTAL_API_KEY": "IHR_API_KEY"
      }
    }
  }
}
```

---

## 🧪 Lokaler Test

Der MCP-Server benötigt keine externen Abhängigkeiten (nur Python 3.9+ Standardbibliothek).

Testen über die Kommandozeile (Stdio JSON-RPC):
```bash
python server.py
```

---

## 📄 Lizenz
MIT License – siehe [LICENSE](LICENSE).
