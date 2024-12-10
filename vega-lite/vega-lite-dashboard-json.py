import pandas as pd
import openai
import json
import os
import regex as re
import time
from utils import get_openai_api_key
from templates import line_chart_template, bar_chart_template, pie_chart_template
openai.api_key = get_openai_api_key()
def select_template(chart_type):
    templates = {
        "line": line_chart_template,
        "bar": bar_chart_template,
        "pie": pie_chart_template
    }
    return templates.get(chart_type)

def extract_visualization_parameters(assistant_reply):
    try:
        data = json.loads(assistant_reply)
        chart_type = data.get("chart_type", "").lower()
        spec = data.get("spec", {})
        return chart_type, spec
    except json.JSONDecodeError:
        print("Invalid JSON from assistant.")
        return None, {}
    except KeyError as ke:
        print(f"Missing key in assistant reply: {ke}")
        return None, {}


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


def send_message_to_openai(conversation, dataframe_info, column_info, data_sample, api_key):
    system_prompts = [
        {
            "role": "system",
            "content": (
                "You are an assistant that generates Vega-Lite JSON specifications based on user requests and provided data."
                " Do **not** include the 'data' field with 'values' in your specifications."
                " Assume that the data will be provided externally by the application."
                " Focus solely on defining the visualization marks, encodings, and other specifications."
            ),
        },
        {
            "role": "system",
            "content": (
                "Please respond **only** with the Vega-Lite JSON specification. Do **not** include any explanations, comments, or additional text."
                " Ensure that the JSON is valid and properly formatted."
            ),
        },
        {
            "role": "system",
            "content": f"Here is a summary of the CSV data:\n{json.dumps(dataframe_info, indent=2)}",
        },
        {"role": "system", "content": f"Columns: {', '.join(column_info)}"},
        {
            "role": "system",
            "content": f"Here is a sample of the data:\n{json.dumps(data_sample, indent=2)}"
        },
        {
            "role": "system",
            "content": (
                "Do **not** include the 'data' field in your Vega-Lite specification."
                " The data will be injected separately by the application."
            ),
        },
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

def initialize_html(html_file='output-vega-lite-dashboard.html'):
    """Create the HTML file with necessary headers if it doesn't exist."""
    if not os.path.exists(html_file):
        with open(html_file, 'w') as f:
            f.write("""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Vega-Lite Visualizations Dashboard</title>
                <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
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
                <h1>Vega-Lite Visualizations Dashboard</h1>
            </body>
            </html>
        """)

def append_json_to_html(json_data, data, html_file='output-vega-lite-dashboard.html'):
    initialize_html(html_file)
    visualization_id = f"vis_{int(time.time() * 1000)}"
    json_data['data'] = {'values': data}
    visualization_html = f"""
    <div class="visualization">
        <div id="{visualization_id}"></div>
        <script>
            vegaEmbed("#{visualization_id}", {json.dumps(json_data, indent=2)}).then(function(result) {{

            }}).catch(console.error);
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

    openai.api_key = api_key

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

    # Convert the DataFrame to a list of records (JSON)
    data_as_json = df.to_dict(orient='records')
    data_sample = df.head(5).to_dict(orient='records')

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Ending the chat. Goodbye!")
            break
        if user_input:
            conversation.append({"role": "user", "content": user_input})
        try:
            assistant_reply = send_message_to_openai(
                conversation, description, columns, data_sample, api_key
            )
        except ConnectionError as ce:
            print(ce)
            continue
        extracted_json = extract_json(assistant_reply)
        if extracted_json:
            chart_type, spec = extract_visualization_parameters(extracted_json)
            if not chart_type:
                print("\nAssistant provided invalid or incomplete JSON.")
                conversation.append({"role": "assistant", "content": extracted_json})
                continue
            template = select_template(chart_type)
            if not template:
                print(f"\nUnrecognized chart type: '{chart_type}'. Please use 'line', 'bar', or 'pie'.")
                conversation.append({"role": "assistant", "content": extracted_json})
                continue
            try:
                # Make a deep copy of the template to avoid modifying the original
                merged_json = json.loads(json.dumps(template))
                # Merge the LLM-generated spec into the template
                merged_json = deep_merge_dicts(merged_json, spec)
                # Validate the merged JSON
                if not validate_vega_lite_json(merged_json):
                    print("Generated Vega-Lite JSON is invalid.")
                    continue
                print("\n--- Merged Vega-Lite JSON ---")
                print(json.dumps(merged_json, indent=2))
                # Append the JSON to the HTML file with embedded data
                append_json_to_html(merged_json, data_as_json)
                conversation.append({"role": "assistant", "content": json.dumps(merged_json)})
                print(f"\nVisualization appended to 'output-vega-lite-dashboard.html'.")
            except json.JSONDecodeError as jde:
                print("\nError processing the template JSON:")
                print(jde)
                conversation.append({"role": "assistant", "content": str(jde)})
            except Exception as e:
                print(f"\nAn error occurred during merging: {e}")
                conversation.append({"role": "assistant", "content": str(e)})
        else:
            print("\nAssistant:")
            print(assistant_reply)
            conversation.append({"role": "assistant", "content": assistant_reply})
        print("\n")

    print("\nAll visualizations have been saved to 'output-vega-lite-dashboard.html'.")

if __name__ == "__main__":
    main()
