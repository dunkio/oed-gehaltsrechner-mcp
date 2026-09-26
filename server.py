"""
MCP Server for ÖD-Gehaltsrechner API (ÖD-Infoportal)
Standard Model Context Protocol (MCP) server for Claude Desktop, Cursor, and AI Agents.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Ensure UTF-8 I/O for MCP JSON-RPC protocol across all operating systems (crucial on Windows)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

API_BASE_URL = os.environ.get("OED_API_BASE_URL", "https://infos-oeffentlicher-dienst.de")
API_KEY = (
    os.environ.get("OED_INFOPORTAL_API_KEY", "")
    or os.environ.get("OED_API_KEY", "")
    or os.environ.get("STAATSDIENST_API_KEY", "")
)

def _fetch_api(path: str, method: str = "GET", data: dict = None) -> dict:
    url = f"{API_BASE_URL}{path}"
    headers = {
        "User-Agent": "OED-MCP-Server/1.0",
        "Accept": "application/json",
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    req_data = json.dumps(data).encode("utf-8") if data else None
    if req_data:
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            return {"error": json.loads(err_msg)}
        except Exception:
            return {"error": f"HTTP {e.code}: {err_msg}"}
    except Exception as e:
        return {"error": str(e)}

def list_tools():
    return [
        {
            "name": "get_public_sector_options",
            "description": "Liefert eine Übersicht aller Dienstherren (Bund & 16 Bundesländer) und Tarifverträge (TVöD, TV-L, etc.) mit den verfügbaren Besoldungsgruppen.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_salary_and_zulagen_options",
            "description": "DISCOVERY: Liefert für einen Dienstherrn oder Tarifvertrag und eine Gruppe alle Stufen mit Grundgehalt sowie alle wählbaren Stellenzulagen (Polizei, Justiz etc.), Amtszulagen und Familienzuschlags-Regeln.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "employment_type": {
                        "type": "string",
                        "enum": ["beamte", "tarif"],
                        "description": "'beamte' für Besoldung oder 'tarif' für Tarifverträge"
                    },
                    "dienstherr": {
                        "type": "string",
                        "description": "Dienstherr (z. B. 'bayern', 'bund', 'nordrhein-westfalen') – erforderlich wenn employment_type='beamte'"
                    },
                    "tarifvertrag": {
                        "type": "string",
                        "description": "Tarifvertrag (z. B. 'tvoed-vka', 'tv-l') – erforderlich wenn employment_type='tarif'"
                    },
                    "gruppe": {
                        "type": "string",
                        "description": "Besoldungs- oder Entgeltgruppe (z. B. 'A9', 'A13', 'E11', 'B2')"
                    }
                },
                "required": ["employment_type", "gruppe"]
            }
        },
        {
            "name": "calculate_agent_salary",
            "description": "VOLLSTÄNDIGE ÖD-BERECHNUNG & BMF-PAP: Berechnet das exakte Brutto, Netto und die jährliche Sonderzahlung inklusive ausgewählter Zulagen-IDs und bundeslandspezifischem Familienzuschlag. Die Netto-Ermittlung (Lohnsteuer, Solidaritätszuschlag, Kirchensteuer und Sozialabgaben) erfolgt exakt nach dem aktuellen Programmablaufplan (PAP) des Bundesfinanzministeriums (BMF).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "employment_type": {"type": "string", "enum": ["beamte", "tarif"], "description": "'beamte' oder 'tarif'"},
                    "dienstherr": {"type": "string", "description": "z. B. 'bayern', 'bund', 'nordrhein-westfalen'"},
                    "tarifvertrag": {"type": "string", "description": "z. B. 'tvoed-vka', 'tv-l'"},
                    "gruppe": {"type": "string", "description": "z. B. 'A9', 'A13', 'E11'"},
                    "stufe": {"type": "string", "description": "Erfahrungsstufe (z. B. '3', '4')"},
                    "selected_zulage_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste ausgewählter Zulagen-IDs aus get_salary_and_zulagen_options"
                    },
                    "familienstand": {"type": "string", "enum": ["ledig", "verheiratet"], "description": "Familienstand für Familienzuschlag Stufe 1"},
                    "kinder": {"type": "integer", "description": "Anzahl kindergeldberechtigter Kinder für Familienzuschlag"},
                    "ortsklasse": {"type": "string", "description": "Bayern Ortsklasse (i bis vii) für Orts- und Familienzuschlag"},
                    "mietenstufe": {"type": "string", "description": "NRW Mietenstufe (i bis vii) für regionalen Ergänzungszuschlag"},
                    "steuerklasse": {"type": "integer", "enum": [1, 2, 3, 4, 5, 6], "description": "Lohnsteuerklasse (1 bis 6)"},
                    "steuervier": {"type": "number", "description": "Faktor bei Steuerklasse IV mit Faktor (z. B. 0.85, Standard: 1.0)"},
                    "bundesland": {"type": "string", "description": "Bundesland für Lohnsteuer, Kirchensteuer und PV Sachsen (z. B. 'bayern', 'nordrhein-westfalen')"},
                    "kirchensteuer": {"type": "boolean", "description": "Kirchensteuerpflichtig (Standard: false)"},
                    "church_tax_rate": {"type": "number", "description": "Kirchensteuersatz (z. B. 0.08 für Bayern/BW, 0.09 für andere)"},
                    "kinderfreibetraege": {"type": "number", "description": "Zahl der Kinderfreibeträge auf LSt-Karte (z. B. 0.5, 1.0, 2.0)"},
                    "geburtsjahr": {"type": "integer", "description": "Geburtsjahr (z. B. 1990 für Altersentlastung & PV-Zuschlag für Kinderlose)"},
                    "krankenversicherung": {"type": "string", "enum": ["pkv", "gkv", "beihilfe_gkv", "pkvMit"], "description": "'pkv' (Privat), 'gkv' (Gesetzlich), 'beihilfe_gkv' (Pauschale Beihilfe), 'pkvMit' (PKV mit AG-Zuschuss)"},
                    "kvz": {"type": "number", "description": "Kassenindividueller GKV-Zusatzbeitrag in Prozent (z. B. 2.5 oder 2.9)"},
                    "pkpv": {"type": "number", "description": "Monatlicher PKV-Gesamtbeitrag des Arbeitnehmers in Euro"},
                    "pkpvgesamt": {"type": "number", "description": "Basisabsicherungsbeitrag der PKV nach Bürgerentlastungsgesetz (steuermindernd)"},
                    "kinderpflege": {"type": "integer", "description": "Anzahl Kinder unter 25 für PV-Abschlag ab dem 2. Kind (0,25 % je Kind)"},
                    "rentenversicherung": {"type": "string", "enum": ["gRV", "nein"], "description": "'gRV' (Gesetzlich rentenversichert) oder 'nein' (Beamte/Befreit)"},
                    "arbeitslosenversicherung": {"type": "string", "enum": ["gAV", "nein"], "description": "'gAV' (Arbeitslosenversichert) oder 'nein' (Beamte/Befreit)"},
                    "zusatzversorgung": {"type": "string", "description": "Betriebliche Zusatzversorgung ÖD (z. B. 'vblclassic', 'zvk' oder 'nein')"},
                    "employment_percentage": {"type": "number", "description": "Beschäftigungsumfang in Prozent (z. B. 50.0, 80.0, Standard: 100.0)"}
                },
                "required": ["employment_type", "gruppe", "stufe", "steuerklasse", "krankenversicherung"]
            }
        },
        {
            "name": "calculate_standard_salary",
            "description": "DIREKTBERECHNUNG & BRUTTO-NETTO-RECHNER: Berechnet Grundgehalt, Brutto, Netto und Sonderzahlung aus Kerndaten. Unterstützt sowohl Tarif & Besoldung ('beamte', 'tarif', 'aerzte') als auch freie Bruttobeträge ('sonstige' mit 'brutto_gehalt') mit exakter Lohnsteuer- und Sozialversicherungsberechnung nach aktuellem Programmablaufplan (PAP) des Bundesfinanzministeriums (BMF).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "employment_type": {
                        "type": "string",
                        "enum": ["beamte", "tarif", "aerzte", "sonstige"],
                        "description": "'beamte', 'tarif', 'aerzte' oder 'sonstige' (für freie Gehaltseingabe/Brutto-Netto-Rechner)"
                    },
                    "brutto_gehalt": {
                        "type": "number",
                        "description": "Fester monatlicher oder jährlicher Bruttobetrag in Euro (nur erforderlich bei employment_type='sonstige')"
                    },
                    "zeitraum_gehalt": {
                        "type": "string",
                        "enum": ["monat", "jahr"],
                        "description": "Zeitraum für brutto_gehalt: 'monat' oder 'jahr' (Standard: 'monat')"
                    },
                    "dienstherr": {"type": "string", "description": "z. B. 'bayern', 'bund' (für Beamte)"},
                    "tarifvertrag": {"type": "string", "description": "z. B. 'tvoed-vka', 'tv-l' (für Tarif)"},
                    "gruppe": {"type": "string", "description": "Besoldungs- oder Entgeltgruppe (z. B. 'A9', 'E11')"},
                    "stufe": {"type": "string", "description": "Erfahrungsstufe (z. B. '3')"},
                    "steuerklasse": {"type": "integer", "enum": [1, 2, 3, 4, 5, 6], "description": "Lohnsteuerklasse (1 bis 6)"},
                    "steuervier": {"type": "number", "description": "Faktor bei Steuerklasse IV mit Faktor (z. B. 0.85, Standard: 1.0)"},
                    "bundesland": {"type": "string", "description": "Bundesland für Lohnsteuer und Kirchensteuersatz (z. B. 'bayern', 'nordrhein-westfalen')"},
                    "kirchensteuer": {"type": "boolean", "description": "Kirchensteuerpflichtig (Standard: false)"},
                    "kinderfreibetraege": {"type": "number", "description": "Zahl der Kinderfreibeträge auf LSt-Karte (z. B. 0.5, 1.0, 2.0)"},
                    "geburtsjahr": {"type": "integer", "description": "Geburtsjahr (z. B. 1990 für Altersentlastung & PV-Zuschlag für Kinderlose)"},
                    "krankenversicherung": {"type": "string", "enum": ["pkv", "gkv", "beihilfe_gkv", "pkvMit"], "description": "'pkv' (Privat), 'gkv' (Gesetzlich), 'beihilfe_gkv' oder 'pkvMit'"},
                    "kvz": {"type": "number", "description": "Kassenindividueller GKV-Zusatzbeitrag in Prozent (z. B. 2.5 oder 2.9)"},
                    "pkpv": {"type": "number", "description": "Monatlicher PKV-Gesamtbeitrag in Euro"},
                    "pkpvgesamt": {"type": "number", "description": "Basisabsicherungsbeitrag der PKV nach Bürgerentlastungsgesetz (steuermindernd)"},
                    "kinderpflege": {"type": "integer", "description": "Anzahl Kinder unter 25 für PV-Abschlag ab dem 2. Kind (0,25 % je Kind)"},
                    "rentenversicherung": {"type": "string", "enum": ["gRV", "nein"], "description": "'gRV' (Gesetzlich rentenversichert) oder 'nein' (Beamte/Befreit)"},
                    "arbeitslosenversicherung": {"type": "string", "enum": ["gAV", "nein"], "description": "'gAV' (Arbeitslosenversichert) oder 'nein' (Beamte/Befreit)"},
                    "zusatzversorgung": {"type": "string", "description": "Betriebliche Zusatzversorgung ÖD (z. B. 'vblclassic', 'zvk' oder 'nein')"},
                    "employment_percentage": {"type": "number", "description": "Beschäftigungsumfang in Prozent (z. B. 50.0, 80.0, Standard: 100.0)"}
                },
                "required": ["employment_type", "steuerklasse", "krankenversicherung"]
            }
        }
    ]

def handle_call(tool_name: str, arguments: dict):
    if tool_name == "get_public_sector_options":
        return _fetch_api("/api/v1/options")
    elif tool_name == "get_salary_and_zulagen_options":
        params = []
        if arguments.get("employment_type"):
            params.append(f"employment_type={arguments['employment_type']}")
        if arguments.get("dienstherr"):
            params.append(f"dienstherr={arguments['dienstherr']}")
        if arguments.get("tarifvertrag"):
            params.append(f"tarifvertrag={arguments['tarifvertrag']}")
        if arguments.get("gruppe"):
            params.append(f"gruppe={arguments['gruppe']}")
        qs = "&".join(params)
        return _fetch_api(f"/api/v1/agent/options?{qs}")
    elif tool_name == "calculate_agent_salary":
        return _fetch_api("/api/v1/agent/calculate", method="POST", data=arguments)
    elif tool_name == "calculate_standard_salary":
        return _fetch_api("/api/v1/calculate", method="POST", data=arguments)
    else:
        return {"error": f"Unbekanntes Tool: {tool_name}"}

def main():
    """Standard MCP JSON-RPC Stdio Loop."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "oed-gehaltsrechner",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": list_tools()}
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result_data = handle_call(tool_name, arguments)
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(result_data, ensure_ascii=False, indent=2)}
                        ]
                    }
                }
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
