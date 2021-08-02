# New Story - Mexico TAM

### Prerequisites
If you feel comfortable, feel free to fork/clone this repository. If not, easiest thing is to download as a zip (green "Code" button with download image here on github). 

Python 3 must be installed to run analysis, see https://www.python.org/downloads/. The following python packages must be installed
- matplotlib
- openpyxl
- pandas
- requests
See https://docs.python.org/3/installing/index.html for documentation on installing python packages.

### Inputs
The script lives in a directory, and needs one two inputs. Essentially, what it does is
1. Read the "diccionario" file to determine what are the indicators of inadequate housing
2. Parse the sample survey data, crunch some numbers, and spit out a couple simple histograms and csvs

The two inputs to the script come from this page: (INEGI Massive Download)[http://en.www.inegi.org.mx/app/descarga/?p=3001&ag=00#inv] under MicroData -> Programs -> Population and Housing Unit -> Sample. The first is the actual data. This is a huge zipped folder of csvs (under Databases -> Estados Unidos Mexicanos) and is not checked into this repository because of its size. So you can either download it yourself and unzip it in this folder, or if you just want to run the script it'll do that for you (just allow 10ish minutes for the download to occur, in addition to the 10ish minutes to run the script. It'll print out text before and after download).

The diccionario excel file is a slightly modified of the "Description of the database" file of the extended sample questionnaire. It has three tabs for the three different sections of the questionnaire, Viviendas, Personas, and Migrantes. The script only uses the Viviendas portion for now. I have added an additional column to this file, "Indicator". Essentially, this is a simple way to, in a binary fashion, mark specific columns as indicators of inadequate housing and make changes to what the script is using to classify housing without making modifications to the script itself. 

### Outputs
The script has effectively three outputs (examples of which are checked in to this repository):
1. summary.csv - the high-level data you want: TAM estimate based on inputs and some numbers that went into determining that value
2. histograms - two png files with the same histogram: income distribution for households below 40k pesos per month, overlayed with the same distribution for households living in inadequate conditions. TAM is highlighted in a different color. One of the files has percentage (of households in sample) on the y axis, while the other has estimated number of million households in Mexico on the y axis. The only difference is the axes, the graphs themselves are the same.
3. count_by_indicator.csv - for the chosen indicators of inadequate housing, see how many in the sample (and what percentage) had that indicator. Same data is shown for households in target income bracket.

### Making changes
The easiest way to make changes to the analysis is modifying the excel file to mark certain columns as indicators or not. Empty cells or cells with "FALSE" (or "false", etc) will not be read as indicators. Cells with "TRUE" will be read as indicators. For a sanity check, the script will print out what's being used as an indicator, as well as output the count_by_indicator file.

There's also currently one "custom" indicator - that is, an indicator that's not a simple binary on a column value. Rachel requested that >2.5 people per bedroom be used. It's very difficult to define something like that in excel, and quite easy to do in python. So in the script, there is a variable called "custom_indicators", which is a dictionary. Keys are labels (get put in count_by_indicator file), while values are functions that take a row (of the database file) and return either TRUE or FALSE. More custom indicators could be added.

Longer term, it might also be worth moving away from this binary system. Rachel linked work from a previous cohort on defining a sort of rating system for a specific household, and something similar here would likely be more useful than just marking any house with at least one indicator as "inadequate". A function that takes a household/row and generates a score would be a more sophisticated way to classify households and would be an improvement over the current approach.