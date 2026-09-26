# ÖD-Gehaltsrechner & Brutto-Netto MCP Server (Model Context Protocol)

Offizieller Open-Source MCP-Server zur deterministischen Gehalts- und Besoldungsberechnung im deutschen Öffentlichen Dienst sowie universeller **Brutto-Netto-Rechner** für freie Gehälter nach dem offiziellen **Programmablaufplan (PAP) des Bundesfinanzministeriums (BMF)**.

[![Smithery](https://smithery.ai/badge/@dunkio/brutto-netto-gehaltsrechner)](https://smithery.ai/server/@dunkio/brutto-netto-gehaltsrechner)
[![Glama](https://glama.ai/mcp/servers/@dunkio/brutto-netto-gehaltsrechner/badge)](https://glama.ai/mcp/servers/@dunkio/brutto-netto-gehaltsrechner)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Kompatibel mit **Google Antigravity**, **Claude Desktop**, **Cursor IDE**, **Windsurf** und autonomen KI-Agenten.

---

## 🛠 Enthaltene Tools

1. `get_public_sector_options`: Übersicht aller Dienstherren (Bund + 16 Länder) und Tarifverträge (TVöD, TV-L etc.) mit Besoldungs- und Entgeltgruppen.
2. `get_salary_and_zulagen_options`: **Discovery** – Liefert Stufen mit Grundgehalt sowie alle wählbaren Stellenzulagen (Polizei, Justiz etc.), Amtszulagen und Familienzuschlags-Regeln für eine Gruppe.
3. `calculate_agent_salary`: **Vollständige ÖD-Berechnung & BMF-PAP** – Exaktes Brutto, Netto und jährliche Sonderzahlung mit ausgewählten Zulagen und bundeslandspezifischem Familienzuschlag (Ortsklasse, Mietenstufe) sowie steuerlichen Details nach BMF-PAP.
4. `calculate_standard_salary`: **Direktberechnung & Universeller Brutto-Netto-Rechner** – Schnelle Gehaltsauskunft aus Kerndaten (Besoldung & Tarif) **sowie freie Bruttobeträge** (`employment_type='sonstige'` mit `brutto_gehalt`). Berechnet Lohnsteuer, Solidaritätszuschlag, Kirchensteuer und alle Sozialabgaben (GKV, PKV, RV, AV, PV) exakt nach dem aktuellen **BMF-Programmablaufplan (PAP)**.

---

## ⚡ Installation & Einrichtung

### 1. Remote MCP (Cloud SSE & Streamable HTTP – Empfohlen)

Keine lokale Python-Installation nötig! Verbinden Sie Claude Desktop, Cursor oder Ihren KI-Agenten direkt mit dem cloud-gehosteten Server:

- **Server URL:** `https://infos-oeffentlicher-dienst.de/mcp/sse` (oder Streamable HTTP: `https://infos-oeffentlicher-dienst.de/mcp`)

**Konfiguration (Claude Desktop / Cursor Remote SSE):**
```json
{
  "mcpServers": {
    "brutto-netto-gehaltsrechner": {
      "type": "sse",
      "url": "https://infos-oeffentlicher-dienst.de/mcp/sse?apiKey=IHR_API_KEY"
    }
  }
}
```

---

### 2. Installation via Smithery (1-Click)

```bash
npx @smithery/cli install @dunkio/brutto-netto-gehaltsrechner --client claude
```

Oder im Web-Interface von [Smithery.ai](https://smithery.ai/server/@dunkio/brutto-netto-gehaltsrechner):
- **Server ID:** `@dunkio/brutto-netto-gehaltsrechner`
- **MCP Server URL:** `https://infos-oeffentlicher-dienst.de/mcp/sse`

---

### 3. Google Antigravity Einrichtung

Tragen Sie den Server in Ihre Antigravity MCP-Konfiguration ein (`~/.gemini/config/mcp_config.json`):

```json
{
  "mcpServers": {
    "brutto-netto-gehaltsrechner": {
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

### 4. Claude Desktop Einrichtung (Stdio)

Fügen Sie folgenden Block in Ihre `claude_desktop_config.json` ein:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "brutto-netto-gehaltsrechner": {
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

### 5. Cursor IDE Einrichtung

Erstellen Sie in Ihrem Projekt die Datei `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "brutto-netto-gehaltsrechner": {
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

## 💬 Beispiel-Prompts für Chat & Agenten

Sobald der Server aktiv ist, versteht Ihre KI natürliche Fragen und liefert centgenaue Ergebnisse:

- **Beamtenbesoldung & Familie:**  
  *„Was verdiene ich als Grundschullehrer A13 Stufe 4 in Bayern netto, wenn ich verheiratet bin und 2 Kinder habe?“*
- **Tarifvertrag TVöD:**  
  *„Berechne das TVöD-VKA Entgelt für Gruppe E11 Stufe 3 im Jahr 2026 bei Vollzeit mit VBL.“*
- **Zulagen & Dienstherren:**  
  *„Welche Stellenzulagen gibt es für einen Polizeikommissar A9 beim Bund?“*
- **Freier Brutto-Netto-Rechner (PAP BMF):**  
  *„Berechne mein Nettogehalt bei 4.500 € Brutto als Angestellter in Steuerklasse 1 in NRW.“*

---

## 🧪 Lokaler Test

Der MCP-Server benötigt keine externen pip-Pakete (nur Python 3.9+ Standardbibliothek).

Testen über die Kommandozeile (Stdio JSON-RPC):
```bash
python server.py
```

---

## 🌐 Verzeichnisse & Registries

- **Smithery:** [smithery.ai/server/@dunkio/brutto-netto-gehaltsrechner](https://smithery.ai/server/@dunkio/brutto-netto-gehaltsrechner)
- **Glama:** [glama.ai/mcp/servers/@dunkio/brutto-netto-gehaltsrechner](https://glama.ai/mcp/servers/@dunkio/brutto-netto-gehaltsrechner)
- **OpenAPI:** [infos-oeffentlicher-dienst.de/openapi.json](https://infos-oeffentlicher-dienst.de/openapi.json) (für Toolhouse, Composio, LangChain)
- **Web-Dokumentation & Playground:** [infos-oeffentlicher-dienst.de/mcp](https://infos-oeffentlicher-dienst.de/mcp)

---

## 📄 Lizenz
MIT License – siehe [LICENSE](LICENSE).
