# ista EcoTrend CZ pro Home Assistant

Custom integrace pro Home Assistant, která zobrazuje data z [ecotrend.ista.cz](https://ecotrend.ista.cz/) jako panel v postranním menu a automaticky generované screenshoty grafů jako camera entity.

## Funkce

- **Panel v postranním menu** - přímý přístup k webové stránce ista EcoTrend CZ
- **Camera entity se screenshoty grafů** - automatické pořizování screenshotů grafů spotřeby
- **Volitelné kombinace grafů**:
  - **Teplo** - Dny, Týdny, Měsíce, Roky - Objekt, Minulý rok
  - **Teplá voda** - Dny, Týdny, Měsíce, Roky - Objekt, Minulý rok
  - **Studená voda** - Dny, Týdny, Měsíce, Roky - Minulý rok
- **Tmavé/světlé téma** - automaticky dle nastavení HA nebo ruční volba
- **Konfigurovatelný čas aktualizace** - výchozí 1x denně v 00:00

## Požadavky

### EcoTrend Screenshot Addon (povinné)

Tato integrace vyžaduje addon **EcoTrend Screenshot**, který pořizuje screenshoty z webové stránky ista EcoTrend.

#### Instalace addonu:

1. V Home Assistant přejděte do **Settings** → **Add-ons** → **Add-on Store**
2. Klikněte na tři tečky v pravém horním rohu ⋮ → **Repositories**
3. Přidejte URL: `https://github.com/hronek/EcotrendIstaCzHA`
4. Klikněte na **Add** a zavřete dialog
5. Obnovte stránku (F5)
6. Najděte **EcoTrend Screenshot** a klikněte na něj
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
7. Najděte **ista EcoTrend CZ** a klikněte na **Download**
8. Restartujte Home Assistant

### Manuální instalace

1. Stáhněte obsah tohoto repozitáře
2. Zkopírujte složku `custom_components/ecotrend_ista_cz` do složky `config/custom_components/` vašeho Home Assistant
3. Restartujte Home Assistant

## Konfigurace

1. Ujistěte se, že addon **EcoTrend Screenshot** je nainstalovaný a běží
2. Přejděte do **Settings** → **Devices & Services**
3. Klikněte na **Add Integration**
4. Vyhledejte **ista EcoTrend CZ**
5. Zadejte přihlašovací údaje k ista EcoTrend:
   - **Uživatelské jméno**: Vaše přihlašovací jméno k ista EcoTrend
   - **Heslo**: Vaše heslo k ista EcoTrend
   - **Host addonu**: localhost (výchozí)
   - **Port addonu**: 5000 (výchozí)
   - **Název panelu**: Název v postranním menu
   - **Ikona**: MDI ikona (výchozí: mdi:water-thermometer)
6. Klikněte na **Next**
7. Nakonfigurujte první kameru (graf):
   - **Typ dat**: Teplo / Teplá voda / Studená voda
   - **Interval**: Dny / Týdny / Měsíce / Roky
   - **Porovnání**: Objekt / Minulý rok
   - **Téma**: Automaticky (dle HA) / Tmavé / Světlé
   - **Interval aktualizace**: Počet minut mezi aktualizacemi (výchozí: 1440 = 24h)
   - **Čas aktualizace**: Denní čas pro aktualizaci (výchozí: 00:00)
8. Opakujte pro další kamery, nebo dokončete konfiguraci

## Použití

### Panel v postranním menu

Po konfiguraci se v postranním menu Home Assistant objeví nová položka "ista EcoTrend CZ". Kliknutím se otevře webová stránka pro ruční prohlížení.

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

Přejděte do **Settings** → **Devices & Services** → **ista EcoTrend CZ** → **Configure**

## Atributy camera entity

Každá camera entita obsahuje tyto atributy:
- `tab`: Typ dat (Teplo, Teplá voda, Studená voda)
- `interval`: Časový interval (Dny, Týdny, Měsíce, Roky)
- `comparison`: Režim porovnání (Objekt, Minulý rok)
- `theme`: Nastavené téma
- `last_update`: Čas poslední aktualizace
- `update_interval_minutes`: Interval aktualizace v minutách
- `scheduled_update_time`: Čas plánované denní aktualizace

## Známá omezení

- **Studená voda**: Podporuje pouze porovnání "Minulý rok" (ne "Objekt")
- **První screenshot**: První screenshot může trvat déle (načítání Unity WebGL)
- **Přihlášení**: Pokud se změní heslo k ista EcoTrend, je třeba aktualizovat v nastavení integrace

## Řešení problémů

### Addon se nepřipojuje
- Zkontrolujte, že addon EcoTrend Screenshot běží
- Zkontrolujte logy addonu v **Settings** → **Add-ons** → **EcoTrend Screenshot** → **Log**

### Screenshoty se neaktualizují
- Zkontrolujte přihlašovací údaje k ista EcoTrend
- Zkontrolujte logy Home Assistant pro chyby

### Prázdný screenshot
- Webová stránka ista EcoTrend může být dočasně nedostupná
- Zkuste ruční aktualizaci přes Developer Tools → Services → `homeassistant.update_entity`

## Podpora

Pokud narazíte na problémy, vytvořte [issue na GitHubu](https://github.com/hronek/EcotrendIstaCzHA/issues).

## Licence

MIT License

## Changelog

### v2.0.0
- **Nové**: Camera entity se screenshoty grafů
- **Nové**: Addon EcoTrend Screenshot pro automatické pořizování screenshotů
- **Nové**: Konfigurovatelné kombinace grafů (typ dat, interval, porovnání)
- **Nové**: Volba tmavého/světlého tématu
- **Nové**: Konfigurovatelný čas a interval aktualizace
- **Nové**: Česká a anglická lokalizace

### v1.0.0
- Počáteční verze s iframe panelem
