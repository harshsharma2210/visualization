import openai
import altair as alt
import pandas as pd
import json
import re
import os
import tempfile
import webbrowser

conversation_history = []


def get_openai_api_key():
    """
    Retrieve the OpenAI API key from environment variables or a .env file.
    If not found, prompt the user to enter it and optionally save it to .env.
    """
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
    """
    Save the chart as an HTML file and open it in the default web browser.
    """
    try:
        temp_html = tempfile.mktemp(".html")
        chart.save(temp_html)
        webbrowser.open(f"file://{temp_html}")
        print(f"Chart saved and opened in default browser: {temp_html}")
    except Exception as e:
        print(f"Failed to display chart: {e}")


def extract_customization_details(user_prompt):
    """
    Extract customization details for the chart based on the user's description.
    This focuses solely on customization aspects like color, interactivity, etc.
    """
    openai.api_key = get_openai_api_key()

    system_prompt = """
You are an expert in chart customization. Extract any customization details from the user's description.

Output a JSON object with any of the following keys if they are specified:
- "title": The title of the chart.
- "color": The color to use in the chart.
- "x_axis_label": Label for the x-axis.
- "y_axis_label": Label for the y-axis.
- "interactive": true or false.

Only output the JSON object with the relevant keys.
"""

    try:
        conversation_history.append({"role": "system", "content": system_prompt})
        conversation_history.append({"role": "user", "content": user_prompt})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation_history,
            temperature=0.0,
            max_tokens=500,
        )

        # Get the assistant's reply
        gpt_reply = response.choices[0].message.content.strip()

        # Extract the JSON part from the assistant's reply
        json_match = re.search(r"\{.*\}", gpt_reply, re.DOTALL)
        if json_match:
            customization_details_str = json_match.group(0)
            customization_details = json.loads(customization_details_str)
        else:
            customization_details = {}

        conversation_history.append({"role": "assistant", "content": gpt_reply})

        return customization_details

    except Exception as e:
        print(f"Error extracting customizations: {e}")
        return {}


def analyze_data_and_create_chart(df, user_prompt):
    """
    Generate a Vega-Lite JSON specification based on the dataset and the user's goal.
    """
    openai.api_key = get_openai_api_key()

    columns = list(df.columns)
    data_types = df.dtypes.apply(lambda x: str(x)).to_dict()

    system_prompt = """
You are a data visualization expert. Given the user's description and the dataset information, generate a Vega-Lite JSON specification that creates the desired chart.

Instructions:
- Only output the Vega-Lite JSON specification.
- Do not include any explanations or additional text.
- Assume the data is provided externally; do not include data in the specification.

Example Output:
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "description": "A simple bar chart with embedded data.",
  "data": {"name": "myData"},
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "value", "type": "quantitative"}
  }
}
"""

    user_prompt_with_data = f"""
Dataset Information:
- Columns: {columns}
- Data Types: {data_types}

User Description:
{user_prompt}

Remember:
- Only output the Vega-Lite JSON specification.
- Do not include the actual data in the 'data' field; use "data": {{"name": "myData"}} instead.
"""

    try:
        conversation_history.append({"role": "system", "content": system_prompt})
        conversation_history.append({"role": "user", "content": user_prompt_with_data})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation_history,
            temperature=0.0,
            max_tokens=1500,
        )

        # Get the assistant's reply
        gpt_reply = response.choices[0].message.content.strip()

        # Extract the JSON part from the assistant's reply
        json_match = re.search(r"\{.*\}", gpt_reply, re.DOTALL)
        if json_match:
            vega_lite_spec_str = json_match.group(0)
            vega_lite_spec = json.loads(vega_lite_spec_str)
        else:
            print("No valid JSON found in the LLM response.")
            return None

        conversation_history.append({"role": "assistant", "content": gpt_reply})

        return vega_lite_spec

    except Exception as e:
        print(f"Error in chart generation: {e}")
        return None


