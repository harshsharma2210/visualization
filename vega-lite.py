import pandas as pd
import openai
import json
import os
from utils import get_openai_api_key
client = openai.OpenAI(api_key=get_openai_api_key())

def read_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

def infer_csv_structure(df):
    description = df.describe(include='all').to_dict()
    columns = df.columns.tolist()
    return description, columns

def send_message_to_openai(conversation, dataframe_info, column_info, api_key):
    openai.api_key = api_key
    system_prompts = [
        {
            "role": "system",
            "content": (
                "You are an assistant that generates Vega-Lite JSON schemas based on user requests and provided data."
            )
        },
        {
            "role": "system",
            "content": f"Here is a summary of the CSV data:\n{json.dumps(dataframe_info, indent=2)}"
        },
        {
            "role": "system",
            "content": f"Columns: {', '.join(column_info)}"
        }
    ]

    messages = system_prompts + conversation

    try:
        response =  client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        assistant_reply = response.choices[0].message.content
        return assistant_reply
    except Exception as e:
        raise ConnectionError(f"Error communicating with OpenAI: {e}")

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

    print("\nStart chatting with the assistant. Type 'exit' or 'quit' to end the session.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            print("Ending the chat. Goodbye!")
        if user_input:
            conversation.append({"role": "user", "content": user_input})
        try:
            assistant_reply = send_message_to_openai(conversation, description, columns, api_key)
        except ConnectionError as ce:
            print(ce)
            continue
        try:
            vega_lite_json = json.loads(assistant_reply)
            print("\nAssistant (Vega-Lite JSON Schema):")
            print(json.dumps(vega_lite_json, indent=2))
            # Append assistant reply to conversation history as JSON string
            conversation.append({"role": "assistant", "content": json.dumps(vega_lite_json)})
        except json.JSONDecodeError:
            # If not valid JSON, display as plain text
            print("\nAssistant:")
            print(assistant_reply)
            conversation.append({"role": "assistant", "content": assistant_reply})

        print("\n")  # Add space before next input

if __name__ == "__main__":
    main()
