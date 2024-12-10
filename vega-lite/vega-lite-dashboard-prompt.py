import pandas as pd
import openai
import json
import os
import regex as re
import time
from utils import get_openai_api_key

openai.api_key = get_openai_api_key()
model = "gpt-4o"
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

def get_base_prompt():
    base_prompt = (
        "Please provide the chart configuration in JSON format adhering to the following rules:\n"
        "- The x-axis and y-axis should not have titles, but grid lines must be present for both axes.\n"
        "- Ensure that the x-axis labels are tilted at an appropriate angle to prevent overlap.\n"
        "- Use Indian numbering conventions for the y-axis (e.g., lakhs, crores).\n"
        "- Include interactivity such as tooltips or other interactions.\n"
        "- Format the axes, legend, and grid lines to ensure readability and clarity.\n"
        "- The chart should be a line graph with point markers.\n"
        "- The legend should be positioned below the chart with no title.\n"       
    )
    return base_prompt

def send_message_to_openai(conversation, dataframe_info, column_info, data_sample):
    system_prompts = [
        {
            "role": "system",
            "content": (
                "You are a visualization assistant that generates Vega-Lite line chart specifications. "
                "Do not include any explanatory text in the output, only return the final Vega-Lite JSON specification."
            ),
        },
        {
            "role": "system",
            "content": (
                "Please respond **only** with the Vega-Lite JSON specification. Do **not** include any explanations, comments, or additional text. "
                "Ensure that the JSON is valid and properly formatted."
            ),
        },
        {
            "role": "system",
            "content": f"Here is a summary of the CSV data:\n{json.dumps(dataframe_info, indent=2)}",
        },
        {
            "role": "system",
            "content": f"Columns: {', '.join(column_info)}",
        },
        {
            "role": "system",
            "content": f"Here is a sample of the data:\n{json.dumps(data_sample, indent=2)}",
        },
        {
            "role": "system",
            "content": (
                "Do **not** include the 'data' field in your Vega-Lite specification. "
                "The data will be injected separately by the application."
            ),
        }
    ]

    messages = system_prompts + conversation

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=2000,
        )
        assistant_reply = response.choices[0].message.content
        return assistant_reply
    except Exception as e:
        raise ConnectionError(f"Error communicating with OpenAI: {e}")

def initialize_html(html_file='output-vega-lite-dashboard-prompt.html'):
    """Create the HTML file with necessary headers if it doesn't exist."""
    if not os.path.exists(html_file):
        with open(html_file, 'w') as f:
            f.write("""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Vega-Lite Visualizations dashboard-prompt</title>
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
                <h1>Vega-Lite Visualizations dashboard-prompt</h1>
            </body>
            </html>
        """)

def append_json_to_html(json_data, data, html_file='output-vega-lite-dashboard-prompt.html'):
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

def get_new_json_structure(base_prompt, api_key, model="gpt-4"):
    """Send the base prompt to OpenAI to get a new JSON structure."""
    system_prompt = {
        "role": "system",
        "content": (
            "You are a visualization assistant that generates Vega-Lite specifications based on provided configurations. "
            "Do not include any explanatory text in the output, only return the final Vega-Lite JSON specification."
        ),
    }

    user_prompt = {
        "role": "user",
        "content": base_prompt,
    }

    messages = [system_prompt, user_prompt]

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=2000,
        )
        assistant_reply = response.choices[0].message.content
        return assistant_reply
    except Exception as e:
        raise ConnectionError(f"Error communicating with OpenAI for base prompt: {e}")

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
                conversation, description, columns, data_sample
            )
        except ConnectionError as ce:
            print(ce)
            continue
        extracted_json = extract_json(assistant_reply)
        if extracted_json:
            try:
                vega_lite_json = json.loads(extracted_json)
                print("\n--- Vega-Lite JSON ---")
                print(json.dumps(vega_lite_json, indent=2))
                
                # Append the JSON to the HTML file with embedded data
                append_json_to_html(vega_lite_json, data_as_json)

                conversation.append(
                    {"role": "assistant", "content": json.dumps(vega_lite_json)}
                )
                print(f"\nVisualization appended to 'output-vega-lite-dashboard-prompt.html'.")
            except json.JSONDecodeError:
                print("\nAssistant provided invalid JSON:")
                print(extracted_json)
                conversation.append({"role": "assistant", "content": extracted_json})
        else:
            print("\nAssistant:")
            print(assistant_reply)
            conversation.append({"role": "assistant", "content": assistant_reply})

        print("\n--- Generating refined JSON structure based on base prompt ---")
        try:
            base_prompt = get_base_prompt()
            new_json_reply = get_new_json_structure(base_prompt, api_key)
            extracted_new_json = extract_json(new_json_reply)
            if extracted_new_json:
                try:
                    new_vega_lite_json = json.loads(extracted_new_json)
                    print("\n--- Refined Vega-Lite JSON ---")
                    print(json.dumps(new_vega_lite_json, indent=2))
                    
                    # Append the refined JSON to the HTML file with embedded data
                    append_json_to_html(new_vega_lite_json, data_as_json)

                    conversation.append(
                        {"role": "assistant", "content": json.dumps(new_vega_lite_json)}
                    )
                    print(f"\nRefined visualization appended to 'output-vega-lite-dashboard-prompt.html'.")
                except json.JSONDecodeError:
                    print("\nAssistant provided invalid JSON for refined structure:")
                    print(extracted_new_json)
                    conversation.append({"role": "assistant", "content": extracted_new_json})
            else:
                print("\nAssistant did not provide a valid JSON for refined structure.")
                conversation.append({"role": "assistant", "content": new_json_reply})
        except ConnectionError as ce:
            print(ce)

        print("\n")

    print("\nAll visualizations have been saved to 'output-vega-lite-dashboard-prompt.html'.")

if __name__ == "__main__":
    main()