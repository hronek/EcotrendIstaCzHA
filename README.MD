# Ista EcoTrend CZ pro Home Assistant

Custom integrace pro Home Assistant, která zobrazuje data z [ecotrend.ista.cz](https://ecotrend.ista.cz/) jako panel v postranním menu a automaticky generované screenshoty grafů jako camera entity.

## Funkce

- **Panel v postranním menu** - přímý přístup k webové stránce Ista EcoTrend CZ
- **Camera entity se screenshoty grafů** - automatické pořizování screenshotů grafů spotřeby
- **Volitelné kombinace grafů**:
  - **Teplo** - Dny, Týdny, Měsíce, Roky - Objekt, Minulý rok
  - **Teplá voda** - Dny, Týdny, Měsíce, Roky - Objekt, Minulý rok
  - **Studená voda** - Dny, Týdny, Měsíce, Roky - Minulý rok
- **Tmavé/světlé téma** - automaticky dle nastavení HA nebo ruční volba
- **Konfigurovatelný čas aktualizace** - výchozí 1x denně v 00:00

## Požadavky

### Ista EcoTrend CZ Screenshot Addon (povinné)

Tato integrace vyžaduje addon **Ista EcoTrend CZ Screenshot**, který pořizuje screenshoty z webové stránky Ista EcoTrend.

#### Instalace addonu:

1. V Home Assistant přejděte do **Settings** → **Add-ons** → **Add-on Store**
2. Klikněte na tři tečky v pravém horním rohu ⋮ → **Repositories**
3. Přidejte URL: `https://github.com/hronek/EcotrendIstaCzHA`
4. Klikněte na **Add** a zavřete dialog
5. Obnovte stránku (F5)
6. Najděte **Ista EcoTrend CZ Screenshot** a klikněte na něj
7. Klikněte na **Install**
8. Po instalaci klikněte na **Start**
9. Zkontrolujte, že addon běží (zelená ikona)

## Instalace integrace

### HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Klikněte na **Integrations**
3. Klikněte na tři tečky v pravém horním rohu a vyberte **Custom repositories**
4. Přidejte URL: `https://github.com/hronek/EcotrendIstaCzHA`
5. Vyberte kategorii **Integration**
6. Klikněte na **Add**
7. Najděte **Ista EcoTrend CZ** a klikněte na **Download**
8. Restartujte Home Assistant

### Manuální instalace

1. Stáhněte obsah tohoto repozitáře
2. Zkopírujte složku `custom_components/ecotrend_ista_cz` do složky `config/custom_components/` vašeho Home Assistant
3. Restartujte Home Assistant

## Konfigurace

1. Ujistěte se, že addon **Ista EcoTrend CZ Screenshot** je nainstalovaný a běží
2. Přejděte do **Settings** → **Devices & Services**
3. Klikněte na **Add Integration**
4. Vyhledejte **Ista EcoTrend CZ**
5. Zadejte přihlašovací údaje k Ista EcoTrend:
   - **Uživatelské jméno**: Vaše přihlašovací jméno k Ista EcoTrend
   - **Heslo**: Vaše heslo k Ista EcoTrend
   - **Port addonu**: 5000 (výchozí, volitelné - pokročilé)
   - **Název panelu**: Název v postranním menu
   - **Ikona**: MDI ikona (výchozí: mdi:water-thermometer)

   *Poznámka: IP adresa addonu se zjišťuje automaticky přes Supervisor API. Nemusíte ji zadávat ručně.*

6. Klikněte na **Next**
7. Nakonfigurujte první kameru (graf):
   - **Typ dat**: Teplo / Teplá voda / Studená voda *(povinné)*
   - **Interval**: Dny / Týdny / Měsíce / Roky *(volitelné, výchozí: Měsíce)*
   - **Porovnání**: Objekt / Minulý rok *(volitelné, výchozí: Minulý rok)*
   - **Téma**: Automaticky (dle HA) / Tmavé / Světlé
   - **Interval aktualizace**: Počet minut mezi aktualizacemi (výchozí: 1440 = 24h)
   - **Čas aktualizace**: Denní čas pro aktualizaci (výchozí: 00:00)
8. Screenshot se načte okamžitě po konfiguraci
9. Opakujte pro další kamery, nebo dokončete konfiguraci

## Použití

### Panel v postranním menu

Po konfiguraci se v postranním menu Home Assistant objeví nová položka "Ista EcoTrend CZ". Kliknutím se otevře webová stránka pro ruční prohlížení.

### Camera entity v Lovelace

Každá nakonfigurovaná kombinace vytvoří camera entitu, kterou můžete zobrazit na dashboardu:

```yaml
type: picture-entity
entity: camera.ecotrend_teplo_mesice_minuly_rok_0
show_state: false
```

Nebo použijte kartu Picture Glance:

```yaml
type: picture-glance
entities: []
camera_image: camera.ecotrend_teplo_mesice_minuly_rok_0
camera_view: auto
```

### Více grafů na dashboardu

```yaml
type: horizontal-stack
cards:
  - type: picture-entity
    entity: camera.ecotrend_teplo_mesice_minuly_rok_0
    show_state: false
  - type: picture-entity
    entity: camera.ecotrend_tepla_voda_mesice_minuly_rok_1
    show_state: false
```

## Správa kamer

V nastavení integrace můžete:
- **Upravit přihlašovací údaje**
- **Odebrat existující kamery**
- **Přidat nové kamery**

Přejděte do **Settings** → **Devices & Services** → **Ista EcoTrend CZ** → **Configure**

## Atributy camera entity

Každá camera entita obsahuje tyto atributy:
- `tab`: Typ dat (Teplo, Teplá voda, Studená voda)
- `interval`: Časový interval (Dny, Týdny, Měsíce, Roky)
- `comparison`: Režim porovnání (Objekt, Minulý rok)
- `theme`: Nastavené téma
- `last_update`: Čas poslední aktualizace
- `update_interval_minutes`: Interval aktualizace v minutách
- `scheduled_update_time`: Čas plánované denní aktualizace

## Manuální aktualizace screenshotu

Pokud chcete screenshot aktualizovat okamžitě (mimo plánovaný čas), můžete použít službu:

**Developer Tools → Services:**
```yaml
service: ecotrend_ista_cz.refresh_screenshot
data:
  entity_id: camera.ecotrend_teplo_mesice_minuly_rok_0
```

Nebo v automatizaci:
```yaml
service: ecotrend_ista_cz.refresh_screenshot
target:
  entity_id: camera.ecotrend_teplo_mesice_minuly_rok_0
```

## Známá omezení

- **Studená voda**: Podporuje pouze porovnání "Minulý rok" (ne "Objekt")
- **První screenshot**: První screenshot může trvat déle (načítání Unity WebGL)
- **Přihlášení**: Pokud se změní heslo k Ista EcoTrend, je třeba aktualizovat v nastavení integrace

## Řešení problémů

### Addon nebyl nalezen během konfigurace
- Ujistěte se, že addon **Ista EcoTrend CZ Screenshot** je nainstalovaný
- Zkontrolujte, že addon je spuštěný (zelená ikona v Add-ons)
- Integrace automaticky najde addon přes Supervisor API

### Addon se nepřipojuje
- Zkontrolujte, že addon Ista EcoTrend CZ Screenshot běží
- Zkontrolujte logy addonu v **Settings** → **Add-ons** → **Ista EcoTrend CZ Screenshot** → **Log**
- IP adresa addonu se zjišťuje automaticky, není třeba ji zadávat ručně

### Screenshoty se neaktualizují
- Zkontrolujte přihlašovací údaje k Ista EcoTrend
- Zkontrolujte logy Home Assistant pro chyby
- Zkuste manuální aktualizaci přes službu `ecotrend_ista_cz.refresh_screenshot`

### Prázdný screenshot
- Webová stránka Ista EcoTrend může být dočasně nedostupná
- Zkuste ruční aktualizaci přes službu `ecotrend_ista_cz.refresh_screenshot`
- První screenshot po instalaci se načítá okamžitě, ale může trvat déle (Unity WebGL)

## Podpora

Pokud narazíte na problémy, vytvořte [issue na GitHubu](https://github.com/hronek/EcotrendIstaCzHA/issues).

## Licence

MIT License

## Changelog

### v3.0.0
- **Nové**: Automatické zjišťování addon IP přes Supervisor API
- **Vylepšení**: Interval a porovnání jsou nyní volitelné (výchozí: Měsíce, Minulý rok)
- **Vylepšení**: Screenshot se načítá okamžitě po konfiguraci kamery
- **Nové**: Služba `ecotrend_ista_cz.refresh_screenshot` pro manuální aktualizaci
- **Vylepšení**: Lepší chybové hlášky při konfiguraci (addon nenalezen, neběží)
- **Oprava**: Odstraněno ruční zadávání IP adresy addonu
- **Optimalizace**: Přidány paměťové optimalizace pro Chromium na Raspberry Pi

### v2.0.0
- **Nové**: Camera entity se screenshoty grafů
- **Nové**: Addon Ista EcoTrend CZ Screenshot pro automatické pořizování screenshotů
- **Nové**: Konfigurovatelné kombinace grafů (typ dat, interval, porovnání)
- **Nové**: Volba tmavého/světlého tématu
- **Nové**: Konfigurovatelný čas a interval aktualizace
- **Nové**: Česká a anglická lokalizace

### v1.0.0
- Počáteční verze s iframe panelem
