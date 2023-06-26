# How to use

## List tools
First, run browse.py category to get the links of the tools in the category. This may take a while.

```sh
python3 browse.py <category>
```

## Extract tool data
Then, run extract.py -D category to download the tool information for a category into a csv file.

```sh
python3 extract.py -D <category>
```

Extract has a few other options. Please check the code.

## Show landscape
Run landscape.py to show the landscape of a category, and upload the csv file with the tool information to visualize the landscape.

```sh
streamlit run landscape.py
```