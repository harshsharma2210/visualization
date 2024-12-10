# utils.py
import os
import tempfile
import webbrowser
from copy import deepcopy
import pandas as pd
import os
import regex as re
def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and os.path.exists(".env"):
        with open(".env", "r") as env_file:
            for line in env_file:
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        print("OpenAI API Key not found in environment variables or .env file.")
        api_key = input("Please enter your OpenAI API Key: ").strip()
        save_choice = input(
            "Would you like to save this API key for future sessions? (yes/no): "
        ).lower()
        if save_choice == "yes":
            with open(".env", "w") as env_file:
                env_file.write(f"OPENAI_API_KEY={api_key}")
            print("API key saved to .env file.")
    return api_key
  
def display_chart(chart):
    try:
        temp_html = tempfile.mktemp(".html")
        chart.save(temp_html)
        webbrowser.open(f"file://{temp_html}")
        print(f"Chart saved and opened in default browser: {temp_html}")
    except Exception as e:
        print(f"Failed to display chart: {e}")


def deep_merge_dicts(dict1, dict2):
    merged = deepcopy(dict1)
    for key, value in dict2.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def read_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

def infer_csv_structure(df):
    description = df.describe(include="all").to_dict()
    columns = df.columns.tolist()
    return description, columns

def extract_json(text):
    json_pattern = re.compile(r"\{(?:[^{}]|(?0))*\}")
    match = json_pattern.search(text)
    if match:
        return match.group()
    return None

def extract_chart_type(vega_lite_schema):
    mark = vega_lite_schema.get("mark")
    if mark is None:
        return None
    if isinstance(mark, dict):
        return mark.get("type")
    if isinstance(mark, str):
        return mark
    return None