def apply_customizations_and_create_chart(df, vega_lite_spec, customizations):
    """
    Apply customizations to the Vega-Lite spec and create the chart.
    """
    # Apply customizations to the Vega-Lite spec
    if customizations:
        if "title" in customizations:
            vega_lite_spec["title"] = customizations["title"]
        if "x_axis_label" in customizations and "encoding" in vega_lite_spec:
            if "x" in vega_lite_spec["encoding"]:
                vega_lite_spec["encoding"]["x"]["title"] = customizations["x_axis_label"]
        if "y_axis_label" in customizations and "encoding" in vega_lite_spec:
            if "y" in vega_lite_spec["encoding"]:
                vega_lite_spec["encoding"]["y"]["title"] = customizations["y_axis_label"]
        if "color" in customizations:
            # Depending on the chart type, color encoding might differ
            # Here, we assume that color is mapped to a specific field or set directly
            if "encoding" in vega_lite_spec and "color" in vega_lite_spec["encoding"]:
                vega_lite_spec["encoding"]["color"] = {
                    "value": customizations["color"]
                }
            else:
                # If no color encoding exists, add a mark color
                if "mark" in vega_lite_spec:
                    if isinstance(vega_lite_spec["mark"], dict):
                        vega_lite_spec["mark"]["color"] = customizations["color"]
                    else:
                        vega_lite_spec["mark"] = {"type": vega_lite_spec["mark"], "color": customizations["color"]}
        if "interactive" in customizations:
            if not customizations["interactive"]:
                vega_lite_spec.pop("selection", None)
                if "config" not in vega_lite_spec:
                    vega_lite_spec["config"] = {}
                vega_lite_spec["config"]["view"] = {"continuousWidth": 500, "continuousHeight": 300}

    # Add the data to the spec
    vega_lite_spec["data"] = {"values": df.to_dict(orient='records')}

    try:
        # Create the chart using Altair
        chart = alt.Chart.from_dict(vega_lite_spec)

        # Handle interactivity if specified
        if customizations.get("interactive", True):
            chart = chart.interactive()

        return chart

    except Exception as e:
        print(f"Error creating chart from Vega-Lite spec: {e}")
        return None


def main():
    print("Intelligent CSV Chart Generator")
    while True:
        data_source_choice = input(
            "Do you want to upload a CSV file (1) or enter a URL to fetch CSV data (2)? Enter 1 or 2: anything else to exit "
        ).strip()

        if data_source_choice == "1":
            csv_path = input("Enter the path to your CSV file: ").strip()
            try:
                df = pd.read_csv(csv_path)
                print(f"CSV file '{csv_path}' loaded successfully.")
            except Exception as e:
                print(f"Error reading the CSV file: {e}")
                continue
        elif data_source_choice == "2":
            csv_url = input("Enter the URL of the CSV file: ").strip()
            try:
                df = pd.read_csv(csv_url)
                print(f"CSV data from '{csv_url}' fetched successfully.")
            except Exception as e:
                print(f"Error fetching the CSV data from URL: {e}")
                continue
        else:
            print("Invalid choice. Exiting.")
            return

        user_prompt = input(
            "Describe the insight or analysis you want from this data: "
        ).strip()

        if not user_prompt:
            print("No description provided. Exiting.")
            return

        # Extract customizations based on user prompt
        customizations = extract_customization_details(user_prompt)

        # Generate Vega-Lite specification based on data and user prompt
        vega_lite_spec = analyze_data_and_create_chart(df, user_prompt)

        if vega_lite_spec:
            # Create chart with customizations
            chart = apply_customizations_and_create_chart(
                df, vega_lite_spec, customizations
            )
            if chart:
                display_chart(chart)
            else:
                print("Failed to create the chart.")
        else:
            print("Failed to generate Vega-Lite specification.")

        while True:
            follow_up_prompt = (
                input("Would you like to modify the chart further? (yes/no): ")
                .strip()
                .lower()
            )
            if follow_up_prompt != "yes":
                break
            user_prompt = input("Please provide the modification details: ").strip()
            if not user_prompt:
                print("No modification details provided.")
                break
            customizations = extract_customization_details(user_prompt)
            vega_lite_spec = analyze_data_and_create_chart(df, user_prompt)
            if vega_lite_spec:
                chart = apply_customizations_and_create_chart(
                    df, vega_lite_spec, customizations
                )
                if chart:
                    display_chart(chart)
                else:
                    print("Failed to create the modified chart.")
            else:
                print("Failed to generate Vega-Lite specification for modifications.")


if __name__ == "__main__":
    main()
