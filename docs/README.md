# DJs Timeline-maskin

En Python-applikation för att bearbeta PDF-filer och uppdatera Excel-filer med strukturerad information.

## Beskrivning

DJs Timeline-maskin är ett GUI-verktyg som hjälper till att:
- Bearbeta PDF-filer och extrahera textinnehåll
- Generera strukturerade filnamn baserat på PDF-innehåll
- Uppdatera Excel-filer med information från PDF-filerna
- Hantera konfigurationer och inställningar

## Installation

### Krav
- Python 3.8 eller senare
- Pip (Python package manager)

### Installera dependencies
```bash
pip install -r requirements.txt
```

## Användning

Starta applikationen genom att köra:
```bash
python app.py
```

## Projektstruktur

```
├── app.py                    # Huvudingång för applikationen
├── core/
│   ├── config.py            # Konfigurationshantering
│   ├── pdf_processor.py     # PDF-bearbetning
│   ├── filename_parser.py   # Filnamnsparsning
│   └── excel_manager.py     # Excel-filhantering
├── gui/
│   ├── main_window.py       # Huvudfönster (GUI)
│   └── utils.py             # GUI-verktyg
├── utils/
│   └── constants.py         # Konstanter
├── requirements.txt         # Python-dependencies
└── README.md               # Denna fil
```

## Funktioner

- **PDF-bearbetning**: Läser och validerar PDF-filer
- **Filnamnsgenerering**: Skapar strukturerade filnamn från PDF-innehåll
- **Excel-integration**: Uppdaterar Excel-filer med extraherad information
- **Konfigurationshantering**: Sparar användarinställningar
- **Modernt GUI**: Byggt med ttkbootstrap för modern utseende
- **Låsning av fält**: Möjlighet att låsa fält för persistent data

## Teknisk information

- **Python-version**: 3.7+
- **GUI-ramverk**: ttkbootstrap/tkinter
- **PDF-bearbetning**: PyPDF2
- **Excel-hantering**: openpyxl

## Licens

Detta projekt är för personlig användning.

## Bidrag

Detta är ett personligt projekt.