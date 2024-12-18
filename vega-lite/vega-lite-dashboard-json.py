import pandas as pd
import openai
import json
import os
import regex as re
import time
import copy
from utils import (
    get_openai_api_key,
    deep_merge_dicts,
    read_csv,
    infer_csv_structure,
    extract_json,
    extract_chart_type
)
from templates import line_chart_template, bar_chart_template, pie_chart_template
openai.api_key = get_openai_api_key()


def select_template(chart_type):
    templates = {
        "line": line_chart_template, 
        "bar": bar_chart_template,    
        "arc": pie_chart_template    
    }
    return templates.get(chart_type)



def send_message_to_openai(conversation, dataframe_info, column_info, data_sample):
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
            "content": f"Here is a sample of the data:\n{json.dumps(data_sample, indent=2)}",
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


def initialize_html(html_file="output-vega-lite-dashboard.html"):
    """Create the HTML file with necessary headers if it doesn't exist."""
    if not os.path.exists(html_file):
        with open(html_file, "w") as f:
            f.write(
                """<!DOCTYPE html>
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
        """
            )


def append_json_to_html(json_data, data, html_file="output-vega-lite-dashboard.html"):
    initialize_html(html_file)
    visualization_id = f"vis_{int(time.time() * 1000)}"
    json_data["data"] = {"values": data}
    visualization_html = f"""
    <div class="visualization">
        <div id="{visualization_id}"></div>
        <script>
            vegaEmbed("#{visualization_id}", {json.dumps(json_data, indent=2)}).then(function(result) {{

            }}).catch(console.error);
        </script>
    </div>
    """
    with open(html_file, "r") as f:
        content = f.read()
    insertion_point = content.rfind("</body>")
    if insertion_point == -1:
        insertion_point = len(content)

    new_content = (
        content[:insertion_point] + visualization_html + content[insertion_point:]
    )
    with open(html_file, "w") as f:
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

    print("\nStart chatting with the assistant. Type 'exit' or 'quit' to end the session.\n")
    initialize_html()
    data_as_json = df.to_dict(orient="records")
    data_sample = df.head(5).to_dict(orient="records")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Ending the chat. Goodbye!")
            break
        if user_input:
            conversation.append({"role": "user", "content": user_input})
        try:
            assistant_reply = send_message_to_openai(
                conversation, description, columns, data_sample
            )
        except ConnectionError as ce:
            print(ce)
            continue
        extracted_json = extract_json(assistant_reply)
        if extracted_json and isinstance(extracted_json, str):
            extracted_json = json.loads(extracted_json)
        if extracted_json:
            chart_type = extract_chart_type(extracted_json)
            if not chart_type:
                print("\nAssistant provided invalid or incomplete JSON.")
                conversation.append({"role": "assistant", "content": json.dumps(extracted_json)})
                continue            
            template = select_template(chart_type)
            if not template:
                print(f"\nUnrecognized chart type: '{chart_type}'. Please use 'line', 'bar', or 'arc'.")
                conversation.append({"role": "assistant", "content": json.dumps(extracted_json)})
                continue
            try:
                template_copy = copy.deepcopy(template)
                template_copy = deep_merge_dicts(extracted_json, template_copy)
                print(json.dumps(template_copy, indent=2))
                append_json_to_html(template_copy, data_as_json)
                conversation.append({"role": "assistant", "content": json.dumps(template_copy)})
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
