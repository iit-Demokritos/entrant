#
# bitree_test.py
# Test the tree extraction process
#

import sys
import unittest
from extract_tables import process_wb
from openpyxl import load_workbook
import os

sys.path.append('../')


class TestBiTreeExtraction10K(unittest.TestCase):
    """Test the bi tree extraction process"""

    def setUp(self):
        # Load a test 10-K report and extract data
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        workbook = load_workbook(ROOT_DIR + '/test-data/10-K.xlsx')
        self.tables_10K = process_wb(workbook)

    def testTopHeaders(self):
        """Test the number of top headers"""
        # The first 3 tables should have 2 header rows
        # The 4th table should have 1 header row
        for t in range(0, 3):
            self.assertEqual(self.tables_10K[t]['TopHeaderRowsNumber'], 2)
        self.assertEqual(self.tables_10K[3]['TopHeaderRowsNumber'], 1)

    def testLeftHeaders(self):
        """Test the number of left headers"""
        # The first 4 tables should have 2 left headers
        for t in range(0, 4):
            self.assertEqual(self.tables_10K[t]['LeftHeaderColumnsNumber'], 2)

    def testTopTreeRoot(self):
        """Test the top tree root"""
        # Test 1st table
        top_tree = self.tables_10K[0]['TopTreeRoot']
        # The top tree root should have coordinates (-1,-1)
        self.assertEqual(top_tree['RI'], -1)
        self.assertEqual(top_tree['CI'], -1)
        # Should have 4 children
        self.assertEqual(len(top_tree['Cd']), 4)

    def testTopTree(self):
        """Test the top tree"""
        # Test 1st table
        top_tree = self.tables_10K[0]['TopTreeRoot']
        self.assertEqual(len(top_tree['Cd'][0]['Cd']), 0)

        self.assertEqual(len(top_tree['Cd'][1]['Cd']), 1)
        self.assertEqual(len(top_tree['Cd'][2]['Cd']), 0)
        self.assertEqual(top_tree['Cd'][1]['RI'], 0)
        self.assertEqual(top_tree['Cd'][1]['CI'], 1)
        self.assertEqual(top_tree['Cd'][2]['RI'], 1)
        self.assertEqual(top_tree['Cd'][2]['CI'], 2)

    def testLeftTreeRoot(self):
        """Test the left tree root"""
        # Test the 1st table
        left_tree = self.tables_10K[0]['LeftTreeRoot']
        # The left tree root should have coordinates (-1,-1)
        self.assertEqual(left_tree['RI'], -1)
        self.assertEqual(left_tree['CI'], -1)
        # Should have 24 children
        self.assertEqual(len(left_tree['Cd']), 26)

    def test_left_tree(self):
        """Test the left tree"""
        # Test the 1st table
        left_tree = self.tables_10K[0]['LeftTreeRoot']
        childrens_per_child = [
            0, 0, 31, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3
        ]
        for val, child in enumerate(left_tree['Cd']):
            self.assertEqual(len(child['Cd']), childrens_per_child[val])
        # The coordinates of the children of the left root
        coordinates = [
            0, 1, 2, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 84, 89, 94, 99, 104, 109, 114, 119, 124, 129,
            134, 139, 144
        ]
        for val, child in enumerate(left_tree['Cd']):
            self.assertEqual(child['RI'], coordinates[val])
            self.assertEqual(child['CI'], 0)


suite = unittest.TestLoader().loadTestsFromTestCase(TestBiTreeExtraction10K)
unittest.TextTestRunner(verbosity=2).run(suite)
