#
# merged_regions_test.py
# Test the merged regions that are extracted
#

import sys
import unittest
from extract_tables import process_ws
from openpyxl import load_workbook
import os

sys.path.append('../')


class TestMergedRegions(unittest.TestCase):
    """Test the merged regions extraction"""

    def setUp(self):
        # Load a test 10-K report and extract data
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        workbook = load_workbook(ROOT_DIR + '/test-data/10-K.xlsx')
        worksheets = workbook.worksheets
        worksheet = workbook[worksheets[0].title]
        self.table_10K = process_ws(worksheet)

    def test_merged_regions_len(self):
        """
        Test the table's merged regions
        :return:
        """
        # Should have one merged region
        self.assertEqual(len(self.table_10K['MergedRegions']), 1)

    def test_merged_region(self):
        """
        Test a specific merged region
        :return:
        """
        # Should have:
        # FirstRow: 1
        # LastRow: 2
        # FirstColumn: 1
        # LastColumn: 1
        self.assertEqual(self.table_10K['MergedRegions'][0]['FirstRow'], 0)
        self.assertEqual(self.table_10K['MergedRegions'][0]['LastRow'], 1)
        self.assertEqual(self.table_10K['MergedRegions'][0]['FirstColumn'], 0)
        self.assertEqual(self.table_10K['MergedRegions'][0]['LastColumn'], 0)


suite = unittest.TestLoader().loadTestsFromTestCase(TestMergedRegions)
unittest.TextTestRunner(verbosity=2).run(suite)
