import argparse
import json
import numpy as np
import os
import pandas as pd
import re
import requests
import subprocess
import sys
from bs4 import BeautifulSoup
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Get command-line parameters
parser = argparse.ArgumentParser(
    description="Mass download xbrl or excel files that contain financial "
    "reporting data from EDGAR."
)

parser.add_argument(
    "--cik_list_file",
    "-c",
    type=str,
    help="The path of the file that contains a list of CIKs.",
)

parser.add_argument(
    "--output_path", "-o", type=str, help="The path of the output files."
)

parser.add_argument(
    "--document_type",
    "-t",
    type=str,
    choices=["xbrl", "excel", "zip_xbrl"],
    help="The type of document to download (xbrl or excel).",
)


args = parser.parse_args()
cik_list_file = args.cik_list_file
output_path = args.output_path
document_type = args.document_type


def download_cik_submission_jsons(cik, output_path, additional=None):
    # Get main submission json

    if additional:
        save_file = os.path.join(
            output_path, "submissions", f"{cik}_{str(additional)}.json"
        )
        additional_str = str(additional).zfill(3)
        initial_submission_url = (
            f"https://data.sec.gov/submissions/CIK{cik}-submissions-"
            f"{additional_str}.json"
        )
        print(f"URL: {initial_submission_url}")
    else:
        save_file = os.path.join(output_path, "submissions", f"{cik}.json")
        initial_submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        print(f"URL: {initial_submission_url}")

    if not os.path.exists(save_file):
        retry_strategy = Retry(
            total=3,
            status_forcelist=[101, 429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
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
            if not additional:
                if data_json["filings"]["files"]:
                    for i, item in enumerate(data_json["filings"]["files"]):
                        download_cik_submission_jsons(
                            cik, output_path, additional=i + 1
                        )
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


def download(cik_list_file, output_path):
    # First, get the list of CIKs
    ciks = []
    # File is separated by the character ":", but it is not consistent. Very
    # often, the first column will contain this character, which makes
    # reading the csv very hard. So, I have worked around it by separating
    # each line with ":", storing to a list, reversing the list and storing
    # only columns 1 and 2 (starting from 0) which are the ones I need.
    with open(cik_list_file, "r") as f:
        file_lines = f.readlines()
    for line in file_lines:
        line_list = line.split(":")
        line_list = list(reversed(line_list))
        ciks.append(line_list[1])

    for cik in ciks:
        download_cik_submission_jsons(cik, output_path=output_path)


def download_files(output_path, document_type):

    retrieved_list = set()
    new_retrieved_list = set()
    files_path = ""
    urls_file = ""
    retrieved_file = ""
    error_file = ""
    if document_type == "excel":
        files_path = os.path.join(output_path, "excel_files")
        urls_file = "excel_urls_list.csv"
        retrieved_file = "retrieved_excel_files.txt"
        error_file = "excel_errors.txt"
    elif document_type == "xbrl":
        files_path = os.path.join(output_path, "xbrl_files")
        urls_file = "xbrl_urls_list.csv"
        retrieved_file = "retrieved_xbrl_files.txt"
        error_file = "xbrl_errors.txt"
    elif document_type == "zip_xbrl":
        files_path = os.path.join(output_path, "xbrl_zip_files")
        urls_file = "xbrl_zip_urls_list.csv"
        retrieved_file = "retrieved_xbrl_zip_files.txt"
        error_file = "xbrl_zip_errors.txt"

    # Load the list that contains the visited URLs
    if not os.path.exists(retrieved_file):
        Path(retrieved_file).touch()
    with open(retrieved_file) as f:
        for line in f:
            retrieved_list.add(line.rstrip())

    # Load the list of error URLs
    error_urls_list = set()
    new_error_urls_list = set()
    if not os.path.exists(error_file):
        Path(error_file).touch()
    with open(error_file, "r") as f:
        for line in f:
            error_urls_list.add(line.rstrip())
    retry_strategy = Retry(
        total=3,
        status_forcelist=[101, 429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=2,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    with open("cik_ticker.tsv", "r") as cik_file:
        df_cik = pd.read_csv(cik_file, sep="\t")

    urls_path = os.path.join("input_data", "urls_htm")

    for urls_file in sorted(os.listdir(urls_path)):
        # Load the dataframe with excel files info and URLs
        urls_file_path = os.path.join(urls_path, urls_file)
        accessions_dataframe = pd.read_csv(urls_file_path, sep=";")
        for idx, item in accessions_dataframe.iterrows():
            cik = item["cik"]
            # Get cik's tickers
            tickers = get_tickers(cik=cik, df_cik=df_cik)
            for ticker in tickers:
                url = item["url_" + ticker]
                if not url in retrieved_list:
                    if not url in error_urls_list:
                        reporting_date = item["reporting_date"]
                        is_inline_xbrl = item["is_inline_xbrl_flag"]
                        report_type = (
                            item["report_type"].replace("/", "-").replace(" ", "_")
                        )
                        accession_number = item["accession_number_for_url"]
                        file_name = ""
                        if document_type == "excel":
                            file_name = (
                                f"{cik}_{ticker}_{reporting_date}"
                                f"_{report_type}_"
                                f"{accession_number}.xlsx"
                            )
                        elif document_type == "zip_xbrl":
                            file_name = (
                                f"{cik}_{ticker}_{reporting_date}_{report_type}_"
                                f"{accession_number}-xbrl.zip"
                            )
                        elif document_type == "xbrl":
                            file_name = url.split("/")[-1]
                            # print(file_name)
                            # if is_inline_xbrl == 1:
                            #     file_name = f'{cik}_{ticker}_{reporting_date}_{report_type}_' \
                            #                       f'{accession_number}.htm'
                            # elif is_inline_xbrl == 0:
                            #     file_name = f'{cik}_{ticker}_{reporting_date}_{report_type}_' \
                            #                 f'{accession_number}.xml'
                        single_file_full_path = os.path.join(
                            files_path, str(cik), str(accession_number)
                        )
                        file_full_path = os.path.join(single_file_full_path, file_name)
                        if not os.path.exists(single_file_full_path):
                            os.makedirs(single_file_full_path)
                        if not os.path.exists(file_full_path):
                            r = http.get(
                                url=url,
                                headers={"User-agent": "Mozilla/5.0"},
                                stream=True,
                            )
                            if r.status_code == 200:
                                print(f"Correctly retrieved {url}.")
                                with open(file_full_path, "wb") as fp:
                                    fp.write(r.content)
                                new_retrieved_list.add(url)
                            else:
                                error_string = (
                                    f"{cik}: Error occured in request"
                                    f" {url}. Status code:"
                                    f" {r.status_code}"
                                )
                                new_error_urls_list.add(url)
                                print(error_string)
                        else:
                            print(f"File {file_name} already exists.")
                            retrieved_list.add(url)
                    else:
                        print(
                            "This URL has already returned a 404 error in " "the past."
                        )
                else:
                    print(f"File {url} already retrieved.")
        with open(retrieved_file, "a") as rf:
            rf.write("\n".join(new_retrieved_list))
        with open(error_file, "a") as ef:
            ef.writelines("\n".join(new_error_urls_list))


def get_tickers(cik, df_cik):
    """
    Given a CIK, find the corresponding list of tickers.

    :rtype: str
    :param cik: int
    :param df_cik: Dataframe
    """

    cik_for_url = str(cik).lstrip("0")
    # TODO: Need to take into account that multiple
    #  tickers can correspond to only one CIK. Thus,
    #  we need to take a list of matching tickers and not
    #  just the first ticker that we come accross.

    tickers = df_cik.loc[df_cik["cik"].astype(str) == cik_for_url, "ticker"]
    if tickers.size > 1:
        print(f"tickers: {tickers}")
    return tickers


def build_url_list(input_path, document_type):
    """
    Build the URL list for either xbrl, excel, html, or other future formats
    for xBRL reports. Just provide the path where the submission json files
    are stored and the type of files to download (xbrl, excel, xbrl_zip).
    Selection "xbrl" retrieves both htm (inline xBRL) and xml. This is done
    offline. We get the ciks and accession keys from the jsons and build the
    URLs for downloading the files.

    :param input_path: str
    :param document_type: str
    """
    urls_list = []
    all_accessions = {}
    all_tickers = {}

    secondary_file = False
    urls_list_file_path = ""
    with open("cik_ticker.tsv", "r") as cik_file:
        df_cik = pd.read_csv(cik_file, sep="\t")
    if document_type == "excel":
        urls_list_file_path = "excel_urls_list.csv"
    elif document_type == "xbrl":
        urls_list_file_path = "xbrl_urls_list_1.csv"
    submissions_path = os.path.join(input_path, "submissions")
    urls_path = os.path.join(input_path, "urls_htm")
    if not os.path.exists(urls_path):
        os.makedirs(urls_path)

    for file in sorted(os.listdir(submissions_path)):
        tickers = []
        accessions_dataframe = pd.DataFrame()
        print(f"Checking file: {file}")
        file_path = os.path.join(submissions_path, file)
        with open(file_path, "r") as f:
            json_object = json.load(f)
        try:
            cik = str(json_object["cik"]).lstrip("0")
            tickers = json_object["tickers"]
            if tickers == []:
                tickers = get_tickers(cik=cik, df_cik=df_cik)
                if len(tickers) > 1:
                    print(f"Found more than one tickers for cik: {cik}")
            accession_info = json_object["filings"]["recent"]
        except KeyError:
            # If there isn't cik or ticker in the json, then we are dealing
            # with the secondary submission file, which means that we should
            # store relevant data to the cik that is in the file name.
            secondary_file = True
            cik = file.split("_")[0].lstrip("0")
            tickers = all_tickers[cik]
            accession_info = json_object
        accessions_dataframe["accession_number"] = accession_info["accessionNumber"]
        accessions_dataframe["report_type"] = accession_info["form"]
        accessions_dataframe["report_type_for_url"] = (
            accessions_dataframe["report_type"].astype(str).str.replace("-", "")
        )
        accessions_dataframe["report_type_for_url"] = accessions_dataframe[
            "report_type_for_url"
        ].str.lower()
        accessions_dataframe["reporting_date"] = accession_info["reportDate"]
        accessions_dataframe["filing_date"] = accession_info["filingDate"]
        accessions_dataframe["is_xbrl_flag"] = accession_info["isXBRL"]
        accessions_dataframe["is_inline_xbrl_flag"] = accession_info["isInlineXBRL"]
        accessions_dataframe["cik"] = cik
        all_tickers[cik] = tickers

        # Format report type for htm urls
        accessions_dataframe["report_type_for_url"] = (
            accessions_dataframe["report_type"].astype(str).str.replace("-", "")
        )
        accessions_dataframe["report_type_for_url"] = (
            accessions_dataframe["report_type_for_url"].astype(str).str.replace("_", "")
        )
        accessions_dataframe["report_type_for_url"] = (
            accessions_dataframe["report_type_for_url"].astype(str).str.replace("/", "")
        )
        accessions_dataframe["report_type_for_url"] = (
            accessions_dataframe["report_type_for_url"].astype(str).str.lower()
        )

        try:
            # accessions_dataframe['fiscal_year_end'] = accessions_dataframe[
            #     'fiscal_year_end'].replace(r'^\s*$', np.NaN, regex=True)
            accessions_dataframe["fiscal_year_end"] = accession_info["fiscalYearEnd"]
        except:
            accessions_dataframe["fiscal_year_end"] = ""
            print("No fiscal year end")
        try:
            accessions_dataframe["filing_date"] = accessions_dataframe[
                "filing_date"
            ].replace(r"^\s*$", np.NaN, regex=True)
        except:
            print("No filing date")
        accessions_dataframe["reporting_date"] = accessions_dataframe[
            "reporting_date"
        ].replace(r"^\s*$", np.NaN, regex=True)
        if not secondary_file:
            all_accessions[cik] = accessions_dataframe
        if not accessions_dataframe["filing_date"].empty:
            accessions_dataframe["filing_year"] = (
                accessions_dataframe["filing_date"].str[0:4].astype(int)
            )
        if not accessions_dataframe["reporting_date"].empty:
            try:
                accessions_dataframe["reporting_year"] = (
                    accessions_dataframe["reporting_date"].str[0:4].astype(int)
                )
            except ValueError:
                print(f'Value Error: {accessions_dataframe["reporting_date"]}')
        accessions_dataframe = accessions_dataframe[
            (accessions_dataframe["is_xbrl_flag"] == 1)
            | (accessions_dataframe["is_inline_xbrl_flag"] == 1)
        ]
        accessions_dataframe["cik_for_url"] = (
            accessions_dataframe["cik"].astype(int).astype(str)
        )
        accessions_dataframe["accession_number_for_url"] = (
            accessions_dataframe["accession_number"].astype(str).str.replace("-", "")
        )
        if document_type == "excel":
            accessions_dataframe["url"] = (
                "https://www.sec.gov/Archives/edgar/data/"
                + accessions_dataframe["cik_for_url"].astype(str)
                + "/"
                + accessions_dataframe["accession_number_for_url"].astype(str)
                + "/Financial_Report.xlsx"
            )
        elif document_type == "zip_xbrl":
            accessions_dataframe["url"] = (
                "https://www.sec.gov/Archives/edgar/data/"
                + accessions_dataframe["cik_for_url"].astype(str)
                + "/"
                + accessions_dataframe["accession_number_for_url"].astype(str)
                + "/"
                + accessions_dataframe["accession_number"].astype(str)
                + "-xbrl.zip"
            )
        elif document_type == "xbrl":
            if (
                accessions_dataframe["reporting_date"].empty
                and not accessions_dataframe["filing_date"].empty
            ):
                accessions_dataframe["year_for_xml_url"] = (
                    accessions_dataframe["filing_year"].astype(int) - 1
                )
                accessions_dataframe["date_for_xml_url"] = (
                    accessions_dataframe["year_for_xml_url"].astype(str)
                    + accessions_dataframe["fiscal_year_end"]
                )
            else:
                accessions_dataframe["date_for_xml_url"] = (
                    accessions_dataframe["reporting_date"]
                    .astype(str)
                    .str.replace("-", "")
                )

            if not accessions_dataframe.empty:
                for ticker in tickers:
                    ticker = ticker.lower()
                    print(f"ticker from the list of tickers: {ticker}")
                    accessions_dataframe["url_" + ticker] = (
                        "https://www.sec.gov/Archives/edgar/data/"
                        + accessions_dataframe["cik_for_url"].astype(str)
                        + "/"
                        + accessions_dataframe["accession_number_for_url"].astype(str)
                        + "/"
                        + ticker
                        + "-"
                        + accessions_dataframe["date_for_xml_url"].astype(str)
                        + ".htm"
                    )
                    # Keep only inline xbrl entries
                    accessions_dataframe = accessions_dataframe[
                        (accessions_dataframe["is_inline_xbrl_flag"] == 1)
                    ]
                    for index, row in accessions_dataframe.iterrows():
                        print(f"full URL for html:" f" {row['url_' + ticker]}")

                    # https://www.sec.gov/ix?doc=/Archives/edgar/data/33002/000095017022000064/ebf-20211130.htm
                    # accessions_dataframe['url_' + ticker] = \
                    #     "https://www.sec.gov/Archives/edgar/data/" + \
                    #     accessions_dataframe['cik_for_url'].astype(str) + "/"\
                    #     + accessions_dataframe[
                    #         'accession_number_for_url'].astype(str) + "/" + \
                    #     ticker + "-" + \
                    #     np.where(accessions_dataframe['is_inline_xbrl_flag'] ==
                    #              1, accessions_dataframe[
                    #         'report_type_for_url'] + '_htm', '') + \
                    #     accessions_dataframe['date_for_xml_url'].astype(str) + \
                    #     np.where(accessions_dataframe['is_inline_xbrl_flag'] ==
                    #              1, '.htm', '.xml')
                    # print(f"full URL for xml: {accessions_dataframe['url_' + ticker]}")

        url_path_for_cik = os.path.join(urls_path, cik + ".csv")
        if not accessions_dataframe.empty:
            pd.DataFrame(accessions_dataframe).to_csv(
                path_or_buf=url_path_for_cik, sep=";", mode="w", index=False
            )
        # accessions_dataframe['url'] = \
        #     'https://www.sec.gov/Archives/edgar/data/' + \
        #     accessions_dataframe['cik_for_url'].astype(str) + '/' + \
        #     accessions_dataframe['accession_number_for_url'].astype(str) + \
        #     '/' + accessions_dataframe['accession_number'].astype(str) + \
        #     '-xbrl.zip'
        # XBRLs
        # https://www.sec.gov/Archives/edgar/data/1732845/000156459018029723/wrk-20180930.xml
        # https://www.sec.gov/Archives/edgar/data/100885/000010088518000048/unp-20171231.xml
        # Excel files corresponding to xbrls
        # 'https://www.sec.gov/Archives/edgar/data/1683541/000168354119000008/Financial_Report.xlsx'
        # xbrl in zip:
        # https://www.sec.gov/Archives/edgar/data/320193/000119312521001982/0001193125-21-001982-xbrl.zip
        # Inline xbrl:
        # https://www.sec.gov/Archives/edgar/data/1732845/000156459018029723/wrk-10k_20180930.htm
        # Extracted xbrl xml url:
        # https://www.sec.gov/Archives/edgar/data/1732845/000156459021057778/wrk-10k_20210930_htm.xml


def download_additional_submissions(submission_json_path):
    """
    Check whether there are additional submission jsons and download them

    :param submission_json_path: The path that contains the submissions jsons
    """
    cik = os.path.split(submission_json_path)[-1:][0].split(".")[0]
    with open(submission_json_path, "r") as f:
        try:
            cik_json = json.load(f)
        except UnicodeDecodeError:
            print(f"File {submission_json_path} is not valid. Skipping...")
    try:
        if cik_json["filings"]["files"]:
            for i, item in enumerate(cik_json["filings"]["files"]):
                download_cik_submission_jsons(cik, output_path, additional=i + 1)
    except KeyError:
        print('Json file does not contain the "filing" path. Skipping...')


def download_all_additional_submissions(submissions_path):
    for file in os.listdir(submissions_path):
        file_path = os.path.join(submissions_path, file)
        download_additional_submissions(file_path)


def download_all_report_files(input_path, arelle_command_path):

    submissions_path = os.path.join(input_path, "submissions")
    downloaded_submissions_path = os.path.join(input_path, "submissions_used")
    all_reports_downloaded = False
    arelle_command_list = []
    arelle_urls_path = os.path.join(input_path, "arelle_urls")
    if not os.path.exists(arelle_urls_path):
        os.makedirs(arelle_urls_path)
    if not os.path.exists(downloaded_submissions_path):
        os.makedirs(downloaded_submissions_path)

    # Setting up the HTTP adapter to optimize download reliability
    retry_strategy = Retry(
        total=3,
        status_forcelist=[101, 429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=3,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    current_directory = os.getcwd()

    for file in sorted(os.listdir(submissions_path)):
        accessions_dataframe = pd.DataFrame()
        accessions_dataframe = accessions_dataframe.iloc[0:0]
        file_path = os.path.join(submissions_path, file)
        with open(file_path, "r") as f:
            json_object = json.load(f)
        try:
            cik = str(json_object["cik"]).lstrip("0")
            accession_info = json_object["filings"]["recent"]
        except KeyError:
            # If there isn't cik or ticker in the json, then we are dealing
            # with the secondary submission file, which means that we should
            # store relevant data to the cik that is in the file name.
            secondary_file = True
            cik = file.split("_")[0].lstrip("0")
            accession_info = json_object
        accessions_dataframe["accession_number"] = accession_info["accessionNumber"]
        accessions_dataframe["accession_number_for_url"] = (
            accessions_dataframe["accession_number"].astype(str).str.replace("-", "")
        )
        accessions_dataframe["is_xbrl_flag"] = accession_info["isXBRL"]
        accessions_dataframe["is_inline_xbrl_flag"] = accession_info["isInlineXBRL"]

        # Filter out all reports that don't have an xBRL representation
        accessions_dataframe = accessions_dataframe[
            (accessions_dataframe["is_xbrl_flag"] == 1)
            | (accessions_dataframe["is_inline_xbrl_flag"] == 1)
        ]

        # Form URLs for all reports in the accessions dataframe
        accessions_dataframe["url"] = (
            "https://www.sec.gov/Archives/edgar/data/"
            + cik
            + "/"
            + accessions_dataframe["accession_number_for_url"]
            + "/"
        )
        # Create the reports path, if it doesn't exist
        all_reports_path = os.path.join(input_path, "all_reports")
        if not os.path.exists(all_reports_path):
            os.makedirs(all_reports_path)

        # Download
        for index, row in accessions_dataframe.iterrows():
            all_reports_downloaded = False
            accession_info_downloaded = False
            url = row["url"][0:-1]
            content = ""
            accession_number = row["accession_number_for_url"]
            file_path = os.path.join(all_reports_path, cik, accession_number)
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            # file_path = os.path.join(file_path, 'index.html')
            r = http.get(url=url, headers={"User-agent": "Mozilla/5.0"}, stream=True)
            if r.status_code == 200:
                print(f"Correctly retrieved {url}.")
                content = r.content
                accession_info_downloaded = True
                # with open(file_path, 'wb') as fp:
                #     fp.write(r.content)
                # new_retrieved_list.add(url)
            else:
                error_string = (
                    f"{cik}: Error occured in request"
                    f" {url}. Status code:"
                    f" {r.status_code}"
                )
                # new_error_urls_list.add(url)
                print(error_string)

            # Get relevant links from the html file
            if accession_info_downloaded:
                soup = BeautifulSoup(content, "html.parser")
                parent = [
                    "https://www.sec.gov" + node.get("href")
                    for node in soup.find_all("a")
                    if accession_number in node.get("href")
                    # and (node.get('href').endswith('.xsd'))
                    and (
                        (node.get("href").endswith("_htm.xml"))
                        or (node.get("href").endswith(".xsd"))
                    )
                ]

                for sub_url in parent:
                    if sub_url.endswith(".xsd"):
                        # If the url contains xsd, find the corresponding xml
                        # file and convert it to JSON-xBRL.
                        sub_url = sub_url.replace(".xsd", ".xml")
                        save_path = os.path.join(
                            current_directory,
                            "output_data",
                            "xbrl_json",
                            cik,
                            accession_number,
                        )

                        if not os.path.exists(save_path):
                            os.makedirs(save_path)
                        file_name = sub_url.split("/")[-1]
                        save_file_path = os.path.join(save_path, file_name + ".json")
                        command_for_arelle = [
                            "python",
                            arelle_command_path,
                            # f'--package-DTS={taxonomy_file_path}',
                            # f'--xdgConfigHome {current_directory}',
                            "--plugins=saveLoadableOIM",
                            f"--saveLoadableOIM={save_file_path}",
                            "-f",
                            sub_url,
                        ]
                        # Use the Arelle command here to get the xbrl file
                        # from the web in order to take advantage of the
                        # xsd caching capability, which is not available for
                        # offline xbrl files.
                        # Store command in a list to execute later if needed.
                        arelle_command_list.append(" ".join(command_for_arelle))
                        print("Command: \n" + " ".join(command_for_arelle))
                        with open("arelle_from_python.log", "ab") as out, open(
                            "arelle_from_python-error.log", "ab"
                        ) as err:
                            process = subprocess.Popen(
                                command_for_arelle, stdout=out, stderr=err
                            )
                            process.wait()
                            print(process.returncode)
                        if process.returncode == 0:
                            all_reports_downloaded = True
                        else:
                            all_reports_downloaded = False
                    elif sub_url.endswith(".htm"):
                        # If the file is HTML just keep it to extract
                        # the inline xBRL later on.
                        r = http.get(
                            url=sub_url,
                            headers={"User-agent": "Mozilla/5.0"},
                            stream=True,
                        )
                        if r.status_code == 200:
                            all_reports_downloaded = True
                            file_name = sub_url.split("/")[-1]
                            sub_file_path = os.path.join(file_path, file_name)
                            print(f"Correctly retrieved {sub_url}.")
                            content = r.content
                            with open(sub_file_path, "wb") as fp:
                                fp.write(r.content)
                        else:
                            all_reports_downloaded = False
                            error_string = (
                                f"{cik}: Error occured in request"
                                f" {sub_url}. Status code:"
                                f" {r.status_code}"
                            )
                            print(error_string)

                        if sub_url.endswith("_htm.xml"):
                            sub_url = sub_url.replace("_htm.xml", ".htm")

        # If all reports of a CIK have been downloaded, move the submission
        # file to the "done" folder.
        if all_reports_downloaded == True:
            final_submission_file_path = os.path.join(submissions_path, file)
            used_submissions_file_path = os.path.join(downloaded_submissions_path, file)
            os.replace(final_submission_file_path, used_submissions_file_path)
        arelle_urls_file_path = os.path.join(
            arelle_urls_path, f"arelle_command_list_{cik}.txt"
        )
        with open(arelle_urls_file_path, "w") as arelle_urls_file:
            arelle_urls_file.write("\n".join(arelle_command_list))
            arelle_command_list = []


def convert_reports_to_json(input_path, command_path):

    # This is for Arelle to work correctly on the mac
    if sys.platform == "darwin" and getattr(sys, "frozen", False):
        for i in range(len(sys.path)):  # signed code can't contain python modules
            sys.path.append(sys.path[i].replace("MacOS", "Resources"))

    current_directory = os.getcwd()
    reports_path = os.path.join(current_directory, input_path, "all_reports")

    # Setting up the HTTP adapter to optimize download reliability
    retry_strategy = Retry(
        total=3,
        status_forcelist=[101, 429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=3,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    print(os.getcwd())

    sorted_reports_list = sorted(os.listdir(reports_path), key=int)
    for cik in sorted_reports_list:
        cik_path = os.path.join(reports_path, cik)
        print(f"cik_path: {cik_path}")
        if cik.isdigit():
            for accession_number in sorted(os.listdir(cik_path)):
                if accession_number.isdigit():
                    accession_path = os.path.join(cik_path, accession_number)
                    r = re.compile(".*\d.*\.xml")
                    # r = re.compile("^.*(\d{8}\.xml|\d{8}_htm\.xml)$")
                    files_list = os.listdir(accession_path)
                    files_to_convert = list(filter(r.match, files_list))
                    # print(f'Accession path: {accession_path}')
                    # print(f'Accession number: {accession_number}')
                    # print(f'files_list: {files_list}')
                    # print(f'files_to_convert: {files_to_convert}')
                    r = re.compile("^.*_htm\.xml$")
                    final_xml_file = list(filter(r.match, files_to_convert))
                    if final_xml_file:
                        final_xml_file = final_xml_file[0]
                        final_html_file = final_xml_file.replace("_html.xml", ".html")
                    elif not final_xml_file and files_to_convert:
                        final_xml_file = min(files_to_convert, key=len)

                    print(f"xml file to convert: {final_xml_file}")

                    # Convert xml file using arelle command line
                    if final_xml_file:
                        file_to_convert_path = os.path.join(
                            accession_path, final_xml_file
                        )
                        print(os.getcwd())
                        save_path = os.path.join(
                            current_directory,
                            "output_data",
                            "xbrl_json",
                            cik,
                            accession_number,
                        )

                        if not os.path.exists(save_path):
                            os.makedirs(save_path)
                        save_file_path = os.path.join(
                            save_path, final_xml_file + ".json"
                        )
                        taxonomy_file_path = os.path.join(
                            save_path, final_xml_file + ".xsd"
                        )
                        command_for_arelle = [
                            "python",
                            command_path,
                            f"--package-DTS={taxonomy_file_path}",
                            "--plugins=saveLoadableOIM",
                            f"--saveLoadableOIM={save_file_path}",
                            "-f",
                            file_to_convert_path,
                        ]
                        print("Command: \n" + " ".join(command_for_arelle))
                        with open("arelle_from_python.log", "ab") as out, open(
                            "arelle_from_python-error.log", "ab"
                        ) as err:
                            process = subprocess.Popen(
                                command_for_arelle, stdout=out, stderr=err
                            )
                            process.wait()
                            print(process.returncode)

            # Command for conversion:
            # python3 ~/work/Arelle/arelleCmdLine.py
            # --plugins=saveLoadableOIM --saveLoadableOIM=ej.json
            # -f ~/work/edgar_json/input_data/all_reports/1674101/000095014221000103/eh210125218_8k_htm.xml


if __name__ == "__main__":
    # download(cik_list_file=cik_list_file, output_path=output_path)
    # download_cik_submission_jsons('0000051143', 'output_data')
    # download_additional_submissions('./output_data/submissions/0000825316.json')
    # download_all_additional_submissions('./output_data/submissions')
    # download_files(output_path=output_path, document_type='excel')
    # download_files(output_path=output_path, document_type='xbrl')
    # build_url_list(input_path='input_data',
    #                document_type=document_type)
    # download_xbrl_files(output_path=output_path)
    download_all_report_files(
        input_path="input_data",
        arelle_command_path="./work/Arelle/arelleCmdLine.py",
    )
