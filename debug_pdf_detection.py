#!/usr/bin/env python3
"""
Diagnostic script: test all three methods for detecting open PDF files.
Run this while a PDF is open in PDF Studio 2024.

Usage: python debug_pdf_detection.py /path/to/open/file.pdf
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Användning: python debug_pdf_detection.py /sökväg/till/fil.pdf")
        print("Kör detta medan filen är öppen i PDF Studio 2024.")
        sys.exit(1)

    file_path = sys.argv[1]
    filename = Path(file_path).name
    stem = Path(file_path).stem
    own_pid = os.getpid()

    print(f"Fil: {file_path}")
    print(f"Filnamn: {filename}")
    print(f"Stem: {stem}")
    print(f"Egen PID: {own_pid}")
    print("=" * 60)

    # --- Method 1: CGWindowList ---
    print("\n[Metod 1] CGWindowListCopyWindowInfo")
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGNullWindowID,
            kCGWindowListOptionAll,
        )
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
        print(f"  Antal fönster: {len(windows)}")
        matches = []
        all_with_names = []
        for w in windows:
            win_name = w.get('kCGWindowName', '') or ''
            owner = w.get('kCGWindowOwnerName', '') or ''
            owner_pid = w.get('kCGWindowOwnerPID', 0)
            if win_name:
                all_with_names.append(f"    [{owner} (PID {owner_pid})] {win_name}")
            if filename in win_name or stem in win_name:
                matches.append(f"    MATCH: [{owner} (PID {owner_pid})] {win_name}")

        print(f"  Fönster med namn (icke-tomma): {len(all_with_names)}")
        if len(all_with_names) <= 30:
            for line in all_with_names:
                print(line)
        else:
            print("  (för många att visa, visar första 30)")
            for line in all_with_names[:30]:
                print(line)

        if matches:
            print(f"\n  MATCHNINGAR mot '{filename}' / '{stem}':")
            for m in matches:
                print(m)
        else:
            print(f"\n  Inga matchningar mot '{filename}' eller '{stem}'")
    except Exception as e:
        print(f"  FEL: {e}")

    # --- Method 2: lsof ---
    print("\n[Metod 2] lsof")
    try:
        result = subprocess.run(
            ['lsof', '--', file_path],
            capture_output=True, text=True, timeout=5,
        )
        print(f"  Returkod: {result.returncode}")
        if result.stdout.strip():
            print(f"  Output:\n{result.stdout}")
        else:
            print("  Ingen output (filen har ingen öppen filhanterare)")
    except Exception as e:
        print(f"  FEL: {e}")

    # --- Method 3: AppleScript System Events ---
    print("\n[Metod 3] AppleScript System Events")
    # First: simple permission test
    print("  Steg A: Behörighetstest...")
    try:
        result = subprocess.run(
            ['osascript', '-e',
             'tell application "System Events" to get name of first '
             'process whose background only is false'],
            capture_output=True, text=True, timeout=5,
        )
        print(f"  Returkod: {result.returncode}")
        if result.returncode == 0:
            print(f"  OK — behörighet finns. Resultat: {result.stdout.strip()}")
        else:
            print(f"  MISSLYCKADES — stderr: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT — behörighetsdialog kan ha visats")
    except Exception as e:
        print(f"  FEL: {e}")

    # Second: list all window titles
    print("\n  Steg B: Lista alla fönsternamn...")
    try:
        applescript = '''
            set output to ""
            tell application "System Events"
                set appProcesses to every process whose background only is false
                repeat with proc in appProcesses
                    set procName to name of proc
                    try
                        set winList to name of every window of proc
                        repeat with winTitle in winList
                            set output to output & procName & " :: " & winTitle & linefeed
                        end repeat
                    end try
                end repeat
            end tell
            return output
        '''
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True, text=True, timeout=10,
        )
        print(f"  Returkod: {result.returncode}")
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            print(f"  Alla fönster ({len(lines)} st):")
            for line in lines:
                marker = " <-- MATCH" if (filename in line or stem in line) else ""
                print(f"    {line}{marker}")
        elif result.returncode == 0:
            print("  Inga fönster hittades")
        else:
            print(f"  MISSLYCKADES — stderr: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
    except Exception as e:
        print(f"  FEL: {e}")

    # --- Method 4: Process search ---
    print("\n[Metod 4] Processökning (ps aux)")
    try:
        result = subprocess.run(
            ['ps', 'aux'], capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.strip().splitlines()
        print(f"  Totalt {len(lines)} processer")

        # Look for anything PDF Studio / Java related
        keywords = ['pdf studio', 'pdfstudio', 'qoppa', 'java']
        print(f"\n  Processer som matchar {keywords}:")
        found_any = False
        for line in lines:
            lower = line.lower()
            if any(kw in lower for kw in keywords):
                found_any = True
                print(f"    {line[:200]}")

        if not found_any:
            print("    Inga matchande processer hittade")

        # Also check for the filename/stem in any process args
        print(f"\n  Processer som innehåller filnamnet/stem:")
        found_file = False
        for line in lines:
            if filename in line or stem in line:
                found_file = True
                print(f"    {line[:200]}")
        if not found_file:
            print("    Inga processer refererar till filnamnet")

    except Exception as e:
        print(f"  FEL: {e}")

    # --- Method 5: AppleScript — list ALL processes and window counts ---
    print("\n[Metod 5] AppleScript — processer och antal fönster")
    try:
        applescript = '''
            set output to ""
            tell application "System Events"
                set appProcesses to every process whose background only is false
                repeat with proc in appProcesses
                    set procName to name of proc
                    try
                        set winCount to count of windows of proc
                        set output to output & procName & " (" & winCount & " fönster)" & linefeed
                    on error
                        set output to output & procName & " (kan ej läsa fönster)" & linefeed
                    end try
                end repeat
            end tell
            return output
        '''
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            print(f"  Foreground-processer ({len(lines)} st):")
            for line in lines:
                print(f"    {line}")
        elif result.returncode == 0:
            print("  Inga processer hittades")
        else:
            print(f"  MISSLYCKADES — stderr: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
    except Exception as e:
        print(f"  FEL: {e}")

    # --- Method 6: AppleScript — get window TITLES (not names) ---
    print("\n[Metod 6] AppleScript — fönster-titlar (title vs name)")
    try:
        applescript = '''
            set output to ""
            tell application "System Events"
                set appProcesses to every process whose background only is false
                repeat with proc in appProcesses
                    set procName to name of proc
                    try
                        set winList to every window of proc
                        repeat with w in winList
                            try
                                set winTitle to title of w
                                set output to output & procName & " :: title=" & winTitle & linefeed
                            end try
                            try
                                set winName to name of w
                                set output to output & procName & " :: name=" & winName & linefeed
                            end try
                            try
                                set winDesc to description of w
                                set output to output & procName & " :: desc=" & winDesc & linefeed
                            end try
                        end repeat
                    end try
                end repeat
            end tell
            return output
        '''
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            print(f"  Fönsterdetaljer ({len(lines)} rader):")
            for line in lines:
                marker = " <-- MATCH" if (filename in line or stem in line) else ""
                print(f"    {line}{marker}")
        elif result.returncode == 0:
            print("  Inga fönsterdetaljer hittades")
        else:
            print(f"  MISSLYCKADES — stderr: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
    except Exception as e:
        print(f"  FEL: {e}")

    print("\n" + "=" * 60)
    print("Diagnostik klar.")


if __name__ == "__main__":
    main()
