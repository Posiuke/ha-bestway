# Bestway Smart Hub (Home Assistant)

HACS-kompatible Home Assistant Custom Integration für Bestway / Lay-Z-Spa Whirlpools über die Gizwits Cloud.

## Installation über HACS

1. HACS öffnen → **Integrationen**
2. Menü **Benutzerdefinierte Repositories**
3. Repository-URL `https://github.com/Posiuke/ha-bestway` hinzufügen, Kategorie **Integration**
4. **Bestway Smart Hub** installieren
5. Home Assistant neu starten

## Einrichtung

1. Home Assistant → **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
2. **Bestway Smart Hub** auswählen
3. E-Mail, Passwort und API-Region eingeben (`euapi`, `usapi`, `aaapi`)

Kein YAML notwendig.

## Unterstützte Entities

### Climate
- HVAC-Modi: `heat`, `fan_only`, `off`
- Zieltemperatur setzen (`temp_set` bei v1, `Tset` bei v2)
- Aktuelle Temperatur (`temp_now`)

### Switches
- Filter (`filter_power` / `filter`)
- Bubbles (`wave_power` / `wave`)
- Heizer (`heat_power` / `heat`)

### Sensoren
- Wassertemperatur (`temp_now`, °C)
- Letztes Update (`updated_at`)

### Binary Sensoren
- Zieltemperatur erreicht (`heat_temp_reach`)
- Tastensperre (`locked`)
- Erdschlussfehler (`earth`)
- Fehlercodes `system_err1` bis `system_err9`

## Hinweise zu Pumpen v1 vs v2

Die Integration erkennt automatisch, ob ein Whirlpool v1- oder v2-Attribute meldet und verwendet die passenden Steuerbefehle:

- v1: z. B. `temp_set`, `heat_power`, `filter_power`, `wave_power`
- v2: z. B. `Tset`, `heat`, `filter`, `jet`, `wave`

## Technische Details

- Polling-Intervall: 10 Minuten
- Token-Refresh: alle 7 Tage per Re-Login
- Nach Steuerbefehl: 5 Sekunden warten, dann sofortiger Refresh
