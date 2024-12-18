import pandas as pd
import openai
import json
import os
import regex as re
import time
from utils import get_openai_api_key

openai.api_key = get_openai_api_key()

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

def send_message_to_openai(conversation, dataframe_info, column_info, api_key):
    system_prompts = [
        {
            "role": "system",
            "content": (
                "You are an assistant that generates **valid** Chart.js configuration objects based on user requests and provided data. "
                "Ensure that all JSON syntax rules are followed, including quoting all keys with double quotes and avoiding any comments or placeholders. "
                "Populate all data fields with actual numerical values extracted from the provided dataset."
            ),
        },
        {
            "role": "system",
            "content": f"Here is a summary of the CSV data:\n{json.dumps(dataframe_info, indent=2)}",
        },
        {"role": "system", "content": f"Columns: {', '.join(column_info)}"},
    ]
    
    messages = system_prompts + conversation

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        assistant_reply = response.choices[0].message.content
        return assistant_reply
    except Exception as e:
        raise ConnectionError(f"Error communicating with OpenAI: {e}")

def initialize_html(html_file='output-chartjs.html'):
    """Create the HTML file with necessary headers if it doesn't exist."""
    if not os.path.exists(html_file):
        with open(html_file, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chart.js Visualizations</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .visualization {
            margin-bottom: 50px;
        }
    </style>
</head>
<body>
    <h1>Chart.js Visualizations</h1>
</body>
</html>
""")

def append_json_to_html(config_data, data, html_file='output-chartjs.html'):
    initialize_html(html_file)
    chart_id = f"chart_{int(time.time() * 1000)}"
    
    # Removed overwriting 'data' as config_data already contains necessary data
    # config_data['data'] = {
    #     'datasets': config_data.get('data', {}).get('datasets', []),
    #     'labels': data.get('labels', [])
    # }
    
    # Serialize the config data to JSON
    config_json = json.dumps(config_data, indent=2)
    
    # Dynamically set the chart title if available
    chart_title = config_data.get('options', {}).get('plugins', {}).get('title', {}).get('text', 'Chart')
    
    visualization_html = f"""
    <div class="visualization">
        <h2>{chart_title}</h2>
        <canvas id="{chart_id}"></canvas>
        <script>
            const ctx_{chart_id} = document.getElementById('{chart_id}').getContext('2d');
            new Chart(ctx_{chart_id}, {config_json});
        </script>
    </div>
    """
    with open(html_file, 'r') as f:
        content = f.read()
    insertion_point = content.rfind('</body>')
    if insertion_point == -1:
        insertion_point = len(content)

    new_content = content[:insertion_point] + visualization_html + content[insertion_point:]
    with open(html_file, 'w') as f:
        f.write(new_content)

def main():
    try:
        api_key = get_openai_api_key()
    except ValueError as ve:
        print(ve)
        return
    csv_path = input("Enter the path to your CSV file: ").strip()
    try:
        df = read_csv(csv_path)
        print("\nCSV file successfully uploaded and read!")
    except ValueError as ve:
        print(ve)
        return
    description, columns = infer_csv_structure(df)
    print("\n--- DataFrame Summary ---")
    print(pd.DataFrame(description).transpose())
    conversation = []

    print(
        "\nStart chatting with the assistant. Type 'exit' or 'quit' to end the session.\n"
    )
    initialize_html()
    data_as_json = df.to_dict(orient='records')

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Ending the chat. Goodbye!")
            break
        if user_input:
            conversation.append({"role": "user", "content": user_input})
        try:
            assistant_reply = send_message_to_openai(
                conversation, description, columns, api_key
            )
        except ConnectionError as ce:
            print(ce)
            continue
        extracted_json = extract_json(assistant_reply)
        if extracted_json:
            try:
                chartjs_config = json.loads(extracted_json)
                print("\n--- Chart.js Configuration ---")
                print(json.dumps(chartjs_config, indent=2))
                
                # Append the JSON to the HTML file with embedded data
                append_json_to_html(chartjs_config, data_as_json)

                conversation.append(
                    {"role": "assistant", "content": json.dumps(chartjs_config)}
                )
                print(f"\nVisualization appended to 'output-chartjs.html'.")
            except json.JSONDecodeError:
                print("\nAssistant provided invalid JSON:")
                print(extracted_json)
                conversation.append({"role": "assistant", "content": extracted_json})
        else:
            print("\nAssistant:")
            print(assistant_reply)
            conversation.append({"role": "assistant", "content": assistant_reply})
        print("\n")

    print("\nAll visualizations have been saved to 'output-chartjs.html'.")

if __name__ == "__main__":
    main()
