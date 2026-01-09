"""
Swedish language strings for update checking functionality
Contains all user-facing text for the GitHub version checking system
"""

# Menu items and main interface
UPDATE_STRINGS = {
    # Menu items
    "menu_check_updates": "Sök efter uppdateringar...",

    # Dialog titles
    "dialog_title_update_available": "Uppdatering tillgänglig",
    "dialog_title_checking": "Söker efter uppdateringar",
    "dialog_title_no_updates": "Inga uppdateringar",
    "dialog_title_error": "Uppdateringsfel",

    # Update available dialog
    "update_available_header": "Ny version tillgänglig!",
    "current_version_label": "Din version:",
    "new_version_label": "Ny version:",
    "release_date_label": "Släppt:",
    "release_notes_label": "Versionsinformation:",
    "available_files_label": "Tillgängliga filer:",
    "file_size_format": "{name} ({size} MB)",

    # Security indicators
    "ssl_verified": "🔒 SSL Verifierad",
    "github_official": "📦 Officiell GitHub Release",
    "download_url_label": "Kommer att öppna:",

    # Button labels
    "button_download": "Ladda ner",
    "button_skip_version": "Hoppa över denna version",
    "button_close": "Stäng",
    "button_cancel": "Avbryt",
    "button_retry": "Försök igen",

    # Progress and status messages
    "checking_for_updates": "Söker efter uppdateringar...",
    "connecting_to_github": "Ansluter till GitHub...",
    "downloading_release_info": "Hämtar versionsinformation...",
    "validating_response": "Validerar svar...",
    "checking_complete": "Kontroll slutförd",

    # Success messages
    "no_updates_available": "Du använder redan den senaste versionen!",
    "no_updates_message": "Inga uppdateringar tillgängliga för närvarande.",
    "update_check_successful": "Uppdateringskontroll slutförd framgångsrikt",

    # Version skipping
    "version_skipped": "Version {version} hoppas över",
    "version_skipped_message": "Version {version} är tillgänglig men kommer inte att visas igen.",
    "skip_version_confirmation": "Är du säker på att du vill hoppa över version {version}?",
    "skip_version_explanation": "Den här versionen kommer inte att visas igen förrän nästa version släpps.",

    # Error messages
    "error_network": "Nätverksfel",
    "error_network_message": "Kunde inte ansluta till GitHub. Kontrollera din internetanslutning.",
    "error_network_timeout": "Anslutningen tog för lång tid. Försök igen senare.",
    "error_network_ssl": "SSL-certifikatfel. Kontrollera din internetanslutning.",

    "error_rate_limit": "För många förfrågningar",
    "error_rate_limit_message": "GitHub API-gränsen har överskridits. Försök igen senare.",

    "error_validation": "Valideringsfel",
    "error_validation_message": "Ogiltigt svar från GitHub. Säkerhetsvalidering misslyckades.",

    "error_security": "Säkerhetsfel",
    "error_security_message": "Säkerhetsvalidering misslyckades. Uppdateringskontroll avbröts.",

    "error_unexpected": "Oväntat fel",
    "error_unexpected_message": "Ett oväntat fel inträffade under uppdateringskontrollen.",

    "error_no_releases": "Inga releaser hittades",
    "error_no_releases_message": "Inga releaser hittades i GitHub-arkivet.",

    "error_browser": "Kunde inte öppna webbläsare",
    "error_browser_message": "Kunde inte öppna webbläsaren automatiskt. Kopiera länken manuellt:",

    # Configuration and preferences
    "update_check_disabled": "Uppdateringskontroll inaktiverad",
    "update_check_disabled_message": "Automatisk uppdateringskontroll är inaktiverad i inställningarna.",
    "update_check_privacy_note": "Uppdateringskontroll respekterar din integritet och gör endast säkra anslutningar till GitHub.",

    # Tooltips and help text
    "tooltip_download_button": "Öppna GitHub-releasesidan i din webbläsare för säker nedladdning",
    "tooltip_skip_button": "Hoppa över denna version. Den kommer inte att visas igen.",
    "tooltip_close_button": "Stäng denna dialog utan att göra något",
    "tooltip_url_display": "Exakt URL som kommer att öppnas i webbläsaren",

    # Accessibility labels
    "aria_update_dialog": "Uppdateringsnotifiering",
    "aria_release_notes": "Versionsinformation för ny version",
    "aria_version_info": "Versionsinformation",
    "aria_progress": "Uppdateringskontroll pågår",

    # Advanced/Debug messages (for logging/troubleshooting)
    "debug_checking_version": "Kontrollerar version: nuvarande {current} vs senaste {latest}",
    "debug_api_request": "Gör API-förfrågan till GitHub",
    "debug_response_received": "Svar mottaget från GitHub API",
    "debug_validation_passed": "Säkerhetsvalidering godkänd",
    "debug_version_comparison": "Jämför versioner: {current} → {latest}",

    # Format strings for dynamic content
    "format_version_comparison": "v{current} → v{latest}",
    "format_release_date": "Släppt {date}",
    "format_file_count": "{count} fil(er) tillgängliga",
    "format_update_size": "Total storlek: {size} MB",

    # Additional informational messages
    "manual_download_note": "Alla nedladdningar sker manuellt via webbläsaren för din säkerhet.",
    "github_redirect_warning": "Du kommer att omdirigeras till GitHub för säker nedladdning.",
    "update_recommendation": "Vi rekommenderar att du uppdaterar till den senaste versionen för bästa prestanda och säkerhet.",

    # Status bar messages (if needed)
    "status_checking_updates": "Söker efter uppdateringar...",
    "status_update_available": "Uppdatering tillgänglig: v{version}",
    "status_up_to_date": "Senaste version installerad",
    "status_check_failed": "Uppdateringskontroll misslyckades",
}

# Error code mappings for more specific error messages
ERROR_CODE_MESSAGES = {
    "NETWORK_TIMEOUT": "Anslutningen tog för lång tid",
    "NETWORK_CONNECTION": "Kunde inte ansluta till internet",
    "NETWORK_SSL": "SSL-säkerhetsfel",
    "NETWORK_DNS": "DNS-upplösningsfel",
    "API_RATE_LIMIT": "GitHub API-gränsen överskreds",
    "API_NOT_FOUND": "Arkiv eller releaser hittades inte",
    "API_FORBIDDEN": "Åtkomst nekad till GitHub API",
    "VALIDATION_JSON": "Ogiltigt JSON-svar",
    "VALIDATION_VERSION": "Ogiltigt versionsformat",
    "VALIDATION_URL": "Osäker URL upptäckt",
    "SECURITY_VIOLATION": "Säkerhetsöverträdelse",
}

def get_string(key: str, **kwargs) -> str:
    """
    Get localized string with optional formatting
    
    Args:
        key: String key from UPDATE_STRINGS
        **kwargs: Format parameters for string interpolation
        
    Returns:
        Formatted localized string, or the key if not found
    """
    try:
        template = UPDATE_STRINGS.get(key, key)
        if kwargs:
            return template.format(**kwargs)
        return template
    except (KeyError, ValueError) as e:
        # Fallback to key if formatting fails
        return f"{key} (formatting error: {e})"

def get_error_message(error_code: str) -> str:
    """
    Get user-friendly error message for error code
    
    Args:
        error_code: Error code from ERROR_CODE_MESSAGES
        
    Returns:
        Localized error message
    """
    return ERROR_CODE_MESSAGES.get(error_code, UPDATE_STRINGS["error_unexpected_message"])
