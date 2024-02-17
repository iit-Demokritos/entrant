import requests
import os
from requests.adapters import HTTPAdapter
import json
from urllib3.util import Retry
import numpy as np


def download_excels(excel_urls_list):
    """
    param: excel_urls_list: list of urls to download
    """
    with open(excel_urls_list) as fp:
        lines = fp.readlines()
        for line in lines:
            url = line.split(';')[-1]
            url = url.replace('\n', '')
            if 'http' in url:
                retry_strategy = Retry(
                    total=3,
                    status_forcelist=[101, 429, 500, 502, 503, 504],
                    # method_whitelist=["HEAD", "GET", "OPTIONS"],
                    backoff_factor=2,
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                http = requests.Session()
                http.mount("https://", adapter)
                http.mount("http://", adapter)
                r = http.get(
                    url=url,
                    headers={"User-agent": "Mozilla/5.0"},
                    stream=True,
                )
                if r.status_code == 200:
                    print(f"Correctly retrieved {url}.")
                    filename = url.split('/')[-2]
                    open(f'./output/{filename}.xlsx', 'wb').write(r.content)


def download_cik_submission_jsons(cik):
    save_file = os.path.join("submissions", f"{cik}.json")
    initial_submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    print(f"URL: {initial_submission_url}")

    if not os.path.exists(save_file):
        retry_strategy = Retry(
            total=3,
            status_forcelist=[101, 429, 500, 502, 503, 504],
            # method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)
        r = http.get(
            url=initial_submission_url,
            headers={"User-agent": "Mozilla/5.0"},
            stream=True,
        )
        error_file = "errors.txt"
        if r.status_code == 200:
            print(f"Correctly retrieved document.")
            data_json = r.json()
            with open(save_file, "w") as fp:
                json.dump(data_json, fp)
        else:
            print(
                f"{cik}: Error occured in request {initial_submission_url}. "
                f"Status code: {r.status_code}"
            )
            with open(error_file, "w") as ef:
                ef.write(
                    f"{cik}: Error occured in request "
                    f"{initial_submission_url}."
                    f" Status code: {r.status_code}"
                )
    else:
        print(f"File {save_file} already exists.")


def parse_submission_for_10K(cik, type_of_report):
    with open('./submissions/' + cik + '.json') as fp:
        submission = json.load(fp)
        forms = submission['filings']['recent']['form']
        forms = np.array(forms)
        searchval = type_of_report
        indices = np.where(forms == searchval)[0]
        accession_numbers = []
        urls = []
        for idx in indices:
            accession_numbers.append(submission['filings']['recent']['accessionNumber'][idx])
            accession_num = submission['filings']['recent']['accessionNumber'][idx]
            accession_num = accession_num.replace('-', '')
            url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_num}/Financial_Report.xlsx'
            urls.append(url)
        with open(f'./urls_lists/{cik}.txt', 'w') as fw:
            for url in urls:
                fw.write(url + '\n')


if __name__ == "__main__":
    # download_cik_submission_jsons('0000320193')
    #parse_submission_for_10K('0000320193', '10-K')
    download_excels('./urls_lists/0000320193.txt')