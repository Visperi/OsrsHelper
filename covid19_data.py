"""
MIT License

Copyright (c) 2020 Visperi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# coding=utf-8

import pytz
import requests
import datetime
import json
from typing import Union

hs = {
    "cases": "https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData/v2",
    "hospitalised": "https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaHospitalData"
}
# A variable for easier scheduling etc. if requests are made in loops
previous_request = None


def localize_timestamp(utc_ts: Union[str, datetime.datetime], new_tz: str,
                       utc_ts_datefmt: str = "%Y-%m-%dT%H:%M:%S.%fZ", new_datefmt: str = None) \
        -> Union[str, datetime.datetime]:
    """
    Localize and format an UTC timestamp.

    :param utc_ts: Original UTC timestamp. This can be either a string or a datetime object
    :param new_tz: Timezone where the timestamp should be localized to
    :param utc_ts_datefmt: Original UTC timestamp datetime format. Defaulted in ISO 8601 format.
    :param new_datefmt: Format of the localized timestamp. Defaulted in None when datetime object is returned instead
    :return: Localized timestamp as a datetime object or string
    """
    utc_tz = pytz.utc
    new_tz = pytz.timezone(new_tz)

    try:
        utc_ts = datetime.datetime.strptime(utc_ts, utc_ts_datefmt)
    except TypeError:
        # Timestamp should be in datetime.datetime format if TypeError is raised
        pass

    localized = utc_tz.localize(utc_ts).astimezone(new_tz)

    if new_datefmt:
        localized = localized.strftime(new_datefmt)

    return localized


def get_updated_data(source_dict: dict, timeout: int = 5, safe_mode: bool = True, output_file: str = None,
                     ensure_ascii: bool = False, **dump_kwargs) -> dict:
    """
    Get latest data from given APIs. Supports sources that respond in JSON format.

    :param source_dict: Dictionary containing all data sources in format {'source name': 'url'}
    :param timeout: An integer telling when a hanging request should be timeouted. Defaulted in 5 seconds.
    :param safe_mode: Boolean telling if requests should be made in safe mode. If safe mode is on (default) and a
                      response fails, exceptions are raised instead of saving exceptions into a dictionary. This
                      guarantees that no file modifications are made and may make it easier to handle bad responses.
    :param output_file: File path where response JSON data should be saved. Defaulted in None and data is not saved.
    :param ensure_ascii: Boolean that defines if non-ascii characters are allowed. Defaulted in False.
    :param dump_kwargs: Additional json.dump() keyword arguments
    :return: Dictionary containing response data in format {'source name': response dict}. Real data is not guaranteed
             if safe mode is False.
    """
    updated_data = {}
    
    for source_name in source_dict.keys():
        url = source_dict[source_name]
        try:
            resp = requests.get(url, timeout=timeout)
        except requests.exceptions.ReadTimeout as timeout_error:
            if safe_mode:
                raise timeout_error

            print(f"ReadTimeout: Data source {source_name} answered too slowly.")
            updated_data[source_name] = "ReadTimeout"
            continue

        resp_data = json.loads(resp.text)
        if not resp.ok:
            if safe_mode:
                raise RuntimeError(f"Data source {source_name} answered with status code {resp.status_code} while safe "
                                   f"mode was turned on.")

            print(f"Response not OK: Data source {source_name} answered with status code {resp.status_code}")
            updated_data[source_name] = f"Error {resp.status_code}: {resp_data}"
            continue

        for key in resp_data.keys():
            updated_data[key] = resp_data[key]

    if output_file:
        with open(output_file, "w") as ofile:
            json.dump(updated_data, ofile, ensure_ascii=ensure_ascii, **dump_kwargs)

    return updated_data


def read_datafile(filepath: str) -> dict:
    """
    Read a data file into a dictionary.

    :param filepath: Path to the data file
    :return: Dictionary containing the file data
    """
    with open(filepath, "r") as data_file:
        data = json.load(data_file)
    return data


def get_latest_cases(datadict: dict, datefmt: str = "%Y-%m-%dT%H:%M:%S.%fZ", hospitalised_area: str = "Finland",
                     localize_to: str = None, localized_datefmt: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> dict:
    """
    Get the latest cases in given dictionary. Supports dictionaries in format {'case type': [{case}, {case1}, ...]}.
    The cases in list must have a field 'date'. Hospitalised data cases must have a field 'area'

    :param datadict: Dictionary containing all data where latest cases are parsed
    :param datefmt: A string representing the datetime format of saved data. Defaulted to ISO 8601.
    :param hospitalised_area: String of a specific area where latest hospitalised data is taken. Defaulted into Finland
    :param localize_to: Timezone where UTC dates should be localized. Defaulted to None and no localization is made.
    :param localized_datefmt: A string representing a datetime format for localized date. Defauletd to ISO 8601.
    :return: Dictionary of latest cases for every case type
    """
    return_dict = {}

    for case_type in datadict.keys():
        if case_type == "hospitalised":
            cases = [case for case in datadict[case_type] if case["area"] == hospitalised_area]
        else:
            cases = datadict[case_type]

        # Find the latest case by taking the case with biggest timestamp
        latest_case = max(cases, key=lambda case: datetime.datetime.strptime(case["date"], datefmt))
        return_dict[case_type] = latest_case

    if localize_to:
        for case_type in return_dict.keys():
            localized = localize_timestamp(return_dict[case_type]["date"], localize_to, new_datefmt=localized_datefmt)
            return_dict[case_type]["date"] = localized

    return return_dict


def get_daily_cases(datadict: dict, localize_to: str = None) -> dict:
    """
    Get all daily cases by comparing their timestamps to current date. Localization can be made to get more accurate
    results.

    :param datadict: Dictionary containing all data where daily cases are parsed
    :param localize_to: Timezone where UTC timestamps are localized before comparison. Defaulted to None and no
                        localization is made.
    :return: Dictionary containing all daily cases in format {'case type': [{case}, {case1}, ...]}
    """
    daily_cases = {}

    utc_now = datetime.datetime.utcnow()

    for case_type in datadict.keys():
        cases = []

        for case_dict in datadict[case_type]:

            if localize_to:
                case_ts = localize_timestamp(case_dict["date"], localize_to)
                ts_now = localize_timestamp(utc_now, localize_to)
            else:
                case_ts = datetime.datetime.strptime(case_dict["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
                ts_now = utc_now

            # Confirmed infections are now recorded retroactively by THL, so cases recorded for "yesterday" can
            # basically be considered as "today" new cases
            if (case_ts.date() == ts_now.date() or
                    (case_type == "confirmed" and (ts_now.date() - case_ts.date()).days == 1)):
                cases.append(case_dict)

        daily_cases[case_type] = cases

    return daily_cases
