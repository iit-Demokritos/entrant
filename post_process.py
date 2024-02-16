#
# post_process.py
# Post process output JSON files and remove noisy ones
#

import json
import os
from os import walk
from tqdm import tqdm
import logging

logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]\t%(message)s")
skippedTables_logFormatter = logging.Formatter(
    "%(message)s")

rootLogger = logging.getLogger('Post_Processing')
skippedLogger = logging.getLogger('Removed_tables')

fileHandler = logging.FileHandler(
    "{0}/{1}.log".format('./', 'output_post_processing'), 'w')

skippedTables_fileHandler = logging.FileHandler(
    "{0}/{1}.log".format('./', 'removed_tables_post_processing'), 'w')

fileHandler.setFormatter(logFormatter)
skippedTables_fileHandler.setFormatter(skippedTables_logFormatter)

rootLogger.addHandler(fileHandler)
skippedLogger.addHandler(skippedTables_fileHandler)

# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)
skippedLogger.setLevel(logging.INFO)


def clean_str(str):
    characters = ['&#32', '&#160', '&#8192', '&#8193', '&#8194', '&#8195', '&#8196', '&#8197',
                  '&#8198', '&#8199', '&#8200', '&#8201', '&#8202', '&#8232', '&#8287', '&#12288']
    new_str = str
    for c in characters:
        new_str = new_str.replace(c, ' ')
    return new_str.strip()


def clean_report(report):
    """
    Clean the given report
    :param report: the report to clean
    :return:
    """
    clean_output = []
    table_idx_to_remove = []
    # It is a list of tables
    for table_idx, table in enumerate(report):
        empty_row_idx = None
        num_empty_rows = 0
        num_columns = len(table['Cells'][0])
        for row_idx, row in enumerate(table['Cells']):
            num_Nones = 0
            for column in row:
                if column['V'] == "":
                    num_Nones += 1
                else:
                    column['V'] = clean_str(column['V'])
            if num_Nones == num_columns:
                num_empty_rows += 1
                empty_row_idx = row_idx
        # For this table: if it has more than one row empty, then remove
        if num_empty_rows > 1:
            table_idx_to_remove.append(table_idx)
            skippedLogger.info(f'Skipped table: {table["Title"]}')
        else:
            # Just remove that empty row from the table
            if empty_row_idx is not None:
                table['Cells'].pop(empty_row_idx)
    for table_idx, table in enumerate(report):
        if table_idx not in table_idx_to_remove:
            clean_output.append(table)
    return clean_output


def batch_process(directory):
    """
    Batch post processing of JSON files
    :param directory: The directory containing the json files
    :return:
    """
    print('Getting filenames for post processing..')
    files = []
    for (dirpath, dirnames, filenames) in walk(directory):
        for file in filenames:
            files.append(os.path.join(dirpath, file))
    cnt_errors = 0
    print('Processing files..')
    for file in tqdm(files):
        with open(file) as fp:
            filedata = fp.read()
            report = json.loads(filedata)
            output_filename = './output_cleaned/' + file.split('/')[-1]
            cleaned_data = clean_report(report)
            with open(output_filename, 'w') as fout:
                fout.write(json.dumps(cleaned_data))


if __name__ == "__main__":
    batch_process('./temp_output')
