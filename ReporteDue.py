# Programa para calcular Los trabajos subidos a Produccion por Vendedor, Due-date calculado, 
# Diferencia Due-date Calculado vs. Due-Date en Sistema de Produccion
# Junio 5/ 2023

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from openpyxl import load_workbook
import sys

directory = os.getcwd()

dfs = []
nombre_nueva_hoja = 'Due_Date'
datos = pd.read_excel(r'DuedateRutas_Reporte.xlsx',sheet_name='Semanal')
datos.info()
indexDeleted = datos[(datos['Job Status'].isin(['Voided', 'New'])) | (datos['Diferencia DueDates'].isnull()) | (datos['Part Store #'].isin([20,21]))].index
datos.drop(indexDeleted,inplace=True) 
datos.to_excel(r'Revision.xlsx')

datos['Menor que 0'] = datos['Diferencia DueDates'] < 0

def crear_lista(group):
    count_true = group['Menor que 0'].sum()  # Cuenta cuántos son True
    count_false = len(group) - count_true    # Cuenta cuántos son False
    due_dates = group['Due_Date_Vendedor'].tolist()
    return [(count_true, count_false, due_dates)]

result = datos.groupby([
    'Created by (Salesperson)',
    'Customer',
    pd.Grouper(key='Created', freq='60S'),
    pd.Grouper(key='Due_Date_Calculado')
]).apply(crear_lista)


def crear_lista2(group):
    count_true = group['Menor que 0'].sum()  # Cuenta cuántos son True
    count_false = len(group) - count_true    # Cuenta cuántos son False
    return [(count_true, count_false)]

result2 = datos.groupby([
    'Created by (Salesperson)',
    'Customer',
    pd.Grouper(key='Created', freq='1T'),
    pd.Grouper(key='Due_Date_Calculado')
]).apply(crear_lista2)

salesperson_counts = datos.groupby('Created by (Salesperson)')['Menor que 0'].value_counts().unstack(fill_value=0)
salesperson_counts.reset_index(inplace=True)
salesperson_counts.rename(columns={True: 'True Salesperson', False: 'False Salesperson'}, inplace=True)

result2 = result2.to_frame(name='Counts')
result2 = result2.merge(salesperson_counts, how='left', left_on='Created by (Salesperson)', right_on='Created by (Salesperson)')

def crear_lista3(group):
    count_true = group['Menor que 0'].sum()  # Cuenta cuántos son True
    count_false = len(group) - count_true    # Cuenta cuántos son False
    
    rows = [
        (group.name[0], group.name[1], group.name[2], count_true, True),
        (group.name[0], group.name[1], group.name[2], count_false, False)
    ]
    
    return pd.DataFrame(rows, columns=['Created by (Salesperson)', 'Customer', 'Created', 'Count', 'Menor que 0'])

result3 = datos.groupby([
    'Created by (Salesperson)',
    'Customer',
    pd.Grouper(key='Created', freq='1T'),
    pd.Grouper(key='Due_Date_Calculado')  # Agrupa por hora con diferencia de 1 minuto
]).apply(crear_lista3)
result3.reset_index(drop=True, inplace=True)
true_rows = result3[result3['Menor que 0']]
false_rows = result3[result3['Menor que 0']==0]
salesperson_counts = true_rows.groupby('Created by (Salesperson)')['Count'].sum().reset_index()
salesperson_countsfalse = false_rows.groupby('Created by (Salesperson)')['Count'].sum().reset_index()
result3 = pd.concat([result3, salesperson_counts,salesperson_countsfalse], ignore_index=True, sort=False)
result3.sort_values(by=['Created by (Salesperson)', 'Created'], inplace=True)
resultor = datos.groupby(['Created by (Salesperson)', 'Menor que 0']).size().reset_index(name='Count')

os.remove(r'DueDate_Report.xlsx') 
archivo_excel = 'DueDate_Report.xlsx'
writer = pd.ExcelWriter(archivo_excel)
df1 = result.to_frame()

with pd.ExcelWriter(archivo_excel) as writer: 
    result.to_excel(writer, sheet_name='DueDate_Ordenes',startrow= 1, startcol=0 )
    resultor.to_excel(writer, sheet_name='DueDate_Ordenes',startrow= 1, startcol=len(df1.columns)+6 )
    result2.to_excel(writer,sheet_name='DueDate_Ordenes',startrow= 1, startcol=len(df1.columns)+len(resultor.columns)+12 )
    result3.to_excel(writer,sheet_name='DueDate_Ordenes',startrow= 1, startcol=len(df1.columns)+len(resultor.columns)+len(result2.columns)+18 )