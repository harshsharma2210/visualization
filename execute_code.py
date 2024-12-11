import openai
import altair as alt
import pandas as pd
import os
import ast
import webbrowser

def get_openai_api_key():
    """
    Retrieve OpenAI API key from environment or user input.
    
    Returns:
        str: OpenAI API key
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
    return api_key

def generate_chart_code(prompt):
    """
    Generate chart code using OpenAI's GPT model.
    
    Args:
        prompt (str): Description of the chart to generate
    
    Returns:
        str: Generated Python code for creating an Altair chart
    """
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=get_openai_api_key())
    
    # Prepare the full prompt with context
    full_prompt = f"""
    Generate complete, executable Python code using Altair to create a chart based on the following description:
    {prompt}
    
    Requirements:
    1. Use Altair (alt) for visualization
    2. Create a comprehensive DataFrame with realistic sample data
    3. Implement a complete chart with proper encoding and properties
    4. Include necessary imports (pandas, altair)
    5. Ensure the code can be directly executed
    6. Add meaningful chart properties like title, width, height
    
    Provide ONLY the Python code that includes:
    - Data generation
    - Chart creation
    - Chart display
    
    Example context for guidance:
    - If it's time series data, generate dates with reasonable values
    - If it's categorical data, create meaningful categories
    - Use appropriate chart types (bar, line, scatter) based on data
    """
    
    # Generate chart code
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in creating data visualizations and Altair charts."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0,
        max_tokens=2000
    )
    
    # Extract the generated code
    return response.choices[0].message.content.strip()

def execute_and_display_chart(chart_code):
    """
    Execute the generated Altair chart code and display the chart.
    
    Args:
        chart_code (str): Python code for creating an Altair chart
    
    Raises:
        Exception: If there's an error in code generation or execution
    """
    try:
        # Create a local namespace for executing the code
        local_namespace = {
            'alt': alt,
            'pd': pd
        }
        
        # Execute the generated code
        exec(chart_code, local_namespace)
        
        # Attempt to find and render the chart
        chart = local_namespace.get('chart')
        if chart:
            # Save the chart as an HTML file
            output_file = 'generated_chart.html'
            chart.save(output_file)
            print(f"Chart saved to {output_file}")
            
            # Attempt to open the chart in the default web browser
            webbrowser.open(output_file, new=2)
        else:
            print("No chart object found in the generated code.")
            
    except Exception as e:
        print(f"Error executing chart code: {e}")
        print("\nGenerated Code:")
        print(chart_code)

def main():
    """
    Main function to generate and display an Altair chart.
    """
    # Ensure OpenAI library is imported
    try:
        import openai
    except ImportError:
        print("OpenAI library not found. Please install it using:")
        print("pip install openai")
        return
    
    # Prompt for chart description
    chart_description = input("Enter a description for the chart you want to generate: ")
    
    try:
        # Generate Altair chart code
        chart_code = generate_chart_code(chart_description)
        
        # Execute and display the chart
        execute_and_display_chart(chart_code)
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

"""
Prerequisites:
1. Install required libraries:
   pip install openai altair pandas

2. Set up OpenAI API key:
   - Either set the OPENAI_API_KEY environment variable
   - Or input the key when prompted

3. Example usage:
   - Run the script
   - Enter a chart description like:
     "Create a bar chart showing sales by product category"
     "Generate a scatter plot of temperature vs. sales"
     "Visualize monthly revenue for a tech startup"
"""