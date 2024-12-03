# utils.py
import os
import tempfile
import webbrowser

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
  
def display_chart(chart):
    try:
        temp_html = tempfile.mktemp(".html")
        chart.save(temp_html)
        webbrowser.open(f"file://{temp_html}")
        print(f"Chart saved and opened in default browser: {temp_html}")
    except Exception as e:
        print(f"Failed to display chart: {e}")
