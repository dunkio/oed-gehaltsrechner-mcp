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
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False
            },
            "inputSchema": {
                "type": "object",
                "properties": {}
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "dienstherren": {
                        "type": "array",
                        "description": "Liste aller Dienstherren für Beamte (Bund und alle 16 Bundesländer)",
                        "items": {"type": "string"}
                    },
                    "tarifvertraege": {
                        "type": "array",
                        "description": "Liste aller Tarifverträge im Öffentlichen Dienst (z. B. TVöD VKA, TV-L)",
                        "items": {"type": "string"}
                    },
                    "perioden": {
                        "type": "array",
                        "description": "Verfügbare Gültigkeitszeiträume und Tarifrunden",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        {
            "name": "get_salary_and_zulagen_options",
            "description": "DISCOVERY: Liefert für einen Dienstherrn oder Tarifvertrag und eine Gruppe alle Stufen mit Grundgehalt sowie alle wählbaren Stellenzulagen (Polizei, Justiz etc.), Amtszulagen und Familienzuschlags-Regeln.",
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "employmentType": {
                        "type": "string",
                        "enum": ["beamte", "tarif"],
                        "description": "Art des Beschäftigungsverhältnisses: 'beamte' für Besoldung oder 'tarif' für Tarifverträge."
                    },
                    "dienstherr": {
                        "type": "string",
                        "description": "Dienstherr / Bundesland (z. B. 'bayern' bzw. 'by', 'bund', 'nordrhein-westfalen' bzw. 'nrw') – erforderlich wenn employmentType='beamte'."
                    },
                    "tarifvertrag": {
                        "type": "string",
                        "description": "Tarifvertrag (z. B. 'tvoed-vka', 'tv-l') – erforderlich wenn employmentType='tarif'."
                    },
                    "gruppe": {
                        "type": "string",
                        "description": "Besoldungs- oder Entgeltgruppe (z. B. 'A9', 'A13', 'E11', 'B2')."
                    },
                    "period_key": {
                        "type": "string",
                        "description": "Optionaler Gültigkeitszeitraum / Tarifrunde (z. B. '20260501_'). Standard: aktuellste Tabelle."
                    }
                },
                "required": ["employmentType", "gruppe"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "gruppe": {"type": "string", "description": "Besoldungs- oder Entgeltgruppe"},
                    "stufen": {"type": "object", "description": "Tabellen-Grundgehälter je Erfahrungsstufe"},
                    "stellenzulagen": {
                        "type": "array",
                        "description": "Wählbare Stellenzulagen und Amtszulagen mit Betrag und ID",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "betrag": {"type": "number"}
                            }
                        }
                    },
                    "familienzuschlag": {
                        "type": "object",
                        "description": "Regeln und Beträge für Ehe- und Kinderbestandteile des Familienzuschlags"
                    }
                }
            }
        },
        {
            "name": "calculate_agent_salary",
            "description": "VOLLSTÄNDIGE ÖD-BERECHNUNG & BMF-PAP: Berechnet das exakte Brutto, Netto und die jährliche Sonderzahlung inklusive ausgewählter Zulagen-IDs und bundeslandspezifischem Familienzuschlag. Die Netto-Ermittlung (Lohnsteuer, Solidaritätszuschlag, Kirchensteuer und Sozialabgaben) erfolgt exakt nach dem aktuellen Programmablaufplan (PAP) des Bundesfinanzministeriums (BMF).",
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "employmentType": {
                        "type": "string",
                        "enum": ["beamte", "tarif", "aerzte"],
                        "description": "Art des Beschäftigungsverhältnisses: 'beamte' für Besoldung, 'tarif' für Tarifverträge (z. B. TVöD, TV-L), 'aerzte' für Ärztetarife. Standard: 'beamte'."
                    },
                    "dienstherr": {
                        "type": "string",
                        "description": "Dienstherr / Bundesland bei Beamten (z. B. 'bund', 'bayern' bzw. 'by', 'nordrhein-westfalen' bzw. 'nrw'). Erforderlich wenn employmentType='beamte'."
                    },
                    "tarifvertrag": {
                        "type": "string",
                        "description": "Tarifvertrag bei Tarifbeschäftigten oder Ärzten (z. B. 'tvoed-vka', 'tvoed-bund', 'tv-l', 'tv-aerzte-vka'). Erforderlich wenn employmentType='tarif' oder 'aerzte'."
                    },
                    "gruppe": {
                        "type": "string",
                        "description": "Besoldungs- oder Entgeltgruppe (z. B. 'A9', 'A13', 'B2' für Beamte oder 'E11', 'E9b', 'S12', 'P8', 'Ä1' für Tarif). Standard: 'A9'."
                    },
                    "stufe": {
                        "type": "string",
                        "description": "Erfahrungsstufe / Dienstaltersstufe (z. B. '1', '2', '3', '4', '5', '6'). Standard: '3'."
                    },
                    "period_key": {
                        "type": "string",
                        "description": "Optionaler Gültigkeitszeitraum / Tarifrunde (z. B. '20260501_'). Standard: aktuellste Tabelle."
                    },
                    "selected_zulage_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste ausgewählter Zulagen-IDs aus get_salary_and_zulagen_options (z. B. Amtszulage, Stellenzulage)."
                    },
                    "sonstigeZulagen": {
                        "type": "number",
                        "description": "Sonstige individuelle, steuerpflichtige Monatszulage in Euro (Standard: 0.0)."
                    },
                    "familienstand": {
                        "type": "string",
                        "enum": ["ledig", "verheiratet"],
                        "description": "Familienstand für den beamtenrechtlichen Familienzuschlag Stufe 1 ('ledig' oder 'verheiratet'). Standard: 'ledig'."
                    },
                    "kinder": {
                        "type": "integer",
                        "description": "Anzahl kindergeldberechtigter Kinder für den Familienzuschlag (z. B. 0, 1, 2). Befreit zugleich vom PV-Zuschlag für Kinderlose."
                    },
                    "ortsklasse": {
                        "type": "string",
                        "enum": ["i", "ii", "iii", "iv", "v", "vi", "vii"],
                        "description": "Bayern Ortsklasse ('i' bis 'vii') für den regionalen Orts- und Familienzuschlag. Standard: 'i'."
                    },
                    "mietenstufe": {
                        "type": "string",
                        "enum": ["i", "ii", "iii", "iv", "v", "vi", "vii"],
                        "description": "NRW Mietenstufe ('i' bis 'vii') für den regionalen Ergänzungszuschlag. Standard: 'i'."
                    },
                    "steuerjahr": {
                        "type": "integer",
                        "enum": [2025, 2026],
                        "description": "Steuerjahr für den BMF-Programmablaufplan (Standard: 2026)."
                    },
                    "steuerklasse": {
                        "type": "integer",
                        "enum": [1, 2, 3, 4, 5, 6],
                        "description": "Lohnsteuerklasse (1 bis 6). Standard: 1."
                    },
                    "steuervier": {
                        "type": "number",
                        "description": "Faktor bei Steuerklasse IV mit Faktorverfahren (z. B. 0.955, Standard: 1.0)."
                    },
                    "bundesland": {
                        "type": "string",
                        "description": "Bundesland des Wohnorts für Kirchensteuersatz (8% in BY/BW vs. 9% in übrigen Ländern) und PV-Sachsenregelung (z. B. 'bayern', 'by', 'nrw'). Standard: 'bayern'."
                    },
                    "kirchensteuer": {
                        "type": "boolean",
                        "description": "Kirchensteuerpflichtig (true für ja, false für nein). Standard: false."
                    },
                    "kinderfreibetraege": {
                        "type": "number",
                        "description": "Zahl der Kinderfreibeträge auf der elektronischen Lohnsteuerkarte (z. B. 0.0, 0.5, 1.0, 1.5, 2.0). Standard: 0.0."
                    },
                    "kinderpflege": {
                        "type": "integer",
                        "description": "Anzahl Kinder unter 25 Jahren für gesetzliche PV-Staffelung ab dem 2. Kind: 0 (0-1 Kind), 1 (2 Kinder), 2 (3 Kinder), 3 (4 Kinder), 4 (5+ Kinder). Standard: 0."
                    },
                    "geburtsjahr": {
                        "type": "integer",
                        "description": "Geburtsjahr des Beschäftigten für Altersentlastung und PV-Zuschlag für Kinderlose ab 23 Jahren (Standard: 1992)."
                    },
                    "insuranceType": {
                        "type": "string",
                        "enum": ["pkvOhne", "pkvMit", "gkv", "gkvMitBeihilfe"],
                        "description": "Krankenversicherungsart: 'pkvOhne' (Private Krankenversicherung ohne Beihilfe/AG-Zuschuss – typisch für Beamte), 'pkvMit' (PKV mit AG-Zuschuss), 'gkv' (Gesetzliche Krankenversicherung – typisch bei Tarif), 'gkvMitBeihilfe' (Pauschale Beihilfe). Standard: 'pkvOhne'."
                    },
                    "gkvZusatz": {
                        "type": "number",
                        "description": "Kassenindividueller GKV-Zusatzbeitrag in Prozent (z. B. 2.9 für Bundesdurchschnitt 2026, Standard: 2.9)."
                    },
                    "pkvBeitrag": {
                        "type": "number",
                        "description": "Monatlicher PKV-Gesamtbeitrag zur privaten Kranken- und Pflegeversicherung in Euro (Standard: 0.0)."
                    },
                    "profiGesamtprivBasisKvPv": {
                        "type": "number",
                        "description": "Basisabsicherungsbeitrag der PKV nach Bürgerentlastungsgesetz in Euro (steuermindernder Vorsorgeaufwand, Standard: 0.0)."
                    },
                    "pkvZuschussArbeitgeber": {
                        "type": "number",
                        "description": "Monatlicher Arbeitgeberzuschuss zur privaten KV/PV in Euro (Standard: 0.0)."
                    },
                    "rentenversicherung": {
                        "type": "string",
                        "enum": ["nein", "gRV"],
                        "description": "Gesetzliche Rentenversicherung: 'nein' (Beamte/befreit) oder 'gRV' (gesetzlich rentenversichert). Standard: 'nein'."
                    },
                    "arbeitslosenversicherung": {
                        "type": "string",
                        "enum": ["nein", "gAV"],
                        "description": "Gesetzliche Arbeitslosenversicherung: 'nein' (Beamte/befreit) oder 'gAV' (gesetzlich versichert). Standard: 'nein'."
                    },
                    "zusatzversorgung": {
                        "type": "string",
                        "enum": ["nein", "vbl", "vbl-ost"],
                        "description": "Betriebliche Zusatzversorgung im Öffentlichen Dienst: 'nein' (Beamte/keine), 'vbl' (VBL West/klassisch), 'vbl-ost' (VBL Ost). Standard: 'nein'."
                    },
                    "employmentPercentage": {
                        "type": "number",
                        "description": "Beschäftigungsumfang in Prozent bei Teilzeit (z. B. 100.0 für Vollzeit, 80.0, 50.0). Standard: 100.0."
                    }
                },
                "required": ["employmentType", "gruppe", "stufe", "steuerklasse", "insuranceType"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "monat": {
                        "type": "object",
                        "description": "Monatliche Gehalts- und Abzugsdaten",
                        "properties": {
                            "brutto": {"type": "number", "description": "Monatliches Gesamtbrutto in Euro"},
                            "netto": {"type": "number", "description": "Monatliches Auszahlungsnetto in Euro"},
                            "lohnsteuer": {"type": "number", "description": "Monatliche Lohnsteuer nach BMF-PAP in Euro"},
                            "solidaritaetszuschlag": {"type": "number", "description": "Monatlicher Solidaritätszuschlag in Euro"},
                            "kirchensteuer": {"type": "number", "description": "Monatliche Kirchensteuer in Euro"},
                            "sozialabgaben": {"type": "object", "description": "Sozialversicherungsbeiträge (KV, PV, RV, AV)"}
                        }
                    },
                    "jahr": {
                        "type": "object",
                        "description": "Jährliche Gehaltsdaten inklusive Jahressonderzahlung",
                        "properties": {
                            "brutto": {"type": "number", "description": "Jahres-Gesamtbrutto in Euro"},
                            "netto": {"type": "number", "description": "Jahres-Netto in Euro"},
                            "sonderzahlung": {"type": "number", "description": "Jahressonderzahlung in Euro"}
                        }
                    },
                    "zulagen_berechnet": {
                        "type": "array",
                        "description": "Liste der berechneten Zulagen und Zuschläge",
                        "items": {"type": "object"}
                    }
                }
            }
        },
        {
            "name": "calculate_standard_salary",
            "description": "DIREKTBERECHNUNG & BRUTTO-NETTO-RECHNER: Berechnet Grundgehalt, Brutto, Netto und Sonderzahlung aus Kerndaten. Unterstützt sowohl Tarif & Besoldung ('beamte', 'tarif', 'aerzte') als auch freie Bruttobeträge ('sonstige' mit 'bruttoGehalt') mit exakter Lohnsteuer- und Sozialversicherungsberechnung nach aktuellem Programmablaufplan (PAP) des Bundesfinanzministeriums (BMF).",
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "employmentType": {
                        "type": "string",
                        "enum": ["beamte", "tarif", "aerzte", "sonstige"],
                        "description": "'beamte', 'tarif', 'aerzte' oder 'sonstige' (für freie Gehaltseingabe/Brutto-Netto-Rechner). Standard: 'beamte'."
                    },
                    "bruttoGehalt": {
                        "type": "number",
                        "description": "Fester monatlicher oder jährlicher Bruttobetrag in Euro (nur erforderlich bei employmentType='sonstige')."
                    },
                    "zeitraumGehalt": {
                        "type": "string",
                        "enum": ["monat", "jahr"],
                        "description": "Zeitraum für bruttoGehalt: 'monat' oder 'jahr' (Standard: 'monat')."
                    },
                    "dienstherr": {
                        "type": "string",
                        "description": "Dienstherr / Bundesland bei Beamten (z. B. 'bund', 'bayern' bzw. 'by', 'nordrhein-westfalen' bzw. 'nrw')."
                    },
                    "tarifvertrag": {
                        "type": "string",
                        "description": "Tarifvertrag bei Tarifbeschäftigten oder Ärzten (z. B. 'tvoed-vka', 'tv-l')."
                    },
                    "gruppe": {
                        "type": "string",
                        "description": "Besoldungs- oder Entgeltgruppe (z. B. 'A9', 'E11')."
                    },
                    "stufe": {
                        "type": "string",
                        "description": "Erfahrungsstufe (z. B. '3')."
                    },
                    "period_key": {
                        "type": "string",
                        "description": "Optionaler Gültigkeitszeitraum / Tarifrunde."
                    },
                    "sonstigeZulagen": {
                        "type": "number",
                        "description": "Sonstige individuelle, steuerpflichtige Monatszulage in Euro (Standard: 0.0)."
                    },
                    "steuerjahr": {
                        "type": "integer",
                        "enum": [2025, 2026],
                        "description": "Steuerjahr für den BMF-Programmablaufplan (Standard: 2026)."
                    },
                    "steuerklasse": {
                        "type": "integer",
                        "enum": [1, 2, 3, 4, 5, 6],
                        "description": "Lohnsteuerklasse (1 bis 6). Standard: 1."
                    },
                    "steuervier": {
                        "type": "number",
                        "description": "Faktor bei Steuerklasse IV mit Faktorverfahren (z. B. 0.955, Standard: 1.0)."
                    },
                    "bundesland": {
                        "type": "string",
                        "description": "Bundesland des Wohnorts für Kirchensteuersatz und PV Sachsen (z. B. 'bayern', 'by', 'nrw'). Standard: 'bayern'."
                    },
                    "kirchensteuer": {
                        "type": "boolean",
                        "description": "Kirchensteuerpflichtig (true für ja, false für nein). Standard: false."
                    },
                    "kinder": {
                        "type": "string",
                        "enum": ["ja", "nein"],
                        "description": "Gibt an, ob Kinder vorhanden sind: 'ja' oder 'nein' (befreit vom PV-Zuschlag für Kinderlose). Standard: 'nein'."
                    },
                    "kinderfreibetraege": {
                        "type": "number",
                        "description": "Zahl der Kinderfreibeträge auf der Lohnsteuerkarte (z. B. 0.0, 0.5, 1.0, 1.5, 2.0). Standard: 0.0."
                    },
                    "kinderpflege": {
                        "type": "integer",
                        "description": "Anzahl Kinder unter 25 Jahren für gesetzliche PV-Staffelung ab dem 2. Kind: 0 (0-1 Kind), 1 (2 Kinder), 2 (3 Kinder), 3 (4 Kinder), 4 (5+ Kinder). Standard: 0."
                    },
                    "geburtsjahr": {
                        "type": "integer",
                        "description": "Geburtsjahr des Beschäftigten für Altersentlastung und PV-Zuschlag (Standard: 1992)."
                    },
                    "insuranceType": {
                        "type": "string",
                        "enum": ["pkvOhne", "pkvMit", "gkv", "gkvMitBeihilfe"],
                        "description": "Krankenversicherungsart: 'pkvOhne' (Private Krankenversicherung), 'pkvMit' (PKV mit AG-Zuschuss), 'gkv' (Gesetzliche Krankenversicherung), 'gkvMitBeihilfe' (Pauschale Beihilfe). Standard: 'pkvOhne'."
                    },
                    "gkvZusatz": {
                        "type": "number",
                        "description": "Kassenindividueller GKV-Zusatzbeitrag in Prozent (z. B. 2.9 für Bundesdurchschnitt 2026, Standard: 2.9)."
                    },
                    "pkvBeitrag": {
                        "type": "number",
                        "description": "Monatlicher PKV-Gesamtbeitrag in Euro (Standard: 0.0)."
                    },
                    "profiGesamtprivBasisKvPv": {
                        "type": "number",
                        "description": "Basisabsicherungsbeitrag der PKV nach Bürgerentlastungsgesetz in Euro (Standard: 0.0)."
                    },
                    "pkvZuschussArbeitgeber": {
                        "type": "number",
                        "description": "Monatlicher Arbeitgeberzuschuss zur privaten KV/PV in Euro (Standard: 0.0)."
                    },
                    "rentenversicherung": {
                        "type": "string",
                        "enum": ["nein", "gRV"],
                        "description": "Gesetzliche Rentenversicherung: 'nein' (Beamte/befreit) oder 'gRV' (gesetzlich versichert). Standard: 'nein'."
                    },
                    "arbeitslosenversicherung": {
                        "type": "string",
                        "enum": ["nein", "gAV"],
                        "description": "Gesetzliche Arbeitslosenversicherung: 'nein' (Beamte/befreit) oder 'gAV' (gesetzlich versichert). Standard: 'nein'."
                    },
                    "zusatzversorgung": {
                        "type": "string",
                        "enum": ["nein", "vbl", "vbl-ost"],
                        "description": "Betriebliche Zusatzversorgung im Öffentlichen Dienst: 'nein' (Beamte/keine), 'vbl' (VBL West/klassisch), 'vbl-ost' (VBL Ost). Standard: 'nein'."
                    },
                    "employmentPercentage": {
                        "type": "number",
                        "description": "Beschäftigungsumfang in Prozent bei Teilzeit (z. B. 100.0, 80.0, 50.0). Standard: 100.0."
                    }
                },
                "required": ["employmentType", "steuerklasse", "insuranceType"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "monat": {
                        "type": "object",
                        "description": "Monatliche Gehalts- und Abzugsdaten",
                        "properties": {
                            "brutto": {"type": "number", "description": "Gesamtbrutto in Euro"},
                            "netto": {"type": "number", "description": "Nettoauszahlung in Euro"},
                            "lohnsteuer": {"type": "number", "description": "Lohnsteuer nach BMF-PAP in Euro"},
                            "solidaritaetszuschlag": {"type": "number", "description": "Solidaritätszuschlag in Euro"},
                            "kirchensteuer": {"type": "number", "description": "Kirchensteuer in Euro"}
                        }
                    },
                    "jahr": {
                        "type": "object",
                        "description": "Jährliche Gehaltsdaten",
                        "properties": {
                            "brutto": {"type": "number", "description": "Jahresbrutto in Euro"},
                            "netto": {"type": "number", "description": "Jahresnetto in Euro"}
                        }
                    }
                }
            }
        }
    ]

def handle_call(tool_name: str, arguments: dict):
    if tool_name == "get_public_sector_options":
        return _fetch_api("/api/v1/options")
    elif tool_name == "get_salary_and_zulagen_options":
        params = []
        emp_type = arguments.get("employmentType") or arguments.get("employment_type")
        if emp_type:
            params.append(f"employment_type={emp_type}")
        if arguments.get("dienstherr"):
            params.append(f"dienstherr={arguments['dienstherr']}")
        if arguments.get("tarifvertrag"):
            params.append(f"tarifvertrag={arguments['tarifvertrag']}")
        if arguments.get("gruppe"):
            params.append(f"gruppe={arguments['gruppe']}")
        period_k = arguments.get("period_key") or arguments.get("periodKey")
        if period_k:
            params.append(f"period_key={period_k}")
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
                            "name": "brutto-netto-gehaltsrechner",
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
