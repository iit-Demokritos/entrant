#
# CTC_input.py
# Test CTC input for consistency
#

import sys
import unittest
import os
import json

sys.path.append('../')


class TestCellTypeClassificationInput(unittest.TestCase):
    """Test input for the CTC downstream task"""

    def setUp(self):
        # Load the json file that constitutes the input
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        filename = ROOT_DIR + '/../output_CTC/cius.json'
        with open(filename, 'r') as fp:
            self.tables = json.loads(fp.read())

    def test_number_of_rows(self):
        """
        Test the number of rows
        :return:
        """
        for key in self.tables:
            data = self.tables[key]
            string_matrix = data['string_matrix']
            format_matrix = data['format_matrix']
            label_matrix = data['label_matrix']
            datarange = data['range']
            # Checks based on string matrix lengths
            num_rows = len(string_matrix)
            num_columns = len(string_matrix[0])
            self.assertEqual(num_rows, len(format_matrix))
            self.assertEqual(num_columns, len(format_matrix[0]))
            self.assertEqual(num_rows, len(label_matrix))
            self.assertEqual(num_columns, len(label_matrix[0]))
            self.assertEqual(num_rows, datarange[1] - datarange[0] + 1)  # Starting from 0 index
            self.assertEqual(num_columns, datarange[3] - datarange[2] + 1)  # Starting from 0 index

    def test_columns_per_row(self):
        """
        Test each row for the same column length
        :return:
        """
        for key in self.tables:
            data = self.tables[key]
            string_matrix = data['string_matrix']
            format_matrix = data['format_matrix']
            label_matrix = data['label_matrix']
            num_columns = len(string_matrix[0])
            for row in string_matrix:
                self.assertEqual(num_columns, len(row))
            for row in format_matrix:
                self.assertEqual(num_columns, len(row))
            for row in label_matrix:
                self.assertEqual(num_columns, len(row))

    def test_dataranges(self):
        """
        # Check if there is a data range that does not start from 0
        :return:
        """
        for key in self.tables:
            data = self.tables[key]
            datarange = data['range']
            self.assertEqual(datarange[0], 0)
            self.assertEqual(datarange[2], 0)

    def test_format_matrix(self):
        """
        # Scan format matrix for zero or negative values in merge rows and columns
        :return:
        """
        for key in self.tables:
            data = self.tables[key]
            format_matrix = data['format_matrix']
            datarange = data['range']
            for row in format_matrix:
                for cell in row:
                    merged_rows = cell[0]
                    merged_cols = cell[1]
                    self.assertGreaterEqual(merged_rows, 0)
                    self.assertGreaterEqual(merged_cols, 0)
                    self.assertLessEqual(merged_rows, datarange[1] + 1)
                    self.assertLessEqual(merged_cols, datarange[3] + 1)

    def test_position_lists(self):
        """
        # Scan all the position lists to see if they are between the range
        :return:
        """
        for key in self.tables:
            data = self.tables[key]
            datarange = data['range']
            position_lists = data['position_lists']
            column_list = position_lists[0]
            row_list = position_lists[1]
            for cell in column_list:
                position = cell[3]
                self.assertLessEqual(position, datarange[3])
            for cell in row_list:
                position = cell[3]
                self.assertLessEqual(position, datarange[1])


suite = unittest.TestLoader().loadTestsFromTestCase(TestCellTypeClassificationInput)
unittest.TextTestRunner(verbosity=2).run(suite)
