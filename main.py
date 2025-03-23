import time
import os

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_community.tools.shell.tool import ShellTool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")


driver = webdriver.Chrome()

element_dict = {}

def switch_to_iframe(iframe_index: int = 0) -> None:
    """Switches to the iframe based on the provided index (defaults to 0 for the first iframe)."""
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    if len(iframes) > iframe_index:
        driver.switch_to.frame(iframes[iframe_index])

def switch_to_default_content() -> None:
    """Switches back to the main document from the iframe."""
    driver.switch_to.default_content()


def extract_elements_from_frame(context: webdriver.Chrome, frame_id: int = -1) -> tuple:
    """Extracts visible elements using fast JavaScript traversal but retains Selenium elements in element_dict."""

    js_script = """
    function buildElementTree(element) {
        if (element.getBoundingClientRect().width === 0 && element.getBoundingClientRect().height === 0) {
            return null; // Skip elements with no visible size
        }

        let tag = element.tagName.toLowerCase();
        let className = element.className || "";
        let children = [];
        let xpath = generateXPath(element);

        let elementId = tag + "-" + Math.random().toString(36).substr(2, 9); // Unique ID
        let elementStructure = {
            id: elementId,
            type: ["div", "section", "article", "form", "img"].includes(tag) ? "container" : tag,
            class: className,
            xpath: xpath
        };

        if (tag === "a") {
            elementStructure.text = element.innerText.trim();
            elementStructure.url = element.href;
        } else if (tag === "button") {
            elementStructure.text = element.innerText.trim();
            elementStructure.button_type = element.type || "button";
        } else if (tag === "input") {
            elementStructure.name = element.name || "Unnamed";
            elementStructure.input_type = element.type || "text";
            elementStructure.input_value = element.value || "";
        } else if (tag === "textarea") {
            elementStructure.text = element.value || element.innerText.trim();
        } else if (["p", "span", "h1", "h2", "h3", "h4", "h5", "h6"].includes(tag)) {
            let content = element.innerText.trim();
            if (!content) return null;
            elementStructure.content = content;
        }

        // Process children
        let childElements = element.children;
        for (let i = 0; i < childElements.length; i++) {
            let childStructure = buildElementTree(childElements[i]);
            if (childStructure) {
                children.push(childStructure);
            }
        }

        elementStructure.children = children; // Assign children if not empty
        // If the current element is a container and only contains other containers, merge them
        if (elementStructure.type === "container") {
            if (children.length === 1 && children[0].type === "container") {
                elementStructure.class += " -> " + children[0].class;
                elementStructure.children = children[0].children; 
                elementStructure.xpath = children[0].xpath; 
            } else if (children.length === 0) {
                return null; // Remove empty containers
            }
        }


        return elementStructure;
    }

    function generateXPath(element) {
        if (element.id) return 'id("' + element.id + '")';
        if (element === document.body) return "/html/body";
        let ix = 0;
        let siblings = element.parentNode.children;
        for (let i = 0; i < siblings.length; i++) {
            if (siblings[i] === element) return generateXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            if (siblings[i].tagName === element.tagName) ix++;
        }
    }

    return buildElementTree(document.body);
    """

    # Execute JavaScript to get the structured elements
    element_structure = context.execute_script(js_script)
    
    def populate_element_dict(node):
        """Recursively find elements using Selenium and map them to element_dict."""
        if "xpath" in node:
            try:
                element_dict[node["id"]] = {'xpath': node["xpath"], 'frame_id': frame_id}
                del node["xpath"]
            except:
                pass  # Ignore if element is not found

        if "children" in node:
            for child in node["children"]:
                populate_element_dict(child)

    populate_element_dict(element_structure)
    return element_structure

@tool
def get_page_elements() -> dict:
    """Extracts various elements (links, buttons, inputs, and text) from the loaded web page,
    including handling iframes by switching to them and extracting their elements as well.

    Returns:
    dict: A hierarchical JSON structure containing all important elements.
    """
    # Reset element dictionary
    element_dict.clear()  # Clear the existing element dictionary

    # Extract elements from the main document
    root_structure = extract_elements_from_frame(driver)

    # Handle iframes: Switch to each iframe and extract elements from it
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for iframe_index, iframe in enumerate(iframes):
        driver.switch_to.frame(iframe)  # Switch to iframe

        # Extract elements inside the iframe
        iframe_structure = extract_elements_from_frame(driver, iframe_index)

        # Append iframe elements to the main document's structure
        if iframe_structure:
            root_structure["children"].append(iframe_structure)

        driver.switch_to.default_content()  # Switch back to the main document

    return root_structure

@tool
def click_element(key: str, iframe_index: int = -1) -> str:
    """Simulates clicking an element on the page based on the given key, handling iframes.
    
    Parameters:
    key (str): The key to locate the element.
    iframe_index (int): The index of the iframe to search for the element inside. Default is -1 for the main document.
    
    Returns:
    str: Success or error message.
    """
    try:

        # Locate and click the element using key
        xpath = element_dict[key]['xpath']
        iframe_index = element_dict[key]['frame_id']

        if iframe_index >= 0:
            switch_to_iframe(iframe_index)

        element = driver.find_element(By.XPATH, xpath)
        print(element)
        element.click()

        return "Element clicked successfully."
    
    except Exception as e:
        return f"Error clicking element: {e}"
    
    finally:
        if iframe_index >= 0:
            switch_to_default_content()

