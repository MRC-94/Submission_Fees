clear all
do path

program define clean_data // Generates some variables needed for regression + moves to zero the -1, to create the donut in regression
	gen after = 0
	replace after = 1 if months_from_intro>=0

	encode journal, gen(journal_num)

	gen months_from_intro_original = months_from_intro

	gen after_interaction = after*months_from_intro

	replace months_from_intro = months_from_intro + 1 if months_from_intro<0

	gen months_from_intro_sq = months_from_intro*months_from_intro

	gen months_from_intro_cube = months_from_intro*months_from_intro*months_from_intro
end

program define main_reg
	args outcome title
	// No FEs
	eststo clear
	reghdfe `outcome' after months_from_intro after_interaction if months_from_intro<=18 & months_from_intro>=-18 & months_from_intro != 0, cluster(journal_num#months_from_intro)
	eststo
	estadd local bandwidth "18 Months"
	estadd local fe "No"
	estadd local pol "1"
	
	// Full Specificatiom (18 months)
	reghdfe `outcome' after months_from_intro after_interaction if months_from_intro<=18 & months_from_intro>=-18 & months_from_intro != 0, a(journal_num sub_month) cluster(journal_num#months_from_intro)
	eststo
	estadd local bandwidth "18 Months"
	estadd local fe "Yes"
	estadd local pol "1"
	
	// 12 Months
	reghdfe `outcome' after months_from_intro after_interaction if months_from_intro<=12 & months_from_intro>=-12 & months_from_intro != 0, a(journal_num sub_month) cluster(journal_num#months_from_intro)
	eststo
	estadd local bandwidth "12 Months"
	estadd local fe "Yes"
	estadd local pol "1"
	
	// 24 Months
	reghdfe `outcome' after months_from_intro after_interaction if months_from_intro<=24 & months_from_intro>=-24 & months_from_intro != 0, a(journal_num sub_month) cluster(journal_num#months_from_intro)
	eststo
	estadd local bandwidth "24 Months"
	estadd local fe "Yes"
	estadd local pol "1"
	
	// Polynomial order 0
	reghdfe `outcome' after if months_from_intro<=18 & months_from_intro>=-18 & months_from_intro != 0, a(journal_num sub_month) cluster(journal_num#months_from_intro)
	eststo
	estadd local bandwidth "18 Months"
	estadd local fe "Yes"
	estadd local pol "0"
	
	// Polynomial order 2
	reghdfe `outcome' after months_from_intro after_interaction after##c.months_from_intro_sq if months_from_intro<=18 & months_from_intro>=-18 & months_from_intro != 0, a(journal_num sub_month) cluster(journal_num#months_from_intro)
	eststo
	estadd local bandwidth "18 Months"
	estadd local fe "Yes"
	estadd local pol "2"

	esttab using "$path\Results\Tables\\`title'.txt", replace keep(after) ///
	star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) nomtitles label stats(bandwidth pol fe N, label("Bandwidth" "Pol. Order" "Month & Journal FEs" "Observations" ) fmt(%11.0gc))

	esttab using "$path\Results\Tables\\`title'.tex", replace keep(after) ///
	star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) nomtitles label stats(bandwidth pol fe N, label("Bandwidth" "Pol. Order" "Month \& Journal FEs" "Observations" ) fmt(%11.0gc))
end

// Authors seniority (years from phd completion)
use "$path\Data\Cleaned_Datasets\merged_phd_year.dta", clear

clean_data

main_reg seniority_sub "phd_year"

// Authors seniority (number of publications in journal)
use "$path\Data\Cleaned_Datasets\merged_n_pub.dta", clear

clean_data

main_reg n_pub "n_pub"

// JEL codes
use "$path\Data\Cleaned_Datasets\merged_jel.dta", clear

clean_data

main_reg top10 "top10"

// Journal Quality
use "$path\Data\Cleaned_Datasets\merged_n_cit.dta", clear

clean_data

// N. pages
main_reg n_pages "n_pages"
// N. citattions
main_reg citations "citations"

// Ranking
use "$path\Data\Cleaned_Datasets\merged_inst.dta", clear

clean_data

main_reg rank "institution"

// N. authors
use "$path\Data\Cleaned_Datasets\n_auth.dta", clear

clean_data
rename c n_auth // Renaming variable of interest

main_reg n_auth "n_auth"












