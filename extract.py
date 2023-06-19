import requests
from bs4 import BeautifulSoup
import os
import time
import csv

# Read the content of a file
def read_file(filename):
    file = open(filename, "r")
    content = file.read()
    file.close()
    return content

# Write content to a file
def write_file(filename, content):
    file = open(filename, "w")
    file.write(content)
    file.close()

# List the tools in a category
def list_tools_in_category(category):
    file_name = f"categories/{category}"
    content = read_file(file_name)
    return [url.split("/")[-1] for url in content.split("\n") if url]

# Fetch the content of a webpage
def fetch_content(url):
    # Make a GET request to the webpage
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the main content of the website
    content = soup.find("body")

    # Return the extracted content
    return content.get_text(separator='\n\n')

# Fetch the content of the webpage for a tool
def fetch_webpage_for_tool(tool):
    url = f"https://www.futurepedia.io/tool/{tool}"
    content = fetch_content(url)
    # Save the content to a file
    write_file(f"data/{tool}", content)
    return content

# Extract information from the content of a tool webpage
def tool_info(content):
    info = {}
    state = {
        "is_product_information": False,
        "is_added_on": False,
        "is_visit_website": False,
        "is_features": False,
        "is_categories": False
    }
    for line in content.split("\n"):
        line = line.strip()
        if line == "Product Information":
            state["is_product_information"] = True
        elif line == "Added on":
            state["is_added_on"] = True
        elif line == "Visit website":
            state["is_visit_website"] = True
        elif line.endswith("Features"):
            state["is_features"] = True
            info["features"] = []
        elif line == "Categories":
            state["is_categories"] = True
            info["categories"] = []
            state["is_features"] = False
        elif line == "View All Categories":
            state["is_categories"] = False
        elif line != "":
            if state["is_product_information"] and state["is_visit_website"]:
                info["description"] = line
                state["is_product_information"] = False
                state["is_visit_website"] = True
            elif state["is_added_on"]:
                info["added_on"] = line
                state["is_added_on"] = False
            elif state["is_features"]:
                info["features"].append(line)
            elif state["is_categories"]:
                if line != "Browse" and not line.isdigit() and line != ".":
                    info["categories"].append(line)
    return info

def extract_use_cases(features):
    # Split the features into two lists: features proper and use cases
    # The section containing use cases is delimited by the keyword "Use cases"
    # Find a string that starts with "Use cases" and return its index
    index = [i for i, feature in enumerate(features) if feature.lower().startswith("use cases")]
    if len(index) > 0:
        use_cases = features[index[0]:]
        features = features[:index[0]]
    else:
        use_cases = []
    return features, use_cases

if __name__ == "__main__":

    if len(os.sys.argv) < 3:
        print("Usage: python extract.py [-c|-x|-X|-f|-d|-D] [<category>|<tool>]")
        os.sys.exit(1)

    # If argument -c is passed, list the tools in a category
    elif "-c" in os.sys.argv:
        category = os.sys.argv[2]
        tools = list_tools_in_category(category)
        print(tools)

    # If argument -x is passed, fetch the webpage describing a tool
    elif "-x" in os.sys.argv:
        tool = os.sys.argv[2]
        content = fetch_webpage_for_tool(tool)
        print(content)  

    # If argument -X is passed, fetch all the tools in a category 
    elif "-X" in os.sys.argv:
        category = os.sys.argv[2]
        tools = list_tools_in_category(category)
        for tool in tools:
            # Check if the tool has already been extracted
            if os.path.exists(f"data/{tool}"):
                print(f"Skipping {tool}")
                continue
            # Otherwise, extract the tool description
            print(f"Extracting {tool} description")
            fetch_webpage_for_tool(tool)
            # Sleep for 5 seconds to be nice to the server
            time.sleep(5)

    # If argument -f is passed, read the description of a tool
    elif "-f" in os.sys.argv:
        tool = os.sys.argv[2]
        filename = f"data/{tool}"
        content = read_file(filename)
        print(content)

    # If argument -d is passed, extract the description from the website
    elif "-d" in os.sys.argv:
        tool = os.sys.argv[2]
        filename = f"data/{tool}"
        content = read_file(filename)
        info = tool_info(content)
        print("Description:", info["description"])
        print("Added on:", info["added_on"])
        features, use_cases = extract_use_cases(info["features"])
        print("Features:", features)
        print("Use cases:", use_cases)

    # If argument -D is passed, extract descriptions for all the tools
    elif "-D" in os.sys.argv:
        # Open a csv file for the category
        # Headers: Tool, Description, Features, Use Cases
        category = os.sys.argv[2]
        with open(f"csv/{category}.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Tool", "Description", "Features", "Use Cases"])
            for tool in os.listdir("data"):
                filename = f"data/{tool}"
                content = read_file(filename)
                info = tool_info(content)
                if "description" not in info:
                    print(f"Description for {tool} not found")
                else:
                    features, use_cases = extract_use_cases(info["features"])
                    features = " ".join(features)
                    use_cases = " ".join(use_cases)
                    writer.writerow([tool, info["description"], features, use_cases])