@tool
def hover_over_element(key: str, iframe_index: int = -1) -> str:
    """Simulates hovering over an element on the page based on the given key, handling iframes.
    
    Parameters:
    key (str): The key to locate the element.
    iframe_index (int): The index of the iframe to search for the element inside. Default is -1 for the main document.
    
    Returns:
    str: Success or error message.
    """
    try:
        xpath = element_dict[key]['xpath']
        iframe_index = element_dict[key]['frame_id']

        if iframe_index >= 0:
            switch_to_iframe(iframe_index)

        action = ActionChains(driver)
        
        # Locate and hover over the element using key
        element = driver.find_element(By.XPATH, xpath)
        action.move_to_element(element).perform()

        return "Hovered over element successfully."
    
    except Exception as e:
        return f"Error hovering over element: {e}"
    
    finally:
        if iframe_index >= 0:
            switch_to_default_content()

@tool
def enter_input(key: str, text: str, iframe_index: int = -1) -> str:
    """Simulates entering text into an input field on the page based on the given key, handling iframes.
    
    Parameters:
    key (str): The key to locate the input element.
    text (str): The text to be entered into the input field.
    iframe_index (int): The index of the iframe to search for the element inside. Default is -1 for the main document.
    
    Returns:
    str: Success or error message.
    """
    try:
        xpath = element_dict[key]['xpath']
        iframe_index = element_dict[key]['frame_id']

        if iframe_index >= 0:
            switch_to_iframe(iframe_index)

        # Locate the input element using key and enter text
        element = driver.find_element(By.XPATH, xpath)
        print("element found for " + key)
        print(element)
        
        print(len(element_dict))
        element.send_keys(text)

        return "Text entered into input field successfully."
    
    except Exception as e:
        return f"Error entering text: {e}"
    
    finally:
        if iframe_index >= 0:
            switch_to_default_content()

@tool
def wait_for_seconds(seconds: int) -> str:
    """Pauses execution for a specified number of seconds.
    
    Parameters:
    seconds (int): The number of seconds to wait.
    
    Returns:
    str: Success message indicating the wait is complete.
    """
    time.sleep(seconds)
    return f"Waited for {seconds} seconds."

# List of tools to use
 
tools = [
    ShellTool(ask_human_input=True), 
    get_page_elements,
    click_element,
    hover_over_element,
    enter_input,
    wait_for_seconds
    # Add more tools if needed
]

# Configure the language model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Set up the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert QA manual tester. Always verify the current state of the page before taking any action, as interacting with elements may change the page state. \n\n"
            "When filling out forms, ensure that each value is entered into its correctly identified field. **Do not rely on assumptions**—before and after entering data, verify that the values match the expected fields. \n\n"
            "**Critical Instructions:** \n"
            "- **Username must always be entered into the username field.** \n"
            "- **Email must always be entered into the email field.** \n"
            "- **Before submitting the form, double-check that the values are correctly assigned to their respective fields.** \n"
            "- **If a value is misplaced, correct it before proceeding.** \n"
            "- **After submission, retrieve the entered values from the form and confirm they are correct in the UI.** \n"
            "- **Fix if any input values are swapped, misplaced, or overwritten incorrectly and try again.**",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Bind the tools to the language model
llm_with_tools = llm.bind_tools(tools)

# Create the agent
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Main loop to prompt the user
#while True:
#    user_prompt = input("Prompt: ")
#    list(agent_executor.stream({"input": user_prompt}))

#def main():
url = "http://localhost:8075"
    #user_steps = input("Enter test steps as JSON: ")  # Expected JSON input
    
    #test_steps = json.loads(user_steps)
driver.get(url)

#extract_elements_from_frame3(driver)

user_prompt = (
    "Test logging into this page using the following credentials: "
    "Username: host Password: Pass123456\n\n"
    "After logging in, wait 3 seconds and close the popup that appears. "
    "This popup does not auto-dismiss and prevents further actions until it is closed.\n\n"
    "Next, create a new user. Generate and correctly fill in all required details, ensuring that each value is entered in its designated field (e.g., username in the username field, email in the email field)."
    "Before submitting, verify that all fields are populated correctly wth the right values to prevent mix-ups.\n\n"
    "After submission, wait 2 seconds, then check the page for any confirmation messages or user records to verify that the new user was successfully created."
    "Do not assume success—actively confirm the presence of the new user record."
)
list(agent_executor.stream({"input": user_prompt}))

#links_info, buttons_info, inputs_info, visible_text = extract_elements_from_frame(driver)
    #elements = extract_elements(driver)
time.sleep(20)
    #print(elements)
    #execute_test_steps(driver, test_steps, elements)
    
driver.quit()
print("Test completed!")

#if __name__ == "__main__":
#    main()
