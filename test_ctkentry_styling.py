"""
Test script to verify CTkEntry styling parameters for disabled state.
This script helps understand how CustomTkinter handles disabled CTkEntry styling.
"""


import customtkinter as ctk


def test_ctkentry_styling():
    """Test different styling approaches for CTkEntry widgets."""

    # Create test window
    root = ctk.CTk()
    root.title("CTkEntry Styling Test")
    root.geometry("600x400")

    # Test different styling approaches
    frame = ctk.CTkFrame(root)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Test 1: Normal CTkEntry
    label1 = ctk.CTkLabel(frame, text="Normal CTkEntry:")
    label1.pack(pady=(10, 5))

    entry1 = ctk.CTkEntry(frame, placeholder_text="Normal entry")
    entry1.pack(pady=5)

    # Test 2: CTkEntry with state='disabled'
    label2 = ctk.CTkLabel(frame, text="CTkEntry with state='disabled':")
    label2.pack(pady=(20, 5))

    entry2 = ctk.CTkEntry(frame, placeholder_text="Disabled entry", state="disabled")
    entry2.pack(pady=5)

    # Test 3: CTkEntry configured after creation
    label3 = ctk.CTkLabel(frame, text="CTkEntry configured after creation:")
    label3.pack(pady=(20, 5))

    entry3 = ctk.CTkEntry(frame, placeholder_text="Will be configured")
    entry3.pack(pady=5)
    entry3.configure(state="disabled")

    # Test 4: CTkEntry with manual styling
    label4 = ctk.CTkLabel(frame, text="CTkEntry with manual styling:")
    label4.pack(pady=(20, 5))

    entry4 = ctk.CTkEntry(
        frame,
        placeholder_text="Manual styling",
        state="disabled",
        fg_color="#E8E8E8",
        text_color="#666666",
        border_color="#CCCCCC"
    )
    entry4.pack(pady=5)

    # Test 5: CTkEntry with styling applied via configure
    label5 = ctk.CTkLabel(frame, text="CTkEntry with styling via configure:")
    label5.pack(pady=(20, 5))

    entry5 = ctk.CTkEntry(frame, placeholder_text="Will be styled")
    entry5.pack(pady=5)
    entry5.configure(
        state="disabled",
        fg_color="#E8E8E8",
        text_color="#666666",
        border_color="#CCCCCC"
    )

    # Information label
    info_label = ctk.CTkLabel(
        frame,
        text="Compare the visual appearance of different styling approaches",
        font=ctk.CTkFont(size=12, slant="italic")
    )
    info_label.pack(pady=20)

    # Function to toggle between enabled/disabled for testing
    def toggle_states():
        for entry in [entry1, entry2, entry3, entry4, entry5]:
            current_state = entry.cget("state")
            new_state = "normal" if current_state == "disabled" else "disabled"
            entry.configure(state=new_state)

    toggle_btn = ctk.CTkButton(frame, text="Toggle All States", command=toggle_states)
    toggle_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    test_ctkentry_styling()
