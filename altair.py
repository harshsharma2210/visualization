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


def extract_customization_details(user_prompt):
    """
    Extract customization details for the chart based on the user's description.
    This focuses solely on customization aspects like color, interactivity, etc.
    """
    client = openai.OpenAI(api_key=get_openai_api_key())

    system_prompt = """
    You are an expert in data visualization customization. A user will describe how they would like to customize a chart.
    Based on the user's description, extract the following customization details:
    1. Color preferences
    2. Desired interactivity options (e.g., tooltips, zoom, etc.)
    3. Axis or label adjustments (e.g., renaming axis labels, adjusting scale, etc.)
    4. Any other specific visual preferences (e.g., font size, title, etc.)
    
    Output a JSON structure with all the customization details. For example:
    {
        "color": "red",
        "interactive": true,
        "x_axis_label": "Category",
        "y_axis_label": "Value",
        "title": "Sales by Category"
    }
    """

    try:
        conversation_history.append(
            {"role": "system", "content": system_prompt}
        )  # Add system prompt to the conversation history
        conversation_history.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversation_history,
            temperature=0.3,
            max_tokens=1000,
        )

        gpt_recommendation = response.choices[0].message.content
        json_match = re.search(
            r"```json\s*({.*?})\s*```", gpt_recommendation, re.DOTALL
        )
        if json_match:
            customization_details = json.loads(json_match.group(1))
        else:
            customization_details = json.loads(
                re.search(r"\{.*\}", gpt_recommendation, re.DOTALL).group(0)
            )

        conversation_history.append(
            {"role": "assistant", "content": gpt_recommendation}
        )

        return customization_details

    except Exception as e:
        print(f"Error extracting customizations: {e}")
        return {}


def analyze_data_and_create_chart(df, user_prompt):
    """
    Analyze the data and generate a chart type recommendation based on the dataset and the user's goal.
    This will focus on the best chart type selection, columns to plot, etc.
    """
    client = openai.OpenAI(api_key=get_openai_api_key())

    columns = list(df.columns)
    data_preview = df.head().to_string()
    data_info = df.dtypes.to_string()

    system_prompt = """
    You are an expert in data visualization. Given a dataset and a user's goal, analyze the dataset and recommend
    the most appropriate chart type and how to visualize it. Consider:
    1. Chart type options include Bar Chart, Line Chart, Pie Chart, etc.
    2. Which columns should be used for the x and y axes?
    3. Any data transformations needed (e.g., aggregations like sum, mean, etc.)?
    4. Provide a rationale for your choice.

    Output a JSON with the following details:
    {
        "chart_type": "bar/line/pie",
        "x_column": "column_name",
        "y_column": "column_name",
        "transformations": {...},
        "rationale": "Explanation of the chart choice"
    }
    """

    user_prompt_with_data = f"""
    Dataset Details:
    Columns: {columns}
    Data Preview:
    {data_preview}
    
    Column Types:
    {data_info}

    User Context/Goal: {user_prompt}

    Provide a detailed recommendation on the most appropriate chart and any necessary transformations.
    """

    try:
        conversation_history.append(
            {"role": "system", "content": system_prompt}
        )  # Add system prompt to the conversation history
        conversation_history.append({"role": "user", "content": user_prompt_with_data})

        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversation_history,
            temperature=0.2,
            max_tokens=1000,
        )

        gpt_recommendation = response.choices[0].message.content
        json_match = re.search(
            r"```json\s*({.*?})\s*```", gpt_recommendation, re.DOTALL
        )
        if json_match:
            recommendation = json.loads(json_match.group(1))
        else:
            recommendation = json.loads(
                re.search(r"\{.*\}", gpt_recommendation, re.DOTALL).group(0)
            )

        conversation_history.append(
            {"role": "assistant", "content": gpt_recommendation}
        )

        return recommendation

    except Exception as e:
        print(f"Error in chart generation: {e}")
        return None


