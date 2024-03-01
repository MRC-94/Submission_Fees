# -*- coding: utf-8 -*-
"""
Clean and merge data on PhD year completion
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
from path import path

def year_phd_completion(input_string):
    '''
    Transform the string extracted from CVs into the year of completion of the PhD.
    If current PhD student, completion year is set to 2024.
    '''
    word_list = ["present", "pres", "current"] # Word list used to identify current PhD students
    
    if any(ele in input_string.lower() for ele in word_list): # This for current PhD student
        compl_year = 2024
        print(input_string)
        try: # This as sanity check for old CV, if diff very large it means it is an old CV
            start = int(re.findall(r'\b\d{4}\b', input_string)[0])
            diff = compl_year - start
            if diff> 5:
                compl_year = None
        except:
            compl_year = None
    else:
        match = re.search(r'\b\d{2,4}\D*[/\-.–]\D*(\d{2})\b(?!.{3})', input_string)
        if match:
            extracted_number = match.group(1)
            extracted_number =  int(extracted_number)
            if (extracted_number >= 60) & (extracted_number <= 99) :
                compl_year = 1900 + extracted_number
            if extracted_number <= 30:
                compl_year = 2000 + extracted_number
        else:
            years = re.findall(r'\b\d{4}\b', input_string)
            try:
                compl_year = int(max(years))
            except:
                compl_year = None
    print(input_string, "-->>", compl_year)
    return compl_year


def clean_data_authors(data, journal):
    '''
    - All column names to lower string
    - Remove ".pdf" from author names
    - Clean year of PhD completion
    - Add column with journal name
    '''
    data.columns = [col.lower() for col in data.columns]
    data["name"] = data["name"].apply(lambda x: x.split(".pdf")[0].replace(".", "").replace(",", "").lower())
    data = data.astype({'phd year':'string'})
    data["phd_completion"] = data["phd year"][data["phd year"].isna() == False].apply(year_phd_completion)
    data["journal"] = journal
    return data

path_data = rf"{path}\Data\Extracted_Data"

## Data authors
author_jhr = clean_data_authors(pd.read_excel(rf"{path_data}\JHR.xlsx"), "JHR")
author_jurbe = clean_data_authors(pd.read_excel(rf"{path_data}\Journal_Urban_Economics.xlsx"), "JUrbE")
author_red = clean_data_authors(pd.read_excel(rf"{path_data}\RED.xlsx"), "RED")
author_ej = clean_data_authors(pd.read_excel(rf"{path_data}\EJ.xlsx"), "EJ")
author_restud = clean_data_authors(pd.read_excel(rf"{path_data}\ReStud.xlsx"), "ReStud")
author_jole = clean_data_authors(pd.read_excel(rf"{path_data}\JOLE.xlsx"), "JOLE")

data_author = pd.concat([author_jhr, author_jurbe, author_red, author_ej, author_restud, author_jole])

# Check distribution is ok
plt.hist(data_author["phd_completion"][data_author["phd_completion"].isna() == False])
plt.show()

data_phd_year = data_author[['name', 'phd_completion']]

# Some authors appear twice in PhD data
data_phd_year.drop_duplicates("name", inplace = True)

data_phd_year.to_excel(rf"{path}\Data\Cleaned_Datasets\year_phd.xlsx", index = False)


