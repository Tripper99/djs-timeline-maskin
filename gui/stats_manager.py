#!/usr/bin/env python3
"""
Statistics management mixin for DJs Timeline-maskin
Contains methods for managing and displaying application statistics
"""


class StatsManagerMixin:
    """Mixin class for statistics management functionality"""

    def get_stats_text(self) -> str:
        """Get compact statistics text"""
        return (f"PDF: {self.stats['pdfs_opened']} | "
                f"Omdöpt: {self.stats['files_renamed']} | "
                f"Excel: {self.stats['excel_rows_added']}")

    def update_stats_display(self):
        """Update statistics display"""
        self.filename_stats_label.configure(text=self.get_stats_text())
