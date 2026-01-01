# ista EcoTrend CZ pro Home Assistant

Custom integrace pro Home Assistant, která zobrazuje webovou stránku [ecotrend.ista.cz](https://ecotrend.ista.cz/) jako panel v postranním menu.

## Funkce

- Panel v postranním menu Home Assistant
- Zobrazení webové stránky ista EcoTrend CZ v iframe
- Možnost sledovat spotřebu tepla, teplé a studené vody

## Instalace

### HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Klikněte na "Integrations"
3. Klikněte na tři tečky v pravém horním rohu a vyberte "Custom repositories"
4. Přidejte URL: `https://github.com/hronek/EcotrendIstaCzHA`
5. Vyberte kategorii "Integration"
6. Klikněte na "Add"
7. Najděte "ista EcoTrend CZ" a klikněte na "Download"
8. Restartujte Home Assistant

### Manuální instalace

1. Stáhněte obsah tohoto repozitáře
2. Zkopírujte složku `custom_components/ecotrend_ista_cz` do složky `config/custom_components/` vašeho Home Assistant
3. Restartujte Home Assistant

## Konfigurace

1. Přejděte do **Settings** → **Devices & Services**
2. Klikněte na **Add Integration**
3. Vyhledejte **ista EcoTrend CZ**
4. Zadejte:
   - **URL**: URL adresa webu (výchozí: https://ecotrend.ista.cz/)
   - **Název panelu**: Název v postranním menu
   - **Ikona**: MDI ikona (výchozí: mdi:water-thermometer)
5. Klikněte na **Submit**

## Použití

Po konfiguraci se v postranním menu Home Assistant objeví nová položka "ista EcoTrend CZ". Kliknutím se otevře webová stránka.

**Poznámka**: Při prvním použití se musíte ručně přihlásit do ista EcoTrend. Prohlížeč si zapamatuje přihlášení pro další použití.

## Lovelace karta

Můžete také použít iframe kartu přímo na dashboardu:

```yaml
type: iframe
url: https://ecotrend.ista.cz/
aspect_ratio: 16:9
```

## Známá omezení

- **Automatické přihlášení**: Není možné kvůli bezpečnostním omezením prohlížeče
- **X-Frame-Options**: Pokud web blokuje zobrazení v iframe, panel se nemusí zobrazit správně

## Podpora

Pokud narazíte na problémy, vytvořte [issue na GitHubu](https://github.com/hronek/EcotrendIstaCzHA/issues).

## Licence

MIT License
