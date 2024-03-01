# -*- coding: utf-8 -*-
"""
Merge and clean submission dates data
"""

import pandas as pd
import matplotlib.pyplot as plt
from path import path

# Submissions data
# JHR <==
# Merge JHR first part of data with the update
data_pub_jhr_partial = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\JHR_definitive.pickle")
data_pub_jhr_update = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\JHR_update_2024.pickle")
del(data_pub_jhr_partial["check"])
del(data_pub_jhr_partial["index"])
data_pub_jhr = pd.concat([data_pub_jhr_partial, data_pub_jhr_update])
data_pub_jhr["journal"] = "JHR"

# JUrbE <==
data_pub_jurbe_partial = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\JUrbE_final.pickle")
data_pub_jurbe_update = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\JUrbE_final_additional.pickle")

data_pub_jurbe = pd.concat([data_pub_jurbe_partial, data_pub_jurbe_update])
data_pub_jurbe["journal"] = "JUrbE"
data_pub_jurbe['authors_final'] = data_pub_jurbe['authors_scopus']

# RED <==
data_pub_red = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\RED.pickle")
data_pub_red["journal"] = "RED"

# ReStud <==
data_pub_restud_partial = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\restud.pickle")
data_pub_restud_update = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\restud_additional.pickle")

data_pub_restud = pd.concat([data_pub_restud_partial, data_pub_restud_update])
data_pub_restud["journal"] = "ReStud"

# remove 1 publication submitted in 2022
data_pub_restud = data_pub_restud[data_pub_restud.pub_year != 2022]

# JOLE <==
data_pub_jole = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\JOLE_final.pickle")
data_pub_jole["journal"] = "JOLE"

# EJ <==
data_pub_ej = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\EJ_final.pickle")
data_pub_ej["journal"] = "EJ"


# Concat and keep relevant columns
data_pub = pd.concat([data_pub_jurbe, data_pub_jhr, data_pub_red,
                      data_pub_restud, data_pub_jole, data_pub_ej])

data_pub = data_pub[['authors_final', 'submission', 'publication', 'pub_year',
                     'sub_year', "doi", 'journal']]

# For each journal add the data of the introdcution of submission fees
data_pub["intro_fees"] = None
data_pub.loc[data_pub.journal == "ReStud", "intro_fees"] = pd.Timestamp(year = 2016, month = 4, day = 1)
data_pub.loc[data_pub.journal == "JOLE", "intro_fees"] = pd.Timestamp(year = 2018, month = 7, day = 1)
data_pub.loc[data_pub.journal == "JHR", "intro_fees"] = pd.Timestamp(year = 2017, month = 1, day = 1)
data_pub.loc[data_pub.journal == "EJ", "intro_fees"] = pd.Timestamp(year = 2019, month = 9, day = 1)
data_pub.loc[data_pub.journal == "JUrbE", "intro_fees"] = pd.Timestamp(year = 2017, month = 1, day = 1)
data_pub.loc[data_pub.journal == "RED", "intro_fees"] = pd.Timestamp(year = 2020, month = 6, day = 1)

# Days, weeks and months from the intro of fees
data_pub["days_from_intro"] = (data_pub.submission - data_pub.intro_fees).apply(lambda x: x.days)
data_pub["weeks_from_intro"] = data_pub["days_from_intro"]//7
data_pub["months_from_intro"] = data_pub["days_from_intro"]//30

# Sanity checks histograms
plt.hist(data_pub["days_from_intro"][(data_pub["days_from_intro"]<180) & (data_pub["days_from_intro"]>-180)])
plt.show()
plt.hist(data_pub["weeks_from_intro"][(data_pub["weeks_from_intro"]<52) & (data_pub["weeks_from_intro"]>-52)], bins =52)
plt.show()
plt.hist(data_pub["months_from_intro"][(data_pub["months_from_intro"]<=24) & (data_pub["months_from_intro"]>=-24)], bins =49)
plt.show()

# drop one duplicate
data_pub.drop_duplicates("doi", inplace = True)

# Save data
data_pub.to_excel(rf"{path}\Data\Cleaned_Datasets\submission_dates.xlsx", index = False)
data_pub.to_pickle(rf"{path}\Data\Cleaned_Datasets\submission_dates.pickle")

# Plot day of submission (bunching at firt day of month)
plt.hist(data_pub.submission.apply(lambda x: x.day), bins = 31)
plt.show()

plt.hist(data_pub[(data_pub.journal != "JHR") & (data_pub.journal != "ReStud")].submission.apply(lambda x: x.day), bins = 31)
plt.show()

plt.hist(data_pub.submission.apply(lambda x: x.month), bins = 12)
plt.show()





