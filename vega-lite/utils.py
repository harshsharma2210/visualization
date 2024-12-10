# utils.py
import os
import tempfile
import webbrowser
from copy import deepcopy
import json
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

    
def extract_visualization_parameters(assistant_reply):
    """
    Extracts the visualization parameters including chart_type and other encoding details.
    Derives 'chart_type' from the 'mark' property in the Vega-Lite spec.

    Args:
        assistant_reply (str): JSON string from the assistant containing 'spec' key.

    Returns:
        tuple: (chart_type (str), spec (dict))
    """
    try:
        data = json.loads(assistant_reply)
        spec = data.get("spec", {})
        
        # Derive chart_type from 'mark'
        mark = spec.get("mark", "")
        if isinstance(mark, dict):
            chart_type = mark.get("type", "").lower()
        elif isinstance(mark, str):
            chart_type = mark.lower()
        else:
            chart_type = ""
        
        return chart_type, spec
    except json.JSONDecodeError:
        print("Invalid JSON from assistant.")
        return None, {}
    except KeyError as ke:
        print(f"Missing key in assistant reply: {ke}")
        return None, {}
