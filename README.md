![python application](https://github.com/izavits/entrant/actions/workflows/python-app.yml/badge.svg)
![python lint](https://github.com/izavits/entrant/actions/workflows/python-lint.yml/badge.svg)


# ENTRANT: A Large Financial Dataset for Table Understanding

> Extract and clean tables from financial xlsx files from EDGAR and convert them to JSON with
> bi-tree positional information and metadata.
> 
> Related dataset:
> 
> Zavitsanos, E., Mavroeidis, D., Spyropoulou, E., Fergadiotis, M., & Paliouras, G. (2024). ENTRANT: A Large Financial Dataset for Table Understanding [Data set]. Zenodo. https://doi.org/10.5281/zenodo.10667088
> 

## Table of Contents
- [Install](#install)
- [Usage](#usage)
- [Data](#data)
- [Tests](#tests)
- [License](#license)

## Install
- Before starting, ideally, it's recommended to switch to a virtual environment first via `conda` or `virtualenv`.
- Install dependencies via `pip install -r requirements.txt`

## Usage
### For table extraction from EDGAR:
- Place the xls files in a directory named `data` in the project's root.
- Create a directory named `output` to store the results.
- Run `extract_tables_multiprocess.py`.

### For downloading excel reports
- See `fetch_reports.py`
- Pay attention to fair usage of EDGAR

## Data
- Data is hosted at Zenodo: https://zenodo.org/records/10667088

## Tests
Use `pytest` to run the unit tests.

## License
The project is licensed under Creative Commons Attribution 4 license.
