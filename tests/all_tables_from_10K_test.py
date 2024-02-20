#
# all_tables_from_10K_test.py
# Test the table extraction process from a 10K report
#

import sys
import unittest
from extract_tables import process_wb
from openpyxl import load_workbook
import os

sys.path.append('../')


class TestWbTableExtraction10K(unittest.TestCase):
    """Test the table extraction process"""

    def setUp(self):
        # Load a couple of test 10-K report and extract data
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        workbook = load_workbook(ROOT_DIR + '/test-data/10-K.xlsx')
        self.tables_10K = process_wb(workbook)

    def test_number_of_tables(self):
        """
        Test the number of extracted tables
        :return:
        """
        # Should extract at least 8 tables
        self.assertGreaterEqual(len(self.tables_10K), 8)

    def test_table_titles(self):
        """
        Test the title for each table
        :return:
        """
        # Should have the following titles for the first tables
        titles = [
            'Document and Entity Information - USD ($) $ in Billions',
            'CONSOLIDATED INCOME STATEMENT - USD ($) $ in Millions',
            'CONSOLIDATED STATEMENT OF COMPREHENSIVE INCOME - USD ($) $ in Millions'
        ]
        for i, t in enumerate(titles):
            self.assertEqual(self.tables_10K[i]['Title'], t)

    def test_table_rows_lengths(self):
        """
        Test the rows for each table
        :return:
        """
        # Should have the following rows for each table
        lengths = [148, 37, 24, 49, 10, 43, 8, 8]
        for i, s in enumerate(lengths):
            self.assertEqual(len(self.tables_10K[i]['Cells']), s)

    def test_table_cells_lengths(self):
        """
        Test the cells for each table
        :return:
        """
        # Should have the following cells
        cells = [4, 4, 4, 3, 3, 4, 4]
        for i, cell in enumerate(cells):
            for row in self.tables_10K[i]['Cells']:
                self.assertEqual(len(row), cell)


suite = unittest.TestLoader().loadTestsFromTestCase(TestWbTableExtraction10K)
unittest.TextTestRunner(verbosity=2).run(suite)
