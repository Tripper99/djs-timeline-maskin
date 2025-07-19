"""
Excel file management for the DJ Timeline application
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import openpyxl
from openpyxl.styles import Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelManager:
    """Handles Excel file operations"""
    
    def __init__(self, excel_path: str = None):
        self.excel_path = excel_path
        self.workbook = None
        self.worksheet = None
        self.columns = {}
        self.column_names = []
    
    def load_excel_file(self, excel_path: str) -> bool:
        """Load Excel file and map columns"""
        try:
            self.excel_path = excel_path
            self.workbook = openpyxl.load_workbook(excel_path)
            self.worksheet = self.workbook.active
            
            # Map column headers to column indices
            self.columns = {}
            self.column_names = []
            for col_idx, cell in enumerate(self.worksheet[1], 1):
                if cell.value:
                    col_name = str(cell.value).strip()
                    self.columns[col_name] = col_idx
                    self.column_names.append(col_name)
            
            logger.info(f"Loaded Excel file with columns: {self.column_names}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return False
    
    def get_column_names(self) -> List[str]:
        """Get list of column names from Excel file"""
        return self.column_names.copy() if self.column_names else []
    
    def add_row(self, data: Dict[str, str], filename: str, row_color: str = "none") -> bool:
        """Add new row to Excel file with special column handling and optional background color"""
        try:
            if not self.worksheet:
                return False
            
            # Double-check that the Excel file still exists before writing
            if not self.excel_path or not Path(self.excel_path).exists():
                logger.error(f"Excel file not found: {self.excel_path}")
                return False
            
            # Find next empty row
            next_row = self.worksheet.max_row + 1
            
            # Handle special columns
            special_data = data.copy()
            
            # Händelse - preserve user content and add filename if filename exists and not already there
            if 'Händelse' in self.columns:
                current_content = data.get('Händelse', '')
                # Handle both string and CellRichText objects
                if hasattr(current_content, '__class__') and current_content.__class__.__name__ == 'CellRichText':
                    # For CellRichText, we consider it as having content if it has any parts
                    has_content = len(current_content) > 0
                    if has_content and filename:
                        # For CellRichText, we can't easily check if filename is already included
                        # so we'll just keep the current content as-is
                        special_data['Händelse'] = current_content
                    elif not has_content:
                        # Empty CellRichText, add filename if it exists
                        special_data['Händelse'] = filename if filename else ""
                    else:
                        # Has content but no filename, keep as-is
                        special_data['Händelse'] = current_content
                else:
                    # Handle string content
                    current_content = str(current_content).strip()
                    if current_content:
                        # User has added content, check if filename exists and is already included
                        if filename and filename not in current_content:
                            # Add filename at the end if filename exists and not already present
                            special_data['Händelse'] = f"{current_content}\n{filename}"
                        else:
                            # Keep user content as is
                            special_data['Händelse'] = current_content
                    else:
                        # No user content, only add filename if it exists
                        if filename:
                            special_data['Händelse'] = f"\n\n{filename}"
                        else:
                            special_data['Händelse'] = ""
            
            # Tid start - only use date from filename if user hasn't filled it in
            if 'Tid start' in self.columns and 'date' in data:
                user_tid_start = str(special_data.get('Tid start', '')).strip()
                if not user_tid_start:  # Only set if user hasn't provided their own value
                    try:
                        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
                        special_data['Tid start'] = date_obj.date()
                    except ValueError:
                        special_data['Tid start'] = data.get('date', '')
            
            # Källa1 - full filename (only if filename exists)
            if 'Källa1' in self.columns:
                special_data['Källa1'] = filename if filename else ""
            
            # Write data to row
            for col_name, col_idx in self.columns.items():
                value = special_data.get(col_name, '')
                cell = self.worksheet.cell(row=next_row, column=col_idx)
                cell.value = value
                
                # Check if this is a CellRichText object - if so, skip most formatting to preserve RichText
                is_rich_text = hasattr(value, '__class__') and value.__class__.__name__ == 'CellRichText'
                if is_rich_text:
                    logger.info(f"Detected CellRichText for column {col_name}")
                
                # Define border style for all cells (thin black borders on all sides)
                thin_border = Border(
                    left=Side(style='thin', color='000000'),
                    right=Side(style='thin', color='000000'),
                    top=Side(style='thin', color='000000'),
                    bottom=Side(style='thin', color='000000')
                )
                
                # Apply borders to all cells
                cell.border = thin_border
                
                # Apply background color if specified (but not for RichText cells as it might interfere)
                if row_color and row_color != "none" and not is_rich_text:
                    color_map = {
                        "yellow": "FFFF99",
                        "green": "CCFFCC", 
                        "blue": "CCE5FF",
                        "pink": "FFCCEE",
                        "gray": "E6E6E6"
                    }
                    if row_color in color_map:
                        fill = PatternFill(start_color=color_map[row_color], 
                                         end_color=color_map[row_color], 
                                         fill_type="solid")
                        cell.fill = fill
                
                # Column-specific formatting (skip for RichText to preserve formatting)
                if not is_rich_text:
                    if col_name == 'OBS':
                        # Text format for OBS field - basic text field
                        cell.number_format = '@'  # @ means Text format in Excel
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name == 'Inlagd datum':
                        # Date format YYYY-MM-DD for Inlagd datum field - same as other date fields
                        cell.number_format = 'YYYY-MM-DD'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name in ['Kategori', 'Underkategori', 'Person/sak', 'Egen grupp']:
                        # Text format for basic text fields with text wrapping
                        cell.number_format = '@'  # @ means Text format in Excel
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name == 'Händelse':
                        # Text format with text wrapping - wider cells expected
                        cell.number_format = '@'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name == 'Dag':
                        # Text format for the formula result (mån, tis, ons, etc.) - narrow column
                        # Add formula that references Tid start column
                        tid_start_col_idx = self.columns.get('Tid start')
                        if tid_start_col_idx:
                            tid_start_col_letter = get_column_letter(tid_start_col_idx)
                            cell.value = f"=TEXT({tid_start_col_letter}{next_row},\"ddd\")"
                        cell.number_format = '@'  # Text format for day names
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name in ['Tid start', 'Tid slut']:
                        # Date format YYYY-MM-DD for date fields - medium width columns
                        if col_name == 'Tid start' and hasattr(value, 'year'):
                            # Value is already a date object, format it properly
                            cell.number_format = 'YYYY-MM-DD'
                        else:
                            # For text date values or Tid slut field
                            cell.number_format = 'YYYY-MM-DD'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name.startswith('Note'):
                        # Text format with text wrapping for Note fields - expect wider columns
                        cell.number_format = '@'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name.startswith('Källa'):
                        # Text format with text wrapping for source fields - medium width
                        cell.number_format = '@'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    elif col_name == 'Övrigt':
                        # Text format with text wrapping for historical field - wider column expected
                        cell.number_format = '@'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                    else:
                        # Default: Text format for any other fields - basic formatting
                        cell.number_format = '@'
                        cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
                else:
                    # For RichText cells, only apply minimal formatting that won't interfere
                    cell.number_format = '@'  # Keep text format
                    cell.alignment = Alignment(wrap_text=True, vertical='bottom', horizontal='left')
            
            # Save workbook
            self.workbook.save(self.excel_path)
            logger.info(f"Added row to Excel file at row {next_row}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding row to Excel: {e}")
            return False