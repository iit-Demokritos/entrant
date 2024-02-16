# ENTRANT: A Large Financial Dataset for Table Understanding

> Extract and clean tables from financial xlsx files from EDGAR and convert them to JSON with
> bi-tree positional information and metadata.
> 
## Table of Contents
- [Install](#install)
- [Usage](#usage)

## Install
- Before starting, ideally, it's recommended to switch to a virtual environment first via `conda` or `virtualenv` or Python's `venv` module.
- Install dependencies via `pip install -r requirements.txt`

## Usage
### For table extraction from EDGAR:
- Place the xls files in a directory named `data` in the project's root.
- Create a directory named `output` to store the results.
- Run `extract_tables_multiprocess.py`.

### For downloading XBRL reports
- Please, consult the following link for the specifications of both XBRL-XML and XBRL-JSON:
https://specifications.xbrl.org/work-product-index-open-information-model-open-information-model.html
- See `download_reports.py`