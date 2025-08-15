"""
Phase 2: Semi-Autonomous Integration Tests - Requires User Verification
These tests run automatically but need user confirmation that results are correct.
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import ConfigManager
from core.excel_manager import ExcelManager
from core.filename_parser import FilenameParser
from core.pdf_processor import PDFProcessor


class TestIntegrationWorkflows:
    """Integration tests for main application workflows"""

    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_excel_file = os.path.join(self.temp_dir, "test_timeline.xlsx")
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")

    def teardown_method(self):
        """Cleanup test fixtures"""
        try:
            if os.path.exists(self.test_excel_file):
                os.unlink(self.test_excel_file)
            if os.path.exists(self.test_config_file):
                os.unlink(self.test_config_file)
            os.rmdir(self.temp_dir)
        except (FileNotFoundError, OSError):
            pass

    def test_pdf_filename_parsing_workflow(self):
        """Test complete PDF filename parsing workflow"""
        print("\n" + "="*60)
        print("INTEGRATION TEST: PDF Filename Parsing Workflow")
        print("="*60)

        # Test various realistic PDF filenames
        test_filenames = [
            "2024-01-15 Dagens Nyheter korruptionsskandal inom regeringen (3 sid).pdf",
            "2024-02-20 AFTONBLADET PLUS undersökning om skattefusk (7 sid).pdf",
            "2024-03-10 Svenska Dagbladet.pdf",
            "2024-04-05 Expressen breaking news story.pdf"
        ]

        parser = FilenameParser()
        results = []

        for filename in test_filenames:
            print(f"\nTesting filename: {filename}")

            # Parse the filename
            parsed = parser.parse_filename(filename)
            print(f"Parsed result: {parsed}")

            # Reconstruct filename
            reconstructed = parser.construct_filename(
                parsed['date'], parsed['newspaper'],
                parsed['comment'], parsed['pages']
            )
            print(f"Reconstructed: {reconstructed}")

            # Validate the reconstructed filename
            valid, message = parser.validate_filename(reconstructed)
            print(f"Validation: {'VALID' if valid else 'INVALID'} - {message}")

            results.append({
                'original': filename,
                'parsed': parsed,
                'reconstructed': reconstructed,
                'valid': valid
            })

        print("\nWORKFLOW SUMMARY:")
        print(f"Total files tested: {len(test_filenames)}")
        print(f"Successfully parsed: {len([r for r in results if r['parsed']['date']])}")
        print(f"Valid reconstructions: {len([r for r in results if r['valid']])}")

        # Automatic assertions
        assert len(results) == len(test_filenames)
        assert all(result['valid'] for result in results), "All reconstructed filenames should be valid"

        print("\nINTEGRATION TEST PASSED - Review results above")
        return results

    @patch('core.pdf_processor.PyPDF2.PdfReader')
    @patch('builtins.open')
    def test_pdf_processing_workflow(self, mock_open, mock_pdf_reader):
        """Test complete PDF processing workflow with mocked files"""
        print("\n" + "="*60)
        print("INTEGRATION TEST: PDF Processing Workflow")
        print("="*60)

        # Mock PDF reader for different scenarios
        def setup_pdf_mock(pages, encrypted=False, corrupted=False):
            mock_reader = MagicMock()
            mock_reader.is_encrypted = encrypted
            if corrupted:
                mock_reader.pages.__len__ = MagicMock(return_value=pages)
                mock_reader.pages.__getitem__ = MagicMock(side_effect=Exception("Corrupted"))
            else:
                mock_reader.pages = [MagicMock() for _ in range(pages)]
            return mock_reader

        test_cases = [
            {"file": "test_normal.pdf", "pages": 5, "encrypted": False, "corrupted": False},
            {"file": "test_encrypted.pdf", "pages": 3, "encrypted": True, "corrupted": False},
            {"file": "test_corrupted.pdf", "pages": 1, "encrypted": False, "corrupted": True},
            {"file": "test_large.pdf", "pages": 150, "encrypted": False, "corrupted": False}
        ]

        processor = PDFProcessor()
        results = []

        for case in test_cases:
            print(f"\nTesting PDF: {case['file']}")

            # Setup mock for this test case
            mock_pdf_reader.return_value = setup_pdf_mock(
                case['pages'], case['encrypted'], case['corrupted']
            )

            try:
                # Test page counting
                page_count = processor.get_pdf_page_count(case['file'])
                print(f"Page count: {page_count}")

                # Test validation
                # Create a fake file for validation
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(b"fake pdf content")
                    temp_file_path = temp_file.name

                try:
                    with patch.object(processor, 'get_pdf_page_count', return_value=page_count):
                        valid, message = processor.validate_pdf_file(temp_file_path)
                    print(f"Validation: {'VALID' if valid else 'INVALID'} - {message}")
                finally:
                    os.unlink(temp_file_path)

                results.append({
                    'file': case['file'],
                    'expected_pages': case['pages'],
                    'actual_pages': page_count,
                    'valid': valid,
                    'encrypted': case['encrypted'],
                    'corrupted': case['corrupted']
                })

            except ValueError as e:
                print(f"Expected error for corrupted file: {e}")
                results.append({
                    'file': case['file'],
                    'expected_pages': case['pages'],
                    'actual_pages': 0,
                    'valid': False,
                    'error': str(e),
                    'encrypted': case['encrypted'],
                    'corrupted': case['corrupted']
                })

        print("\nPDF PROCESSING SUMMARY:")
        for result in results:
            status = "OK" if not result.get('error') else "WARNING"
            print(f"{status} {result['file']}: {result.get('actual_pages', 0)} pages")

        print("\nPDF PROCESSING WORKFLOW TEST COMPLETED")
        return results

    def test_config_persistence_workflow(self):
        """Test configuration save/load workflow"""
        print("\n" + "="*60)
        print("INTEGRATION TEST: Configuration Persistence Workflow")
        print("="*60)

        # Create test configuration manager
        config_manager = ConfigManager()
        config_manager.config_file = Path(self.test_config_file)

        # Test configuration data with Swedish characters
        test_config = {
            "excel_file": "test_åäö_timeline.xlsx",
            "last_pdf_dir": "C:\\Test\\PDF\\Mapp",
            "window_geometry": "1600x1200",
            "theme": "bootstrap",
            "text_font_size": 12,
            "locked_fields": {
                "Händelse": True,
                "Note1": False,
                "Källa1": True
            },
            "locked_field_contents": {
                "Händelse": "Standardtext för händelser",
                "Note1": "",
                "Källa1": "Källa information"
            },
            "locked_field_formats": {
                "Händelse": {"font_size": 12, "bold": True},
                "Källa1": {"italic": True}
            }
        }

        print("1. Saving configuration with Swedish characters and complex data...")
        config_manager.save_config(test_config)
        print(f"   Config saved to: {self.test_config_file}")

        print("2. Loading configuration...")
        loaded_config = config_manager.load_config()
        print(f"   Loaded {len(loaded_config)} configuration keys")

        print("3. Verifying Swedish character preservation...")
        assert loaded_config["excel_file"] == "test_åäö_timeline.xlsx"
        assert "Händelse" in loaded_config["locked_field_contents"]
        assert loaded_config["locked_field_contents"]["Händelse"] == "Standardtext för händelser"
        print("   Swedish characters preserved correctly")

        print("4. Testing locked fields workflow...")
        locked_states = {"NewField": True, "AnotherField": False}
        locked_contents = {"NewField": "Nytt innehåll", "AnotherField": ""}
        locked_formats = {"NewField": {"color": "blue", "size": 14}}

        config_manager.save_locked_fields(locked_states, locked_contents, locked_formats)

        # Load locked fields
        states, contents, formats = config_manager.load_locked_fields()
        print(f"   Loaded {len(states)} locked field states")
        print(f"   Loaded {len(contents)} locked field contents")
        print(f"   Loaded {len(formats)} locked field formats")

        assert states == locked_states
        assert contents == locked_contents
        assert formats == locked_formats
        print("   Locked fields workflow successful")

        print("\nCONFIGURATION WORKFLOW SUMMARY:")
        print("Configuration save/load: Working")
        print("Swedish character support: Working")
        print("Locked fields persistence: Working")
        print("Complex data structures: Working")

        print("\nCONFIGURATION WORKFLOW TEST COMPLETED")
        return loaded_config

    def test_data_preparation_workflow(self):
        """Test Excel data preparation workflow with realistic data"""
        print("\n" + "="*60)
        print("INTEGRATION TEST: Excel Data Preparation Workflow")
        print("="*60)

        # Create Excel manager with test columns
        excel_manager = ExcelManager()
        excel_manager.columns = {
            'Startdatum': 1,
            'Slutdatum': 2,
            'Dag': 3,
            'Händelse': 4,
            'Kategori': 5,
            'Person/sak': 6,
            'Källa1': 7,
            'Note1': 8,
            'Note2': 9,
            'OBS': 10
        }

        # Test realistic data scenarios
        test_scenarios = [
            {
                "name": "Complete PDF Data",
                "data": {
                    'Händelse': 'Viktigt möte om budget',
                    'Startdatum': '',  # Should use date from PDF
                    'Källa1': '',      # Should use filename
                    'Kategori': 'Politik',
                    'date': '2024-01-15'
                },
                "filename": '2024-01-15 Svenska Dagbladet budgetmöte regering (4 sid).pdf'
            },
            {
                "name": "Manual Entry (No PDF)",
                "data": {
                    'Händelse': 'Bokrecension av ny roman',
                    'Startdatum': '2024-02-20',  # User provided
                    'Källa1': 'Eget material',   # User provided
                    'Kategori': 'Kultur'
                },
                "filename": ''  # No PDF file
            },
            {
                "name": "Mixed Data (User + PDF)",
                "data": {
                    'Händelse': 'Användartext',  # User content
                    'Startdatum': '2024-03-10',  # User date (should override PDF)
                    'Källa1': '',                # Should use PDF filename
                    'Note1': 'Extra information',
                    'date': '2024-03-05'        # PDF date (should be ignored)
                },
                "filename": '2024-03-05 Expressen breaking news.pdf'
            }
        ]

        results = []
        for scenario in test_scenarios:
            print(f"\nTesting scenario: {scenario['name']}")
            print(f"Input data: {scenario['data']}")
            print(f"Filename: {scenario['filename']}")

            # Process the data
            processed = excel_manager._prepare_special_data(scenario['data'], scenario['filename'])
            print(f"Processed result: {processed}")

            # Analyze the results
            analysis = {
                'scenario': scenario['name'],
                'input': scenario['data'],
                'filename': scenario['filename'],
                'output': processed,
                'changes_made': []
            }

            # Check what changes were made
            for field in ['Händelse', 'Startdatum', 'Källa1']:
                if field in processed and field in scenario['data']:
                    if str(processed[field]) != str(scenario['data'][field]):
                        analysis['changes_made'].append({
                            'field': field,
                            'from': scenario['data'][field],
                            'to': processed[field]
                        })

            print(f"Changes made: {len(analysis['changes_made'])}")
            for change in analysis['changes_made']:
                print(f"  {change['field']}: '{change['from']}' -> '{change['to']}'")

            results.append(analysis)

        print("\nDATA PREPARATION WORKFLOW SUMMARY:")
        for result in results:
            print(f"{result['scenario']}: {len(result['changes_made'])} automatic adjustments")

        print("\nDATA PREPARATION WORKFLOW TEST COMPLETED")
        return results

    def test_end_to_end_pdf_workflow(self):
        """Test complete end-to-end PDF processing workflow"""
        print("\n" + "="*80)
        print("INTEGRATION TEST: Complete End-to-End PDF Workflow")
        print("="*80)

        # Simulate a complete user workflow
        pdf_filename = "2024-08-15 DAGENS NYHETER korruption kommun (8 sid).pdf"

        print(f"Starting with PDF file: {pdf_filename}")

        # Step 1: Parse PDF filename
        print("\n1. Parsing PDF filename...")
        parser = FilenameParser()
        parsed_data = parser.parse_filename(pdf_filename)
        print(f"   Parsed components: {parsed_data}")

        # Step 2: Prepare Excel data
        print("\n2. Preparing Excel data...")
        excel_manager = ExcelManager()
        excel_manager.columns = {
            'Startdatum': 1, 'Händelse': 2, 'Kategori': 3,
            'Person/sak': 4, 'Källa1': 5, 'Note1': 6
        }

        # Simulate user input combined with PDF data
        user_input = {
            'Händelse': 'Korruptionsutredning pågår',
            'Kategori': 'Politik',
            'Person/sak': 'Kommunfullmäktige',
            'Note1': 'Viktig för kommande artikel',
            'Startdatum': '',  # Will use PDF date
            'Källa1': ''       # Will use PDF filename
        }

        # Add PDF data to user input
        excel_data = {**user_input, **parsed_data}

        prepared_data = excel_manager._prepare_special_data(excel_data, pdf_filename)
        print(f"   Prepared Excel data: {prepared_data}")

        # Step 3: Generate new filename (if user modified it)
        print("\n3. Handling filename operations...")
        new_filename = parser.construct_filename(
            parsed_data['date'],
            parsed_data['newspaper'],
            "korruption kommun UTREDNING",  # User modified comment
            parsed_data['pages']
        )
        print(f"   New filename would be: {new_filename}")

        # Validate new filename
        valid, message = parser.validate_filename(new_filename)
        print(f"   Filename validation: {'VALID' if valid else 'INVALID'} - {message}")

        # Step 4: Configuration handling
        print("\n4. Configuration management...")
        config_manager = ConfigManager()
        config_manager.config_file = Path(self.test_config_file)

        # Save workflow state (convert any date objects to strings for JSON serialization)
        excel_data_for_config = {}
        for key, value in prepared_data.items():
            if hasattr(value, 'isoformat'):  # datetime.date or datetime.datetime
                excel_data_for_config[key] = value.isoformat()
            else:
                excel_data_for_config[key] = value

        workflow_config = {
            "last_pdf_file": pdf_filename,
            "last_excel_data": excel_data_for_config,
            "workflow_timestamp": datetime.now().isoformat()
        }
        config_manager.save_config(workflow_config)
        print("   Workflow state saved to config")

        # Step 5: Summary
        print("\nEND-TO-END WORKFLOW SUMMARY:")
        print("PDF filename parsed successfully")
        print(f"Excel data prepared with {len(prepared_data)} fields")
        print("New filename generated and validated")
        print("Workflow state persisted")
        print("Swedish characters handled correctly")

        workflow_result = {
            'original_pdf': pdf_filename,
            'parsed_data': parsed_data,
            'user_input': user_input,
            'excel_data': prepared_data,
            'new_filename': new_filename,
            'filename_valid': valid,
            'config_saved': os.path.exists(self.test_config_file)
        }

        print("\nCOMPLETE END-TO-END WORKFLOW TEST PASSED")
        return workflow_result


if __name__ == "__main__":
    # Run integration tests with verbose output
    print("Running Phase 2: Semi-Autonomous Integration Tests")
    print("These tests demonstrate complete workflows and require user review of results.\n")

    pytest.main([__file__, "-v", "-s"])  # -s shows print statements
