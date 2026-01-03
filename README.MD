# Ista EcoTrend CZ pro Home Assistant

Custom integrace pro Home Assistant, která přidává panel v postranním menu pro přímý přístup k webové stránce [ecotrend.ista.cz](https://ecotrend.ista.cz/).

## Funkce

- **Panel v postranním menu** - přímý přístup k webové stránce Ista EcoTrend CZ
- **Konfigurovatelný název a ikona** - můžete si přizpůsobit vzhled v menu
- Panel se načte pouze když na něj kliknete (žádné automatické načítání)

## Instalace

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

1. Přejděte do **Settings** → **Devices & Services**
2. Klikněte na **Add Integration**
3. Vyhledejte **Ista EcoTrend CZ**
4. Nastavte:
   - **URL**: https://ecotrend.ista.cz/ (výchozí)
   - **Název panelu**: Název v postranním menu
   - **Ikona**: MDI ikona (výchozí: mdi:water-thermometer)
5. Klikněte na **Submit**

## Použití

Po konfiguraci se v postranním menu Home Assistant objeví nová položka. Kliknutím se otevře webová stránka Ista EcoTrend CZ v iframe.

Panel se načte pouze když na něj kliknete - nedochází k žádnému automatickému načítání nebo refreshi.

## Podpora

Pokud narazíte na problémy, vytvořte [issue na GitHubu](https://github.com/hronek/EcotrendIstaCzHA/issues).

## Licence

MIT License

## Changelog

### v1.0.0
- Počáteční verze s iframe panelem v postranním menu
- Konfigurovatelný název a ikona
