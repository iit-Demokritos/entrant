#
# table_from_10K_test.py
# Test the table extraction process from a 10K report
#

import sys
import unittest
from extract_tables import process_ws
from openpyxl import load_workbook
import os

sys.path.append('../')


class TestTableExtraction10K(unittest.TestCase):
    """Test the table extraction process"""

    def setUp(self):
        # Load a couple of test 10-K report and extract data
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        workbook = load_workbook(ROOT_DIR + '/test-data/10-K.xlsx')
        worksheets = workbook.worksheets
        worksheet = workbook[worksheets[0].title]
        self.table_10K = process_ws(worksheet)

    def test_table_title(self):
        """
        Test the table title
        :return:
        """
        # Should have title "Document and Entity Information"
        self.assertEqual(self.table_10K['Title'],
                         'Document and Entity Information - USD ($) $ in Billions')

    def test_table_rows_len(self):
        """
        Test the table rows
        :return:
        """
        # Should have 148 rows the 10-K table and 55 the 2nd doc
        self.assertEqual(len(self.table_10K['Cells']), 148)

    def test_table_header(self):
        """
        Test the table header
        :return:
        """
        # Should have rows 0,1,2,34,39,44,49,54,59,64,69,74,79,84,89,94,99,
        # 104,109,114,119,124,129,134,139,144 as header
        headers = [0, 1, 2, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 84, 89, 94, 99, 104, 109, 114, 119, 124,
                   129, 134, 139, 144]
        for i in headers:
            self.assertEqual(self.table_10K['Cells'][i][0]['is_header'], True)

    def test_table_cells_len(self):
        """
        Test the cells
        :return:
        """
        # Should have 4 cells at each row
        for row in self.table_10K['Cells']:
            cells = row
            self.assertEqual(len(cells), 4)


suite = unittest.TestLoader().loadTestsFromTestCase(TestTableExtraction10K)
unittest.TextTestRunner(verbosity=2).run(suite)
