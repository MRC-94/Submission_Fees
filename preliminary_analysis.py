# -*- coding: utf-8 -*-
"""
Preliminary Analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
from scipy.special import boxcox1p
import ast
from path import path

def main_reg(data, outcome , nn, poly, FE = True):
    '''
    Linear regression with donut discontinuity at zero, bandwidth "nn", of polynomial order "poly" (from 0 to 2)
    Outcome is string with column name of outcome in data
    '''
    merged_reg = data[(data.months_from_intro<=nn) & (data.months_from_intro>=-nn)].dropna()

    merged_reg = merged_reg[(merged_reg.months_from_intro != 0) & (merged_reg.months_from_intro != -1)]

    X_reg = pd.DataFrame(merged_reg['months_from_intro'])
    X_reg["constant"] = 1
    X_reg["after"] = 0
    X_reg.loc[X_reg.months_from_intro >= 0, 'after'] = 1
    if poly > 0:
        X_reg["after_months_interaction"] = X_reg["after"]*(X_reg['months_from_intro'])
    if poly > 1:
        X_reg['months_from_intro_sq'] = X_reg['months_from_intro']*X_reg['months_from_intro']
        X_reg["after_months_sq_interaction"] = X_reg["after"]*(X_reg['months_from_intro_sq'])
    if poly > 2:
        return print("Max polynomial order 2")
    if poly == 0:
        del(X_reg['months_from_intro'])
    if FE:
        X_reg = X_reg.merge(pd.get_dummies(merged_reg["sub_month"].apply(lambda x: int(x)), prefix = "month", dtype = int), left_index=True, right_index=True)
        del(X_reg["month_1"])
    
        X_reg = X_reg.merge(pd.get_dummies(merged_reg["journal"], prefix = "journal", dtype = int), left_index=True, right_index=True)
        del(X_reg["journal_EJ"])

    y = merged_reg[f'{outcome}']

    ols = sm.OLS(y.values, X_reg)
    ols_result = ols.fit()
    return ols_result.summary()

# Set here the number before and after the intro of the fees to consider in 
# regressions and RDD plots
N = 18

# Import data with authors and year of completion PhD
data_phd_year = pd.read_excel(rf"{path}\Data\Cleaned_Datasets\year_phd.xlsx")

# Import data with submission dates
data_pub = pd.read_pickle(rf"{path}\Data\Cleaned_Datasets\submission_dates.pickle")

# Copy of dataset without expliding authors
data_pub_one_row = data_pub.copy()

# Create one row per author
data_pub["authors_all"]  = data_pub['authors_final']
data_pub = data_pub.explode('authors_final')

# Remove 2 obs without authors
data_pub = data_pub[~ data_pub['authors_final'].isna()]

# Clean authors names
data_pub['authors_final'] = data_pub['authors_final'].apply(lambda x: x.replace(".", "").replace(",", "").lower())

# drop few duplicated author publication pairs
data_pub.drop_duplicates(['authors_final', 'doi'], inplace = True)

# Merge publication and authors seniority data
merged = data_pub.merge(data_phd_year, left_on = 'authors_final', right_on = "name", how = "left", indicator = True)
##Some these not matched, explained by those in excel "not_found" (those for which I could not find info)

print(merged._merge.value_counts()) # 5473 before merge, 281 not merged
merged = merged[merged._merge == "both"]

# Seniority variables
merged["seniority_sub"] = merged.sub_year - merged.phd_completion
merged["seniority_positive"] = merged["seniority_sub"]
merged.loc[merged["seniority_positive"] < 0, "seniority_positive"] = 0
merged["seniority_boxcox"] = boxcox1p(merged["seniority_positive"], 0)
merged["junior"] = np.nan
merged["junior"][(merged["seniority_sub"]>3) & (merged["seniority_sub"].isna() == False)] = 0
merged["junior"][(merged["seniority_sub"]<=3) & (merged["seniority_sub"].isna() == False)] = 1

merged["junior_1y"] = np.nan
merged["junior_1y"][(merged["seniority_sub"]>1) & (merged["seniority_sub"].isna() == False)] = 0
merged["junior_1y"][(merged["seniority_sub"]<=1) & (merged["seniority_sub"].isna() == False)] = 1

merged["c"] = 1 # Used for number of authors per publication
merged["sub_month"] = merged.submission.apply(lambda x: x.month)

# Save in dta format
merged_for_stata = merged.copy()
merged_for_stata = merged_for_stata.astype({'submission' : "str", 'publication' : "str",
                                            'intro_fees' : "str", 'authors_all' : "str"})
merged_for_stata.to_stata(rf"{path}\Data\Cleaned_Datasets\merged_phd_year.dta", version=118)

###############################################################################

# Descriptive Statistics ######################################################

###############################################################################

# Histogram seniority at submission
plt.hist(merged["seniority_sub"], bins=61, rwidth=0.8, color='#607c8e', density = True)
plt.xlabel("Seniority at Submission")
plt.ylabel("Frequency")
plt.savefig(fr"{path}\Results\Figures\Hist_Seniority_At_Submission.pdf", format="pdf", bbox_inches="tight")
plt.show()

# Evolution seniority over time
dd = merged[["seniority_sub", "sub_year"]].groupby(by="sub_year").mean()
dd2 = merged[["seniority_sub", "sub_year"]].groupby(by="sub_year").median()
plt.plot(dd, marker = "o", markersize = 2, color='#607c8e', markeredgecolor = 'black', label = "Average")
plt.plot(dd2, marker = "o", markersize = 2, color='gold', markeredgecolor = 'black', label = "Median")
plt.ylim(5, 15)
plt.yticks([5, 10, 15])
plt.grid(color='lightsteelblue', linestyle='-', linewidth=0.1)
plt.xlabel("Year of Submission")
plt.ylabel("Seniority at Submission")
plt.legend()
plt.savefig(fr"{path}\Results\Figures\Seniority_Over_Years.pdf", format="pdf", bbox_inches="tight")
plt.show()

# Evolution seniotrity over time, centered at submission intro
merged["years_from_intro"] = merged["months_from_intro"]//12
dd = merged[["seniority_sub",  "years_from_intro"]].groupby(by="years_from_intro").mean()
dd2 = merged[["seniority_sub", "years_from_intro"]].groupby(by="years_from_intro").median()
plt.plot(dd[(dd.index<=2) & (dd.index>=-3)], marker = "o", markersize = 2, markeredgecolor = 'black', label = "Average")
plt.plot(dd2[(dd2.index<=2) & (dd2.index>=-3)], marker = "o", markersize = 2, color='gold', markeredgecolor = 'black', label = "Median")
plt.vlines(-0.5, ymin=5, ymax=15, linestyle = "dashed", color = "lightsteelblue" )
plt.ylim(5, 15)
plt.yticks([5, 10, 15])
plt.grid(color='lightsteelblue', linestyle='-', linewidth=0.1)
plt.xlabel("Year of Submission Relative to Fees Intro")
plt.ylabel("Seniority at Submission")
plt.legend()
plt.savefig(fr"{path}\Results\Figures\Seniority_Over_Years_Centered.pdf", format="pdf", bbox_inches="tight")
plt.show()

# Seniority by journal
dd = merged[["seniority_sub",  "journal"]].groupby(by="journal").mean()
dd2 = merged[["seniority_sub", "journal"]].groupby(by="journal").median()
dd.sort_values("seniority_sub", inplace = True)
dd2.sort_values("seniority_sub", inplace = True)
plt.bar(dd.index, dd.seniority_sub, label = "Average", color='#607c8e')
plt.bar(dd2.index, dd2.seniority_sub, label = "Median", color = "lightsteelblue" )
plt.rc('axes', axisbelow=True)
plt.grid(color='lightsteelblue', linestyle='-', linewidth=0.1)
plt.legend()
plt.savefig(fr"{path}\Results\Figures\Seniority_By_Journals.pdf", format="pdf", bbox_inches="tight")
plt.show()

# Group by month from submission
grouped_merged = merged[['junior', "seniority_sub", "seniority_boxcox", 'months_from_intro', "junior_1y", "c"]].groupby(by = ['months_from_intro'], as_index = False, dropna = False).agg({"seniority_sub" : "mean", 'junior' : "mean", "junior_1y" : "mean", "seniority_boxcox" : "mean", 'months_from_intro' : "mean", "c": "sum"})
grouped_small = grouped_merged[(grouped_merged.months_from_intro<=N) & (grouped_merged.months_from_intro>=-N)]

# Evolution over time junior proportion
plt.vlines(0, ymin=0.1, ymax=0.45, linestyle = "dashed", color = "black" )
plt.plot(grouped_small.months_from_intro, grouped_small.junior, color = "salmon")
plt.xlabel("Months From Fees Intro", fontsize=12)
plt.ylabel("Proportion Juniors", fontsize=12)
plt.show()

## RDD like plot ##
# Remove month right after and before fees intro
grouped_small = grouped_small[(grouped_small.months_from_intro != 0) & (grouped_small.months_from_intro != -1)]

# Years seniority
plt.vlines(-0.4, ymin=5, ymax=15, linestyle = "dashed", color = "black" )
plt.hlines(np.mean(grouped_small.seniority_sub[grouped_small.months_from_intro < 0]), xmin= -N, xmax= -.4,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.hlines(np.mean(grouped_small.seniority_sub[grouped_small.months_from_intro > 0]), xmin=-.4, xmax= N,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.scatter(grouped_small.months_from_intro, grouped_small.seniority_sub, color = "salmon")
plt.xlabel("Months From Intro Fees", fontsize=12)
plt.ylabel("Years Seniority", fontsize=12)
plt.show()

# Junior 1 year
plt.vlines(-0.4, ymin=0, ymax=0.4, linestyle = "dashed", color = "black" )
plt.hlines(np.mean(grouped_small.junior_1y[grouped_small.months_from_intro < 0]), xmin= -N, xmax= -.4,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.hlines(np.mean(grouped_small.junior_1y[grouped_small.months_from_intro > 0]), xmin=-.4, xmax= N,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.scatter(grouped_small.months_from_intro, grouped_small.junior_1y, color = "salmon")
plt.xlabel("Months From Intro Fees", fontsize=12)
plt.ylabel("Proportion Juniors (1Y)", fontsize=12)
plt.show()

# Junior 3 year
plt.vlines(-0.4 , ymin=0, ymax=0.6, linestyle = "dashed", color = "black" )
plt.hlines(np.mean(grouped_small.junior[grouped_small.months_from_intro < 0]), xmin= -N, xmax= -.4,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.hlines(np.mean(grouped_small.junior[grouped_small.months_from_intro > 0]), xmin=-.4, xmax= N,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.scatter(grouped_small.months_from_intro, grouped_small.junior, color = "salmon")
plt.xlabel("Months From Intro Fees", fontsize=12)
plt.ylabel("Proportion Juniors (3Y)", fontsize=12)
plt.show()

# Box-cox transformed seniority
plt.vlines(-0.4, ymin=1.5, ymax=2.5, linestyle = "dashed", color = "black" )
plt.hlines(np.mean(grouped_small.seniority_boxcox[grouped_small.months_from_intro < 0]), xmin= -N, xmax= -.4,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.hlines(np.mean(grouped_small.seniority_boxcox[grouped_small.months_from_intro > 0]), xmin=-.4, xmax= N,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.scatter(grouped_small.months_from_intro, grouped_small.seniority_boxcox, color = "salmon")
plt.xlabel("Months From Intro Fees", fontsize=12)
plt.ylabel("Seniority Log", fontsize=12)
plt.show()

###############################################################################

# Publication Level ###########################################################

###############################################################################

# Group by publication
pub_merged = merged[["sub_month", 'journal', 'junior', "seniority_boxcox",
                     'months_from_intro', 'doi', "junior_1y", "c"]].groupby(by = ['doi', 'journal' ], as_index = False, dropna = False).agg({'junior' : "mean", "junior_1y" : "mean", "seniority_boxcox" : "mean", 'months_from_intro' : "mean", "c": "sum", "sub_month" : "mean"})

# Dummy if all authors are junior
pub_merged["all_junior"] = 0
pub_merged.loc[pub_merged.junior.isna(), "all_junior"] = np.nan
pub_merged.loc[pub_merged.junior == 1, "all_junior"] = 1

# Save in dta format
merged_for_stata = pub_merged.copy()
merged_for_stata.to_stata(rf"{path}\Data\Cleaned_Datasets\n_auth.dta", version = 118)

# Group by month from submission
pub_merged_group = pub_merged[['all_junior', 'months_from_intro', "c"]].groupby(by = ['months_from_intro'], as_index = False, dropna = False).mean()
pub_merged_small = pub_merged_group[(pub_merged_group.months_from_intro<=N) & (pub_merged_group.months_from_intro>=-N)]

## Plots
pub_merged_small = pub_merged_small[(pub_merged_small.months_from_intro != 0) & (pub_merged_small.months_from_intro != -1)]

# Pub level plots
plt.vlines(-0.4 , ymin=0, ymax=0.6, linestyle = "dashed", color = "black" )
plt.hlines(np.mean(pub_merged_small.all_junior[pub_merged_small.months_from_intro < 0]), xmin= -N, xmax= -.4,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.hlines(np.mean(pub_merged_small.all_junior[pub_merged_small.months_from_intro > 0]), xmin=-.4, xmax= N,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.scatter(pub_merged_small.months_from_intro, pub_merged_small.all_junior, color = "salmon")
plt.xlabel("Months From Intro Fees", fontsize=12)
plt.ylabel("Proportion Juniors", fontsize=12)
plt.show()

# Number of publications
plt.vlines(-0.4 , ymin=1, ymax=3.5, linestyle = "dashed", color = "black" )
plt.hlines(np.mean(pub_merged_small.c[pub_merged_small.months_from_intro < 0]), xmin= -N, xmax= -.4,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.hlines(np.mean(pub_merged_small.c[pub_merged_small.months_from_intro > 0]), xmin=-.4, xmax= N,
           linestyle = "dashed", color = "lightseagreen", zorder = -1)
plt.scatter(pub_merged_small.months_from_intro, pub_merged_small.c, color = "salmon")
plt.xlabel("Months From Intro Fees", fontsize=12)
plt.ylabel("Number of Authors", fontsize=12)
plt.show()

# Regressions #################################################################

# Seniority of submission (Years from PhD completion)  
main_reg(merged, 'seniority_sub' , N, 1)

# Junior (leq 3 year from PhD completion)
main_reg(merged, 'junior' , N, 1)

# Junior 1Y (leq 1 year from PhD completion)
main_reg(merged, 'junior_1y' , N, 1)

# Junior (seniority between y and x)
x=5
y=0
merged["junior_x"] = np.nan
merged["junior_x"][(merged["seniority_sub"]>x) & (merged["seniority_sub"].isna() == False)] = 0
merged["junior_x"][(merged["seniority_sub"]<=x) & (merged["seniority_sub"]>=y) & (merged["seniority_sub"].isna() == False)] = 1
merged["junior_x"][(merged["seniority_sub"]<=y)] = np.nan
# Junior x (leq x year from PhD completion)
main_reg(merged, 'junior_x' , N, 1)

# Pub level, number of authors
main_reg(pub_merged, 'c' , N, poly = 1, FE = False)

###############################################################################

### Using Incites Clarivate (ic) Data #########################################

###############################################################################

# Authors seniority in the field (alternative measure: n publications)
# Import data on publications and h-index in journals 
ej_ic_pub = pd.read_excel(rf"{path}\Data\Incites_Clarivate\EJ\EJ_final_pub.xlsx")
red_ic_pub = pd.read_excel(rf"{path}\Data\Incites_Clarivate\RED\RED_final_pub.xlsx")
jurbe_ic_pub = pd.read_excel(rf"{path}\Data\Incites_Clarivate\JUrbE\JUrbE_final_pub.xlsx")
jole_ic_pub = pd.read_excel(rf"{path}\Data\Incites_Clarivate\JOLE\JOLE_final_pub.xlsx")
restud_ic_pub = pd.read_excel(rf"{path}\Data\Incites_Clarivate\ReStud\ReStud_final_pub.xlsx")
jhr_ic_pub = pd.read_excel(rf"{path}\Data\Incites_Clarivate\JHR\JHR_final_pub.xlsx")

all_ic_pub = pd.concat([ej_ic_pub, red_ic_pub, jurbe_ic_pub, jole_ic_pub, restud_ic_pub, jhr_ic_pub])

merged_ic_pub = data_pub_one_row.merge(all_ic_pub, on = "doi", how = "left", indicator = True)
merged_ic_pub = merged_ic_pub[merged_ic_pub._merge == "both"] # 75 publications dropped
del(merged_ic_pub["_merge"])

# Create variable with number of publications and journal-specific h-index of the relevant year
merged_ic_pub["n_pub"] = np.nan
merged_ic_pub["jh_index"] = np.nan
for yyy in range(2014, 2022):
    yyy_str_m1 = f"{yyy - 1}"
    print(yyy_str_m1[2:])
    merged_ic_pub.loc[merged_ic_pub["sub_year"] == yyy ,"n_pub"] = merged_ic_pub.loc[merged_ic_pub["sub_year"] == yyy ,f"n_doc_{yyy_str_m1[2:]}"]
    merged_ic_pub.loc[merged_ic_pub["sub_year"] == yyy ,"jh_index"] = merged_ic_pub.loc[merged_ic_pub["sub_year"] == yyy ,f"h_index_{yyy_str_m1[2:]}"]

# Add submission month
merged_ic_pub["sub_month"] = merged_ic_pub.submission.apply(lambda x: x.month)

# Descriptives
plt.hist(merged_ic_pub[merged_ic_pub.n_pub<=10].n_pub, bins = 10, rwidth=0.9, color='#607c8e', density = True)
plt.xlabel("N. Publications in Journal at Submission")
plt.ylabel("Frequency")
plt.savefig(fr"{path}\Results\Figures\Hist_Publications_At_Submission.pdf", format="pdf", bbox_inches="tight")
plt.show()

# Save in dta format
merged_ic_for_stata = merged_ic_pub.copy()
merged_ic_for_stata = merged_ic_for_stata.astype({'submission' : "str", 'publication' : "str",
                                            'intro_fees' : "str", 'authors_final' : "str"})
merged_ic_for_stata.to_stata(rf"{path}\Data\Cleaned_Datasets\merged_n_pub.dta", version=118 )


# Regressions #################################################################
# journal specific h-index
main_reg(merged_ic_pub, 'jh_index' , N, poly = 1)

# Number of publications
main_reg(merged_ic_pub, 'n_pub' , N, poly = 1)

###############################################################################

### Publication level data from ic (institution, num citations, n pages) ######

###############################################################################

# Import data on all publications level data from ic 
ej_ic_pub_level = pd.read_excel(rf"{path}\Data\Incites_Clarivate\EJ\EJ_all_pub_14_23.xlsx")
red_ic_pub_level = pd.read_excel(rf"{path}\Data\Incites_Clarivate\RED\RED_all_pub_14_23.xlsx")
jurbe_ic_pub_level = pd.read_excel(rf"{path}\Data\Incites_Clarivate\JUrbE\JUrbE_all_pub_14_23.xlsx")
jole_ic_pub_level = pd.read_excel(rf"{path}\Data\Incites_Clarivate\JOLE\JOLE_all_pub_14_23.xlsx")
restud_ic_pub_level = pd.read_excel(rf"{path}\Data\Incites_Clarivate\ReStud\ReStud_all_pub_14_23.xlsx")
jhr_ic_pub_level = pd.read_excel(rf"{path}\Data\Incites_Clarivate\JHR\JHR_all_pub_14_23.xlsx")

# Concat, keep relevant columns and rename them
all_ic_pub_level = pd.concat([ej_ic_pub_level, red_ic_pub_level, jurbe_ic_pub_level,
                              jole_ic_pub_level, restud_ic_pub_level, jhr_ic_pub_level])

all_ic_pub_level = all_ic_pub_level[['DOI', 'Affiliations', 'Times Cited, WoS Core', 'Number of Pages']] 
all_ic_pub_level.columns = ["doi", 'affiliations', 'citations', 'n_pages']

# Merge with publication data on submission
merged_ic_pub_level = data_pub_one_row.merge(all_ic_pub_level, on = "doi", how = "left", indicator = True)
merged_ic_pub_level = merged_ic_pub_level[merged_ic_pub_level._merge == "both"] # 72 publications dropped
del(merged_ic_pub_level["_merge"])
merged_ic_pub_level["sub_month"] = merged_ic_pub_level.submission.apply(lambda x: x.month)

# Save in dta format
merged_ic_for_stata = merged_ic_pub_level.copy()
merged_ic_for_stata = merged_ic_for_stata.astype({'submission' : "str", 'publication' : "str",
                                            'intro_fees' : "str", 'authors_final' : "str"})
merged_ic_for_stata.to_stata(rf"{path}\Data\Cleaned_Datasets\merged_n_cit.dta", version = 118 )

# Regressions #################################################################

main_reg(merged_ic_pub_level, 'citations' , N, poly = 1)

# Institution Data ############################################################

# Clean and explode institution list
merged_ic_inst = merged_ic_pub_level.copy()
merged_ic_inst = merged_ic_inst[~merged_ic_inst["affiliations"].isna()]
merged_ic_inst["affiliations"] = merged_ic_inst["affiliations"].apply(lambda x: [i.strip() for i in x.split(";")])
merged_ic_inst["n_affs"] = merged_ic_inst["affiliations"].apply(lambda x: len(x))
merged_ic_inst["affiliation"] = merged_ic_inst["affiliations"].copy()
merged_ic_inst = merged_ic_inst.explode("affiliation")

# import institutions ranking and merge
inst_rank = pd.read_csv(rf"{path}\Data\Incites_Clarivate\Organizations.csv")
inst_rank = inst_rank[['Name', 'H-Index', 'Rank', 'Country or Region']]
inst_rank.columns = ["affiliation", "h_index", 'rank', 'country']
merged_ic_inst = merged_ic_inst.merge(inst_rank, on = "affiliation")

# Dummy equal one if institution is in USA
merged_ic_inst["USA"] = 0
merged_ic_inst.loc[merged_ic_inst.country == "USA", "USA"] = 1
merged_ic_inst["sub_month"] = merged_ic_inst.submission.apply(lambda x: x.month)

# Save in dta format
merged_ic_for_stata = merged_ic_inst.copy()
merged_ic_for_stata = merged_ic_for_stata.astype({'submission' : "str", 'publication' : "str",
                                            'intro_fees' : "str", 'authors_final' : "str"})
del(merged_ic_for_stata["affiliations"])
merged_ic_for_stata.to_stata(rf"{path}\Data\Cleaned_Datasets\merged_inst.dta", version=118)

# Regressions #################################################################
# Rank
main_reg(merged_ic_inst, 'rank', N, poly = 1)

# Log Rank
merged_ic_inst["log_rank"] =  np.log(merged_ic_inst["rank"])
main_reg(merged_ic_inst, 'log_rank', N, poly = 1)

# Prob US institution
main_reg(merged_ic_inst, 'USA', N, poly = 1)

### JEL codes #################################################################
# Clean and concat JEL codes datasets
jhr_jel = pd.read_pickle(rf"{path}\Data\Scraped_Submission_Dates\JHR_jel.pickle")
jhr_jel["journal"] = "jhr"

ej_jel = pd.read_csv(rf"{path}\Data\Scraped_Submission_Dates\EJ_data_JEL.csv",
                     converters={"JEL_list":ast.literal_eval})
del(ej_jel['Unnamed: 0'])
ej_jel.columns = [ 'title', 'doi', 'jel_list']
ej_jel["doi"] = ej_jel["doi"].apply(lambda x: x.split("https://doi.org/")[1])
ej_jel["journal"] = "ej"

red_jel = pd.read_csv(rf"{path}\Data\Scraped_Submission_Dates\RED_data_JEL.csv",
                     converters={"JEL":ast.literal_eval})
del(red_jel['Unnamed: 0'])
red_jel.columns = ['title', 'doi', 'jel_list']
red_jel["doi"] = red_jel["doi"].apply(lambda x: x.split("https://doi.org/")[1])
red_jel["journal"] = "red"

jurbe_jel = pd.read_csv(rf"{path}\Data\Scraped_Submission_Dates\JUrbE_JEL.csv",
                     converters={"JEL":ast.literal_eval})
del(jurbe_jel['Unnamed: 0'])
jurbe_jel.columns = [ 'title', 'doi', 'jel_list']
jurbe_jel["doi"] = jurbe_jel["doi"].apply(lambda x: x.split("https://doi.org/")[1])
jurbe_jel["journal"] = "jurbe"

restud_jel = pd.read_excel(rf"{path}\Data\Scraped_Submission_Dates\restud_JEL_codes.xlsx")
restud_jel.dropna(inplace = True)
restud_jel["JEL"] = restud_jel.JEL.apply(lambda x: [i.strip() for i in x.split(",")])
del(restud_jel['Unnamed: 0'])
restud_jel.columns = ['doi', 'jel_list']
restud_jel["journal"] = "restud"

all_jel = pd.concat([jhr_jel, ej_jel, red_jel, jurbe_jel, restud_jel])
all_jel["jel"] = all_jel["jel_list"].copy()
all_jel = all_jel.explode("jel")
all_jel["jel"] = all_jel["jel"].str.lower()

# Create a dummy variable if jel code is in 10 most common JEL codes at journal level
for jjj in all_jel.journal.value_counts().index:
    print(jjj)
    cc = all_jel[all_jel.journal == jjj].jel.value_counts() 
    top_10 = cc.index[:10] # most common JEL codes at journal level
    print(top_10.values)
    all_jel.loc[(all_jel.journal == jjj), "top10"] = all_jel.loc[(all_jel.journal == jjj), "jel"].apply(lambda x: int(x in top_10.values))

del(all_jel["jel_list"])
all_jel = all_jel.dropna(subset = "jel")
del(all_jel["title"])
del(all_jel["journal"])

# Match jel codes with publications
merged_jel = data_pub_one_row.merge(all_jel, on = "doi", how = "left", indicator = True)
merged_jel = merged_jel[merged_jel._merge == "both"] # 675 publications not matched
del(merged_jel["_merge"])
merged_jel["sub_month"] = merged_jel.submission.apply(lambda x: x.month)

# Save in dta format
jel_for_stata = merged_jel.copy()
jel_for_stata = jel_for_stata.astype({'submission' : "str", 'publication' : "str",
                                            'intro_fees' : "str", 'authors_final' : "str"})
jel_for_stata.to_stata(rf"{path}\Data\Cleaned_Datasets\merged_jel.dta", version = 118)

# Regressions #################################################################

main_reg(merged_jel, 'top10', N, poly = 1)
main_reg(merged_jel, 'top10', N, poly = 2)


