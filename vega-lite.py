import openai
import pandas as pd
import json
import re
from utils import get_openai_api_key
import os

client = openai.OpenAI(api_key=get_openai_api_key())


def analyze_data_and_create_chart(df, user_prompt=None):
    """
    Generate a Vega-Lite JSON specification based on the dataset and the user's goal.
    If user_prompt is None or empty, the LLM decides the best visualization.
    """
    columns = list(df.columns)
    data_types = df.dtypes.apply(lambda x: str(x)).to_dict()

    system_prompt = """
    You are a data visualization expert. Given the user's description (if any) and the dataset information, generate a Vega-Lite JSON specification that creates the desired chart.

    Instructions:
    - Only output the Vega-Lite JSON specification.
    - Do not include any explanations or additional text.
    - Assume the data is provided externally; do not include data in the specification.
    - Use "data": {"name": "myData"} in the specification.
    """

    if user_prompt:
        user_description = f"User Description:\n{user_prompt}"
    else:
        user_description = "User Description:\nNo specific description provided. Please analyze the dataset and suggest an appropriate visualization."

    user_prompt_with_data = f"""
    Dataset Information:
    - Columns: {columns}
    - Data Types: {data_types}

    {user_description}

    Remember:
    - Only output the Vega-Lite JSON specification.
    - Do not include the actual data in the 'data' field; use "data": {{"name": "myData"}} instead.
    """

    try:
        # Prepare the messages for the LLM
        chart_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_with_data},
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=chart_history,
            temperature=0.0,
            max_tokens=2500,
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

        return vega_lite_spec

    except Exception as e:
        print(f"Error in chart generation: {e}")
        return None


def main():
    print("Intelligent CSV Vega-Lite Spec Generator")
    while True:
        data_source_choice = input(
            "Do you want to upload a CSV file (1) or enter a URL to fetch CSV data (2)? Enter 1 or 2: anything else to exit "
        ).strip()

        if data_source_choice == "1":
            csv_path = input("Enter the path to your CSV file: ").strip()
            if not os.path.isfile(csv_path):
                print(f"File '{csv_path}' does not exist. Please try again.")
                continue
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
            "Describe the insight or analysis you want from this data (press Enter to skip): "
        ).strip()

        vega_lite_spec = analyze_data_and_create_chart(
            df, user_prompt if user_prompt else None
        )

        if vega_lite_spec:
            print("\nGenerated Vega-Lite Specification:")
            print(json.dumps(vega_lite_spec, indent=4))
        else:
            print("Failed to generate Vega-Lite specification.")

        continue_choice = (
            input(
                "Would you like to create another Vega-Lite specification? (yes/no): "
            )
            .strip()
            .lower()
        )
        if continue_choice != "yes":
            print("Exiting the Intelligent CSV Vega-Lite Spec Generator.")
            break


if __name__ == "__main__":
    main()