def apply_customizations_and_create_chart(df, recommendation, customizations):
    """
    Apply the customizations to the generated chart.
    """
    # Default title generation if not provided by user
    title = customizations.get(
        "title", f'{recommendation["y_column"]} by {recommendation["x_column"]}'
    )

    # If title is still missing, we can let GPT provide it based on the data and recommendation
    if not title:
        title = f"{recommendation['chart_type'].capitalize()} Chart: {recommendation['y_column']} vs {recommendation['x_column']}"

    chart_properties = {
        "title": title,
        "color": customizations.get("color", None),
        "interactive": customizations.get("interactive", True),
        "x_axis_label": customizations.get("x_axis_label", recommendation["x_column"]),
        "y_axis_label": customizations.get("y_axis_label", recommendation["y_column"]),
    }

    chart_type = recommendation["chart_type"]
    x_column = recommendation["x_column"]
    y_column = recommendation["y_column"]

    # Create the chart based on the recommendation and customizations
    if chart_type == "bar":
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(f"{x_column}:N", title=chart_properties["x_axis_label"]),
                y=alt.Y(f"{y_column}:Q", title=chart_properties["y_axis_label"]),
                tooltip=[x_column, y_column],
            )
            .properties(title=chart_properties["title"])
            .interactive()
            if chart_properties["interactive"]
            else alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(f"{x_column}:N", title=chart_properties["x_axis_label"]),
                y=alt.Y(f"{y_column}:Q", title=chart_properties["y_axis_label"]),
                tooltip=[x_column, y_column],
            )
        )

        if chart_properties["color"]:
            chart = chart.encode(color=alt.Color(f'{chart_properties["color"]}:N'))

    elif chart_type == "line":
        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X(f"{x_column}:T", title=chart_properties["x_axis_label"]),
                y=alt.Y(f"{y_column}:Q", title=chart_properties["y_axis_label"]),
                tooltip=[x_column, y_column],
            )
            .properties(title=chart_properties["title"])
            .interactive()
            if chart_properties["interactive"]
            else alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X(f"{x_column}:T", title=chart_properties["x_axis_label"]),
                y=alt.Y(f"{y_column}:Q", title=chart_properties["y_axis_label"]),
                tooltip=[x_column, y_column],
            )
        )

        if chart_properties["color"]:
            chart = chart.encode(color=alt.Color(f'{chart_properties["color"]}:N'))

    elif chart_type == "pie":
        chart = (
            alt.Chart(df)
            .mark_arc()
            .encode(
                theta=alt.Theta(
                    f"{y_column}:Q", title=chart_properties["y_axis_label"]
                ),
                color=alt.Color(
                    f"{x_column}:N", title=chart_properties["x_axis_label"]
                ),
                tooltip=[x_column, y_column],
            )
            .properties(title=chart_properties["title"])
            .interactive()
            if chart_properties["interactive"]
            else alt.Chart(df)
            .mark_arc()
            .encode(
                theta=alt.Theta(
                    f"{y_column}:Q", title=chart_properties["y_axis_label"]
                ),
                color=alt.Color(
                    f"{x_column}:N", title=chart_properties["x_axis_label"]
                ),
                tooltip=[x_column, y_column],
            )
        )

    else:
        print(f"Unsupported chart type: {chart_type}")
        return None

    return chart


def main():
    print("Intelligent CSV Chart Generator")
    while True:
        data_source_choice = input(
            "Do you want to upload a CSV file (1) or enter a URL to fetch CSV data (2)? Enter 1 or 2: anything else to exit"
        ).strip()

        if data_source_choice == "1":
            csv_path = input("Enter the path to your CSV file: ").strip()
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                print(f"Error reading the CSV file: {e}")
                return
        elif data_source_choice == "2":
            csv_url = input("Enter the URL of the CSV file: ").strip()
            try:
                df = pd.read_csv(csv_url)
            except Exception as e:
                print(f"Error fetching the CSV data from URL: {e}")
                return
        else:
            print("Invalid choice. Exiting.")
            return

        user_prompt = input(
            "Describe the insight or analysis you want from this data: "
        ).strip()

        customizations = extract_customization_details(user_prompt)
        recommendation = analyze_data_and_create_chart(df, user_prompt)

        if recommendation:
            chart = apply_customizations_and_create_chart(
                df, recommendation, customizations
            )
            if chart:
                display_chart(chart)

        while True:
            follow_up_prompt = (
                input("Would you like to modify the chart further? (yes/no): ")
                .strip()
                .lower()
            )
            if follow_up_prompt != "yes":
                break
            user_prompt = input("Please provide the modification details: ").strip()
            customizations = extract_customization_details(user_prompt)
            recommendation = analyze_data_and_create_chart(df, user_prompt)
            if recommendation:
                chart = apply_customizations_and_create_chart(
                    df, recommendation, customizations
                )
                if chart:
                    display_chart(chart)


if __name__ == "__main__":
    main()
