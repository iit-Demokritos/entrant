#
# convert_xls_to_xlsx.py
# Transcode xls to xlsx in order for pyopenxl to be able to handle them
#

from xls2xlsx import XLS2XLSX
from tqdm import tqdm
from os import walk

print("Getting filenames..")
files = []
for (dirpath, dirnames, filenames) in walk('./CIUS_data_xls'):
    files.extend(filenames)
print('Processing workbooks..')
correctly_processed = 0
errors = 0
for file in tqdm(files):
    filename = file.split('.')[0]
    file_in = './CIUS_data_xls/' + file
    file_out = './CIUS_data_xlsx/' + filename + '.xlsx'
    try:
        x2x = XLS2XLSX(file_in)
        x2x.to_xlsx(file_out)
        correctly_processed += 1
    except:
        errors += 1
print(f'Successfully parsed: {correctly_processed}')
print(f'Errors: {errors}')
