#
# cell_attributes_from_8K_test.py
# Test the cell attributes extraction from a 8K report
#

import sys
import unittest
from extract_tables import process_ws
from openpyxl import load_workbook
import os

sys.path.append('../')


class TestCellAttributesExtraction8K(unittest.TestCase):
    """Test the cell attributes extraction process"""

    def setUp(self):
        # Load a test 8-K report and extract data
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        workbook = load_workbook(ROOT_DIR + '/test-data/8-K.xlsx')
        worksheets = workbook.worksheets
        worksheet = workbook[worksheets[0].title]
        self.table_8K = process_ws(worksheet)

    def test_header_cells(self):
        """
        Test the first cell of the header row
        :return:
        """
        first_cell = self.table_8K['Cells'][0][0]
        # The first cell of the first row should have the following attributes
        self.assertEqual(first_cell['FB'], 1)
        self.assertEqual(first_cell['I'], 0)
        self.assertEqual(first_cell['font_name'], None)
        self.assertEqual(first_cell['font_size'], None)
        self.assertEqual(first_cell['FC'], 0)
        self.assertEqual(first_cell['HA'], 0)
        self.assertEqual(first_cell['VA'], 1)
        self.assertEqual(first_cell['wrap_text'], True)
        self.assertEqual(first_cell['O'], 0)
        self.assertEqual(first_cell['coordinates'], (0, 0))

    def test_cell_attributes(self):
        """
        Test the cells for having all attributes
        :return:
        """
        for row in self.table_8K['Cells']:
            for cell in row:
                # Check if it contains the following attributes
                self.assertIn('FB', cell)
                self.assertIn('I', cell)
                self.assertIn('font_name', cell)
                self.assertIn('font_size', cell)
                self.assertIn('FC', cell)
                self.assertIn('BC', cell)
                self.assertIn('HA', cell)
                self.assertIn('VA', cell)
                self.assertIn('wrap_text', cell)
                self.assertIn('O', cell)
                self.assertIn('coordinates', cell)
                self.assertIn('is_header', cell)
                self.assertIn('V', cell)
                self.assertIn('is_attribute', cell)
                self.assertIn('NS', cell)
                self.assertIn('LB', cell)
                self.assertIn('TB', cell)
                self.assertIn('BB', cell)
                self.assertIn('RB', cell)
                self.assertIn('DT', cell)


suite = unittest.TestLoader().loadTestsFromTestCase(TestCellAttributesExtraction8K)
unittest.TextTestRunner(verbosity=2).run(suite)
