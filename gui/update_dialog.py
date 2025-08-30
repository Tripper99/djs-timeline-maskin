"""
Update dialog for GitHub version checking
CustomTkinter-based dialog for displaying available updates with Swedish language support
"""

import logging
import threading
import webbrowser
from typing import Callable

import customtkinter as ctk

from core.config import ConfigManager
from core.version_checker.models import UpdateCheckResult, UpdateInfo
from utils.update_strings import get_string

logger = logging.getLogger(__name__)


class UpdateProgressDialog(ctk.CTkToplevel):
    """Progress dialog shown during update checking"""

    def __init__(self, parent, check_callback: Callable):
        super().__init__()
        self.parent = parent
        self.check_callback = check_callback
        self.cancelled = False

        self.setup_window()
        self.create_widgets()
        self.start_check()

    def setup_window(self):
        """Configure the progress window"""
        self.title(get_string("dialog_title_checking"))
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(self.parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 200
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 75
        self.geometry(f"400x150+{x}+{y}")

    def create_widgets(self):
        """Create the progress dialog widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text=get_string("checking_for_updates"),
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(0, 10))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(0, 20))
        self.progress_bar.start()

        # Cancel button
        self.cancel_button = ctk.CTkButton(
            main_frame,
            text=get_string("button_cancel"),
            command=self.cancel_check,
            width=100
        )
        self.cancel_button.pack()

    def start_check(self):
        """Start the update check in a background thread"""
        def check_thread():
            try:
                if not self.cancelled:
                    self.update_status(get_string("connecting_to_github"))
                    result = self.check_callback()

                if not self.cancelled:
                    self.after(0, lambda: self.on_check_complete(result))
            except Exception as e:
                logger.error(f"Update check failed: {e}")
                if not self.cancelled:
                    self.after(0, lambda: self.on_check_error(str(e)))

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def update_status(self, message: str):
        """Update the status message"""
        if not self.cancelled:
            self.after(0, lambda: self.status_label.configure(text=message))

    def cancel_check(self):
        """Cancel the update check"""
        self.cancelled = True
        self.destroy()

    def on_check_complete(self, result: UpdateCheckResult):
        """Handle completed update check"""
        self.destroy()

        if result.success and result.update_available and result.update_info:
            # Show update available dialog
            dialog = UpdateAvailableDialog(self.parent, result.update_info, result.current_version)
            dialog.show()
        elif result.success and not result.update_available:
            # Show no updates message
            self.show_info_dialog(
                get_string("dialog_title_no_updates"),
                get_string("no_updates_available")
            )
        else:
            # Show error message
            error_msg = result.error_message or get_string("error_unexpected_message")
            self.show_error_dialog(
                get_string("dialog_title_error"),
                error_msg
            )

    def on_check_error(self, error_message: str):
        """Handle update check error"""
        self.destroy()
        self.show_error_dialog(
            get_string("dialog_title_error"),
            error_message
        )

    def show_info_dialog(self, title: str, message: str):
        """Show information dialog"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 200
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 75
        dialog.geometry(f"400x150+{x}+{y}")

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        label = ctk.CTkLabel(frame, text=message, wraplength=350)
        label.pack(pady=(0, 20))

        button = ctk.CTkButton(frame, text=get_string("button_close"), command=dialog.destroy)
        button.pack()

    def show_error_dialog(self, title: str, message: str):
        """Show error dialog"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(title)
        dialog.geometry("450x200")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 225
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 100
        dialog.geometry(f"450x200+{x}+{y}")

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Error message
        label = ctk.CTkLabel(frame, text=message, wraplength=400)
        label.pack(pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x")

        close_button = ctk.CTkButton(button_frame, text=get_string("button_close"), command=dialog.destroy)
        close_button.pack(side="right")


class UpdateAvailableDialog(ctk.CTkToplevel):
    """Main dialog for displaying available updates"""

    def __init__(self, parent, update_info: UpdateInfo, current_version: str):
        super().__init__()
        self.parent = parent
        self.update_info = update_info
        self.current_version = current_version
        self.config_manager = ConfigManager()
        self.result = None

        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        """Configure the update dialog window"""
        self.title(get_string("dialog_title_update_available"))
        self.geometry("600x500")
        self.resizable(True, True)
        self.minsize(500, 400)
        self.transient(self.parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 300
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 250
        self.geometry(f"600x500+{x}+{y}")

    def create_widgets(self):
        """Create all dialog widgets"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        self.create_header_section(main_frame)

        # Version information section
        self.create_version_info_section(main_frame)

        # Security indicators
        self.create_security_section(main_frame)

        # Release notes section
        self.create_release_notes_section(main_frame)

        # Assets section (if any)
        if self.update_info.assets:
            self.create_assets_section(main_frame)

        # Action buttons
        self.create_action_buttons(main_frame)

    def create_header_section(self, parent):
        """Create the header with update available message"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        # Main header
        header_label = ctk.CTkLabel(
            header_frame,
            text=get_string("update_available_header"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack()

    def create_version_info_section(self, parent):
        """Create version comparison section"""
        version_frame = ctk.CTkFrame(parent)
        version_frame.pack(fill="x", pady=(0, 10))

        # Create grid layout for version info
        version_frame.grid_columnconfigure(1, weight=1)

        # Current version
        ctk.CTkLabel(
            version_frame,
            text=get_string("current_version_label"),
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(
            version_frame,
            text=self.current_version
        ).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        # New version
        ctk.CTkLabel(
            version_frame,
            text=get_string("new_version_label"),
            font=ctk.CTkFont(weight="bold")
        ).grid(row=1, column=0, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(
            version_frame,
            text=f"v{self.update_info.version}",
            text_color=("green", "lightgreen")
        ).grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Release date
        ctk.CTkLabel(
            version_frame,
            text=get_string("release_date_label"),
            font=ctk.CTkFont(weight="bold")
        ).grid(row=2, column=0, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(
            version_frame,
            text=self.update_info.release_date_str
        ).grid(row=2, column=1, sticky="w", padx=10, pady=5)

    def create_security_section(self, parent):
        """Create security indicators section"""
        security_frame = ctk.CTkFrame(parent)
        security_frame.pack(fill="x", pady=(0, 10))

        # SSL indicator
        ssl_label = ctk.CTkLabel(
            security_frame,
            text=get_string("ssl_verified"),
            text_color=("green", "lightgreen"),
            font=ctk.CTkFont(size=11)
        )
        ssl_label.pack(side="left", padx=10, pady=5)

        # GitHub official indicator
        github_label = ctk.CTkLabel(
            security_frame,
            text=get_string("github_official"),
            text_color=("blue", "lightblue"),
            font=ctk.CTkFont(size=11)
        )
        github_label.pack(side="left", padx=10, pady=5)

        # URL display
        url_frame = ctk.CTkFrame(security_frame, fg_color="transparent")
        url_frame.pack(side="right", padx=10, pady=5)

        ctk.CTkLabel(
            url_frame,
            text=get_string("download_url_label"),
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack()

        ctk.CTkLabel(
            url_frame,
            text=self.update_info.html_url,
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40")
        ).pack()

    def create_release_notes_section(self, parent):
        """Create scrollable release notes section"""
        notes_frame = ctk.CTkFrame(parent)
        notes_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Section header
        notes_header = ctk.CTkLabel(
            notes_frame,
            text=get_string("release_notes_label"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        notes_header.pack(anchor="w", padx=10, pady=(10, 5))

        # Scrollable text area for release notes
        if self.update_info.body.strip():
            notes_text = ctk.CTkTextbox(
                notes_frame,
                wrap="word",
                height=150,
                font=ctk.CTkFont(size=11)
            )
            notes_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Insert release notes
            notes_text.insert("1.0", self.update_info.body)
            notes_text.configure(state="disabled")
        else:
            no_notes_label = ctk.CTkLabel(
                notes_frame,
                text="Inga versionsinformation tillgängliga.",
                text_color=("gray60", "gray40")
            )
            no_notes_label.pack(padx=10, pady=10)

    def create_assets_section(self, parent):
        """Create assets information section"""
        if not self.update_info.assets:
            return

        assets_frame = ctk.CTkFrame(parent)
        assets_frame.pack(fill="x", pady=(0, 10))

        # Section header
        assets_header = ctk.CTkLabel(
            assets_frame,
            text=get_string("available_files_label"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        assets_header.pack(anchor="w", padx=10, pady=(10, 5))

        # List assets
        for asset in self.update_info.assets[:5]:  # Limit to 5 assets for space
            asset_text = get_string("file_size_format", name=asset.name, size=asset.size_mb)
            asset_label = ctk.CTkLabel(
                assets_frame,
                text=f"• {asset_text}",
                font=ctk.CTkFont(size=10),
                anchor="w"
            )
            asset_label.pack(anchor="w", padx=20, pady=1)

    def create_action_buttons(self, parent):
        """Create action buttons section"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        # Download button
        download_button = ctk.CTkButton(
            button_frame,
            text=get_string("button_download"),
            command=self.on_download,
            fg_color=("green", "darkgreen"),
            hover_color=("darkgreen", "green"),
            width=120
        )
        download_button.pack(side="left", padx=(0, 10))

        # Skip version button
        skip_button = ctk.CTkButton(
            button_frame,
            text=get_string("button_skip_version"),
            command=self.on_skip_version,
            fg_color=("orange", "darkorange"),
            hover_color=("darkorange", "orange"),
            width=150
        )
        skip_button.pack(side="left", padx=(0, 10))

        # Close button
        close_button = ctk.CTkButton(
            button_frame,
            text=get_string("button_close"),
            command=self.on_close,
            width=100
        )
        close_button.pack(side="right")

    def on_download(self):
        """Handle download button click"""
        try:
            # Open GitHub release page in browser
            webbrowser.open(self.update_info.html_url)
            self.result = "download"
            logger.info(f"Opened download page for version {self.update_info.version}")
            self.destroy()
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            # Show error dialog
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title(get_string("error_browser"))
            error_dialog.geometry("500x200")
            error_dialog.transient(self)

            frame = ctk.CTkFrame(error_dialog)
            frame.pack(fill="both", expand=True, padx=20, pady=20)

            msg_label = ctk.CTkLabel(frame, text=get_string("error_browser_message"))
            msg_label.pack(pady=(0, 10))

            url_entry = ctk.CTkEntry(frame, width=400)
            url_entry.pack(pady=(0, 20))
            url_entry.insert(0, self.update_info.html_url)
            url_entry.configure(state="readonly")

            ctk.CTkButton(frame, text=get_string("button_close"), command=error_dialog.destroy).pack()

    def on_skip_version(self):
        """Handle skip version button click"""
        try:
            # Add version to skip list
            self.config_manager.add_skipped_version(self.update_info.version)
            self.config_manager.add_skipped_version(self.update_info.tag_name)

            self.result = "skip"
            logger.info(f"Skipped version {self.update_info.version}")
            self.destroy()
        except Exception as e:
            logger.error(f"Failed to skip version: {e}")

    def on_close(self):
        """Handle close button click"""
        self.result = "close"
        self.destroy()

    def show(self) -> str:
        """Show the dialog and return the result"""
        self.wait_window()
        return self.result or "close"
