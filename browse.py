from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import random
import sys

# Usage: python browse.py <category>
if len(sys.argv) < 2:
    print("Usage: python browse.py <category>")
    sys.exit(1)

category = sys.argv[1]

# Create a webdriver to control the browser
def create_webdriver():
    driver = webdriver.Safari()
    driver.set_window_size(1024, 768)
    return driver

# Navigate to the page for a tool category
def navigate_to_page(driver, category):
    driver.get(f"https://www.futurepedia.io/ai-tools/{category}")

# Get the number of tools in a category
# Look for a text like this:
# Browse 139+ Best AI Tools for Human Resources
# Extract the number before the "+"
def get_number_of_tools(driver):
    number_of_tools = driver.find_element("xpath", "//*[contains(text(), 'Best AI')]").text
    number_of_tools = int(number_of_tools.split("+")[0])
    return number_of_tools

# Find all the links on the page that start with "/tool/"
def find_tool_links(driver):
    # find all the links on the page
    links = driver.find_elements("tag name", "a")

    # filter the links to only include those that start with "/tool/"
    tool_links = [link.get_attribute("href") for link in links 
        if link.get_attribute("href") and link.get_attribute("href").startswith("https://www.futurepedia.io/")]

    # remove duplicates
    dedup_tool_links = []
    for link in tool_links:
        if not link in dedup_tool_links:
            dedup_tool_links.append(link)

    return dedup_tool_links

# Save the links to a file
def save_links(category, links):
    with open(f"categories/{category}", "w") as f:
        # Write the links to the file
        for link in links:
            f.write(link + "\n")

driver = create_webdriver()
navigate_to_page(driver, category)

number_of_tools = get_number_of_tools(driver)
print("Number of tools:", number_of_tools)

links = []

# scroll down the page until the target text is found
print("Scrolling down the page...")

# Loop until the number of links matches the number of tools
while len(links) < number_of_tools:
    # Scroll down the page
    driver.find_element("tag name", "body").send_keys(Keys.PAGE_DOWN)
    # Be nice to the website and sleep for a random amount of time between 1 and 2 seconds
    time.sleep(1 + random.random())

    links = find_tool_links(driver)

    print("{len(links)} links found so far:")
    print(links)

# Now that we have all the links, save the content of the page to a file
save_links(category, links)

# close the browser window
driver.quit()