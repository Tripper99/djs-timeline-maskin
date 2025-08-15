#!/usr/bin/env python3
"""
Statistics management mixin for DJs Timeline-maskin
Contains methods for managing and displaying application statistics
"""


class StatsManagerMixin:
    """Mixin class for statistics management functionality"""

    def get_stats_text(self) -> str:
        """Get statistics text"""
        return (f"PDF:er öppnade: {self.stats['pdfs_opened']} | "
                f"Filer omdöpta: {self.stats['files_renamed']} | "
                f"Excel-rader: {self.stats['excel_rows_added']}")

    def update_stats_display(self):
        """Update statistics display"""
        self.filename_stats_label.configure(text=self.get_stats_text())
