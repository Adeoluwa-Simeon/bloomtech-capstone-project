# Chrome Browser Testing Agent

## Overview

This project is a Chrome browser testing agent developed as a capstone project for the BloomTech AI training course. The agent automates web interactions, allowing for efficient testing of web applications. It utilizes the Langchain framework and Selenium to interact with web elements, making it a powerful tool for QA manual testing.

## Features

- **Element Extraction**: The agent can extract various elements from a web page, including links, buttons, inputs, and text, even from iframes.
- **Element Interaction**: Simulate user interactions such as clicking buttons, hovering over elements, and entering text into input fields.
- **Time Logging**: Logs the time taken for various operations, helping to identify performance bottlenecks.
- **JavaScript Execution**: Executes JavaScript to traverse the DOM and build a structured representation of the page elements.
- **Customizable Tools**: Easily extendable with additional tools for more complex interactions or testing scenarios.

## Setup Instructions

To set up the Chrome Browser Testing Agent, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   Make sure you have Python installed, then install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the root directory of the project and add the following environment variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   LANGCHAIN_API_KEY=your_langchain_api_key
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=your_project_name
   ```

4. **Run the Agent**:
   Execute the main script to start the testing agent:
   ```bash
   python main.py
   ```

## Environment Variables

The following environment variables need to be set in the `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key for accessing the language model.
- `LANGCHAIN_API_KEY`: Your Langchain API key for utilizing Langchain features.
- `LANGCHAIN_TRACING_V2`: Set to `true` to enable tracing.
- `LANGCHAIN_PROJECT`: The name of your Langchain project.

## Usage

Once the agent is running, you can interact with it through the console. The agent will prompt you for input, allowing you to specify the actions you want to perform on the web page.

## Additional Information

- Ensure you have the Chrome browser installed, as the agent uses the Chrome WebDriver for automation.
- You may need to download the appropriate version of the Chrome WebDriver that matches your installed Chrome version. Place the WebDriver executable in your system's PATH.

## Acknowledgments

Special thanks to BloomTech for providing the resources and support throughout the AI training course.