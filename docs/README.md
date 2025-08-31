# DJs Timeline-maskin

En Python-applikation för att bearbeta PDF-filer och uppdatera Excel-filer med strukturerad information.
Appen kan även användas för att bara lägga till nya rader i en timeline gjord i Excel. 
Appen kan konfigureras så att excel-dokumentet skapas med de kolumnnamn användaren önskar.
Vid inmatning kan fältinnehåll låsas så att fält som ska ha samma innehåll på flera rader inte behöver fyllas i upprepade gånger. 

## Beskrivning

DJs Timeline-maskin är ett GUI-verktyg som hjälper till att:
- Bearbeta PDF-filer och extrahera textinnehåll
- Generera strukturerade filnamn baserat på PDF-innehåll
- Uppdatera Excel-filer med information från PDF-filerna alternativt bara med fältinnehåll som användaren själv fyller i.
- Hantera konfigurationer och inställningar

## Installation
Kör installationsfilen. 

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
