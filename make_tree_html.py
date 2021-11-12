""" SCRIPT THAT MAKES AN EXAMPLE ICHOR STRUCTURE DIRECTORY AND MAKE A .HTML FILE USING LINUX'S `TREE` COMMAND."""

from pathlib import Path
from ichor.file_structure import FILE_STRUCTURE
from ichor.common.types import FileType
from ichor.files.file import File 
from ichor.common.io import mkdir
import bs4 as bs
import os

OUTPUT_FILE_NAME = "ichor_file_structure.html"

# make an example directory containing ichor's file structure
for ref_name, node in FILE_STRUCTURE.items():
    if node.type_ is FileType.Directory:
        mkdir(Path("ICHOR_FILE_STRUCTURE") / node.path)
for ref_name, node in FILE_STRUCTURE.items():
    if node.type_ is FileType.File:
        (Path("ICHOR_FILE_STRUCTURE") / node.path).touch()

# make tree html file to modify for ichor's file structure
os.system(f'tree -aC -H ./ -T "ICHOR FILE STRUCTURE" -o {OUTPUT_FILE_NAME} ./ICHOR_FILE_STRUCTURE/')


with open(OUTPUT_FILE_NAME, "r") as f:
    soup = bs.BeautifulSoup(f, 'html.parser')

# find all <a> tags and remove the href attribute that redirects because we don't need that
all_hrefs = soup.find_all("a")
for href in all_hrefs:

    del href["href"]
    
    # we want to color directories to distinguish from files
    # also remove the href tag because we don't need the produced html to lead to other files/places
    if "DIR" in href["class"]:
        href["style"] = "color:blue;"
        
# remove versioning that is originally at the bottom of the html
version_tag = soup.find("p", class_="VERSION")
version_tag.decompose()


# add the descriptions to each file/directory when hovering over it

# add css part so that tooltip is displayed on hover
head = soup.head
head.append(soup.new_tag('style', type='text/css'))
head.style.append('.tooltip .tooltiptext {top: -5px; left: 105%;}')

all_a_tags = soup.find_all("a")
for tag in all_a_tags:
    
    for ref_name, node in FILE_STRUCTURE.items():
        
        # if the text in the tag is the same as the name of the node (.name gives the name after the last /)
        if tag.string == node.path.name:
            
            # remove excess whitespace and add to title
            tag["title"] = ' '.join(node.description.split())

with open(OUTPUT_FILE_NAME, "w+") as file:
    file.write(str(soup))

os.system(f'rm -r ./ICHOR_FILE_STRUCTURE/')