import requests
from bs4 import BeautifulSoup
import os
import time
import csv

def extract(url):
    # Make a GET request to the website
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the main content of the website
    content = soup.find("body")

    # Return the extracted content
    return content.get_text(separator='\n\n')

def read_file(filename):
    file = open(filename, "r")
    content = file.read()
    file.close()
    return content

def write_file(filename, content):
    file = open(filename, "w")
    file.write(content)
    file.close()

def information(content):
    information = {}
    state = {
        "is_product_information": False,
        "is_visit_website": False,
        "is_features": False,
        "is_categories": False
    }
    for line in content.split("\n"):
        line = line.strip()
        if line == "Product Information":
            state["is_product_information"] = True
        elif line == "Visit website":
            state["is_visit_website"] = True
        elif line.endswith("Features"):
            state["is_features"] = True
            information["features"] = []
        elif line == "Categories":
            state["is_categories"] = True
            information["categories"] = []
            state["is_features"] = False
        elif line == "View All Categories":
            state["is_categories"] = False
        elif line != "":
            if state["is_product_information"] and state["is_visit_website"]:
                information["description"] = line
                state["is_product_information"] = False
                state["is_visit_website"] = True
            elif state["is_features"]:
                information["features"].append(line)
            elif state["is_categories"]:
                if line != "Browse" and not line.isdigit() and line != ".":
                    information["categories"].append(line)

    return information

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

def tools(content):
    tools = []
    state = {
        "is_tool": False,
        "is_categories": False,
    }
    for line in content.split("\n"):
        line = line.strip()
        if line == "VIEW ALL CATEGORIES" or "Read past issues >" in line:
            # Next line is a tool name
            state["is_tool"] = True
        elif line.startswith("#"):
            state["is_categories"] = True
        elif state["is_tool"]:
            tools.append(line)
            state["is_tool"] = False
        elif state["is_categories"] and not line.startswith("#"):
            state["is_categories"] = False
            # The next line could be a tool name or a price, followed by a company name
            if line.startswith("$"):
                state["is_tool"] = True
            else:
                tools.append(line)
    # Remove two lines that are not companies
    tools = [tool for tool in tools 
        if tool != "Discover useful new AI tools." and tool != "Yay! You have seen it all"]
    return tools

def tool_to_url(tool):
    # Lowercase the tool name and replace spaces with dashes
    # Example: This Resume Does Not Exist -> this-resume-does-not-exist
    # Example: MgrWorkbench.ai -> mgrworkbench.ai
    return tool.lower().replace(" | ", " ").replace(" ", "-")

if __name__ == "__main__":

    if len(os.sys.argv) < 3:
        print("Usage: python extract.py [-c|-x|-X|-f|-d|-D] [<category>|<tool>]")
        os.sys.exit(1)

    if "-c" in os.sys.argv:
        category = os.sys.argv[2]
    else:
        tool = os.sys.argv[2]

    # If argument -c is passed, extract the tools in a category
    # Step 1: Extract the content from the website. Example: https://www.futurepedia.io/ai-tools/human-resources
    # Step 2: Extract the tools from the content
    if "-c" in os.sys.argv:
        file_name = f"categories/{category}"
        content = read_file(file_name)
        tools = [tool_to_url(tool) for tool in tools(content)]
        print(tools)

    # If argument -X is passed, iterate through all the tools in a category 
    if "-X" in os.sys.argv:
        category = os.sys.argv[2]
        file_name = f"categories/{category}"
        content = read_file(file_name)
        tools = [tool_to_url(tool) for tool in tools(content)]
        for tool in tools:
            # Check if the tool has already been extracted
            if os.path.exists(f"data/{tool}"):
                print(f"Skipping {tool}")
                continue
            # Otherwise, extract the tool description
            url = f"https://www.futurepedia.io/tool/{tool}"
            content = extract(url)
            write_file(f"data/{tool}", content)
            # Sleep for 5 seconds to avoid getting blocked
            time.sleep(5)

    # If argument -x is passed, extract the content from the website
    if "-x" in os.sys.argv:
        url = f"https://www.futurepedia.io/tool/{tool}"
        content = extract(url)
        write_file(f"data/{tool}", content)
        print(content)

    # If argument -f is passed, read the content from the file
    elif "-f" in os.sys.argv:
        filename = f"data/{tool}"
        content = read_file(filename)
        print(content)

    # If argument -d is passed, extract the description from the website
    elif "-d" in os.sys.argv:
        filename = f"data/{tool}"
        content = read_file(filename)
        info = information(content)
        print("Description:", info["description"])
        features, use_cases = extract_use_cases(info["features"])
        print("Features:", info["features"])
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
                info = information(content)
                if "description" not in info:
                    print(f"Description for {tool} not found")
                else:
                    features, use_cases = extract_use_cases(info["features"])
                    features = " ".join(features)
                    use_cases = " ".join(use_cases)
                    writer.writerow([tool, info["description"], features, use_cases])