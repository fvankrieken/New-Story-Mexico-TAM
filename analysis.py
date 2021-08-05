import os
import requests
import datetime
import zipfile
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
from matplotlib.ticker import PercentFormatter

diccionario_file = 'diccionario_cuestionario_ampliado_cpv2020.xlsx'
mexico_folder = 'Censo2020_CA_eum_csv'
personas_file = 'Personas00.csv'
viviendas_file = 'Viviendas00.csv'
inegi_zip_url = 'http://en.www.inegi.org.mx/contenidos/programas/ccpv/2020/microdatos/Censo2020_CA_eum_csv.zip'

lower_income_limit = 5000 ## monthly, pesos
upper_income_limit = 10000
upper_income_limit_for_plot = 40000

histogram_bins = np.floor(upper_income_limit_for_plot/1000.0)
tam_bins = np.floor(upper_income_limit-lower_income_limit/1000.0)

## custom indicators - anything that involves multiple columns need to live here. Define as functions on row here
## '{label}': lambda r: {function that returns true or false}
custom_indicators = {
    'NUMPERS/CUADORM > 2.5': lambda r: r['NUMPERS']/r['CUADORM'] > 2.5
}

if not os.path.exists(diccionario_file): 
    print('Missing file: diccionario_cuestionario_ampliado_cpv2020.xlsx must be present in current directory')
    exit()

if not os.path.exists(os.path.join(mexico_folder, viviendas_file)):
    print('No data found in Censo2020_CA_eum_csv folder (or no folder found)\nAttempting to download now (allow a few minutes), starting at ' + str(datetime.datetime.now().time))
    try:
        save_path = 'Censo2020_CA_eum_csv.zip'
        r = requests.get(inegi_zip_url, stream=True)
        
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(mexico_folder)  
    except Exception as e:
        print("Downloading failed at " + str(datetime.datetime.now().time) + ":\n" + str(e))
        print('Exiting')
        exit()
    else: 
        print('Download succeeded at ' + str(datetime.datetime.now().time))

total_population_mexico = 128932753 # 2020 estimate

indicators = pd.read_excel(diccionario_file, sheet_name='VIVIENDAS', skiprows=4, usecols=[3, 6, 9], converters={2:bool})
indicators = indicators.rename(columns={'Rango válido': 'Value', 'Mnemónico': 'Header'})
indicators['Header'] = indicators['Header'].fillna(method='ffill')
indicators = indicators[indicators['Value'].apply(lambda r: not '{' in str(r))].dropna()

indicators = indicators[indicators['Indicator']].drop(columns='Indicator').reset_index(drop=True)
indicators['Value'] = indicators['Value'].apply(int)
qualifications = indicators.groupby(['Header'])['Value'].apply(list).to_dict()

print("Parsed Indicators:")
print(indicators)

mexico_viviendas = pd.read_csv(os.path.join(mexico_folder, viviendas_file))
 
total_viviendas_in_sample = len(mexico_viviendas)
indicators['Total Count'] = indicators.apply(lambda row: (mexico_viviendas[row['Header']] == row['Value']).sum(), axis=1)
indicators['Total Percentage'] = indicators['Total Count']/total_viviendas_in_sample

total_personas_in_sample = mexico_viviendas['NUMPERS'].sum()
people_per_household = total_personas_in_sample/total_viviendas_in_sample

total_households_mexico = int(total_population_mexico/people_per_household)

def filter(q: dict[str, list[int]] , r): 
    return any([q[key].__contains__(r[key]) for key in q]) or any([custom_indicators[f](r) for f in custom_indicators])

total_inadequate_ignore_income = mexico_viviendas.apply(lambda r:  filter(qualifications, r), axis=1).sum()
mexico_has_income_reported = mexico_viviendas[mexico_viviendas['INGTRHOG'].notna()]
del mexico_viviendas
income_plot = mexico_has_income_reported[mexico_has_income_reported['INGTRHOG'] < upper_income_limit_for_plot]
inadequate = mexico_has_income_reported.apply(lambda r:  filter(qualifications, r), axis=1)
sample_inadequate = mexico_has_income_reported[inadequate].reset_index(drop=True)
sample_inadequate_plot = sample_inadequate[sample_inadequate['INGTRHOG'] < upper_income_limit_for_plot]

tam = sample_inadequate_plot[(sample_inadequate_plot['INGTRHOG'] <= upper_income_limit) & (sample_inadequate_plot['INGTRHOG'] >= lower_income_limit)].reset_index(drop=True)

plt.hist(income_plot['INGTRHOG'], bins=histogram_bins, alpha=0.5, color='grey', weights=np.ones(len(income_plot)) / len(mexico_has_income_reported), edgecolor='white', linewidth=0.5, label='All households')
plt.hist(sample_inadequate_plot['INGTRHOG'], bins=histogram_bins, weights=np.ones(len(sample_inadequate_plot)) / len(mexico_has_income_reported), edgecolor='white', linewidth=0.5, label='Households with inadequate housing')
plt.hist(tam['INGTRHOG'], bins=tam_bins, color='g', weights=np.ones(len(tam)) / len(mexico_has_income_reported), edgecolor='white', linewidth=0.5, label='TAM')

plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
plt.title("Income breakdown by household in sample")
plt.grid()
plt.legend()
plt.ylabel("Percentage of sample")
plt.xlabel("Monthly income, pesos")

plt.savefig("histogram_percentage.png")
plt.clf()

plt.hist(income_plot['INGTRHOG'], bins=histogram_bins, alpha=0.5, color='grey', weights=np.ones(len(income_plot)) / len(mexico_has_income_reported) * total_households_mexico / 1000000, edgecolor='white', linewidth=0.5, label='All households')
plt.hist(sample_inadequate_plot['INGTRHOG'], bins=histogram_bins, weights=np.ones(len(sample_inadequate_plot)) / len(mexico_has_income_reported) * total_households_mexico / 1000000, edgecolor='white', linewidth=0.5, label='Households with inadequate housing')
plt.hist(tam['INGTRHOG'], bins=tam_bins, color='g', weights=np.ones(len(tam)) / len(mexico_has_income_reported) * total_households_mexico / 1000000, edgecolor='white', linewidth=0.5, label='TAM')

plt.title("Estimated household income distribution in Mexico")
plt.grid()
plt.legend()
plt.ylabel("Estimated millions of households")
plt.xlabel("Monthly income, pesos")

plt.savefig("histogram_total.png")

in_income_range = (mexico_has_income_reported['INGTRHOG'] > lower_income_limit) & (mexico_has_income_reported['INGTRHOG'] < upper_income_limit)

in_income_range_df = mexico_has_income_reported[in_income_range]
indicators['Count in target income'] = indicators.apply(lambda row: (in_income_range_df[row['Header']] == row['Value']).sum(), axis=1)
del in_income_range_df
indicators['Percentage in target income'] = indicators['Total Count']/in_income_range.sum()

indicators.to_csv(path_or_buf='count_by_indicator.csv', index=False)

total_inadequate = inadequate.sum()
total_in_income_range = in_income_range.sum()
both = in_income_range & inadequate
tam_sample = both.sum()
total_income_reported = len(mexico_has_income_reported.index)

personas_with_income_reported = mexico_has_income_reported['NUMPERS'].sum()
personas_in_tam = mexico_has_income_reported[both]['NUMPERS'].sum()

p = tam_sample/total_income_reported

estimate_inadequate_mexico = p * total_population_mexico

#confidence_interval = (p * (1 - p) / total_income_reported)**(1/2)*1.96
#lower_bound = estimate_inadequate_mexico - estimate_inadequate_mexico * confidence_interval
#upper_bound = estimate_inadequate_mexico + estimate_inadequate_mexico * confidence_interval

#print(lower_bound)
#print(upper_bound)

with open('summary.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['People/Households'])
    writer.writerow([])
    writer.writerow(['Sample size (people)', total_personas_in_sample])
    writer.writerow(['Sample size (households)', total_viviendas_in_sample])
    writer.writerow(['Average household size in sample', people_per_household])
    writer.writerow(['Population of Mexico', total_population_mexico])
    writer.writerow(['Estimated number of households in Mexico', total_households_mexico])
    writer.writerow([])
    writer.writerow(['Income'])
    writer.writerow([])
    writer.writerow(['Number of households in sample with income reported', total_income_reported])
    writer.writerow(['Number of households in sample in target income range', total_in_income_range])
    writer.writerow(['Percentage of households in sample in target income range', total_in_income_range/total_income_reported*100])
    writer.writerow(['Estimated total households in Mexico in target income range', total_in_income_range/total_income_reported*total_households_mexico])
    writer.writerow([])
    writer.writerow(['Housing'])
    writer.writerow([])
    writer.writerow(['Number of households in sample with inadequate housing', total_inadequate_ignore_income])
    writer.writerow(['Percentage of households in sample with inadequate housing', total_inadequate_ignore_income/total_viviendas_in_sample*100])
    writer.writerow(['Estimated total households in Mexico with inadequate housing', total_inadequate_ignore_income/total_viviendas_in_sample*total_households_mexico])
    writer.writerow([])
    writer.writerow(['TAM'])
    writer.writerow([])
    writer.writerow(['TAM size in sample, households', tam_sample])
    writer.writerow(['Percentage of households in TAM in sample', tam_sample/total_income_reported*100])
    writer.writerow(['Estimated households in TAM in Mexico', tam_sample/total_income_reported*total_households_mexico])
    writer.writerow(['TAM size in sample, people', personas_in_tam])
    writer.writerow(['Percentage of people in TAM in sample', personas_in_tam/personas_with_income_reported*100])
    writer.writerow(['Estimated people in TAM in Mexico', personas_in_tam/personas_with_income_reported*total_population_mexico])
    