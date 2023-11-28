###Programa Funcional OK Mayo 22/2023
# Programa para calcular el Due-Date de produccion diaria 

import pandas as pd
import numpy as np
import math
import xlwt
import openpyxl
import time
import xlsxwriter
import gspread
import pygsheets
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime, timedelta
from Fun_DueDateLogistica import *
import io
import os
from urllib.parse import urlparse
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from gooey import Gooey, GooeyParser

import gspread
import sys
import warnings
import gspread_dataframe as gd
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)

print("Verificando contenido del archivo .....")
file_id0 = "1F0L_aHVNNhGuV-KNnuT6nCr_X1Af3l3E" #cortes2023.xlxs
file_id1 = "15vHlzGFgi9MjxyclqmNArvheijJhLSK5" #tiempos.xls
file_id2 = "17-gj5CshmFmb-hrFm3Dh4a12P8DcR4bB" #ReporteProduccionDBresultado.xlsx
scopes = [
'https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive'
]

credentials = ServiceAccountCredentials.from_json_keyfile_name("monitor-eficiencia-3a13458926a2.json", scopes)
file = gspread.authorize(credentials)

nombre = 'DuedateRutas.xls'

@Gooey(program_name="Calculo de Due_Date de Base de datos Produccion diaria")
def parse_args():
    """ Use GooeyParser to build up the arguments we will use in our script
    Save the arguments in a default json file so that we can retrieve them
    every time we run the script.
    """
    stored_args = {}
    # get the script name without the extension & use it to build up
    # the json filename
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    args_file = "{}-args.json".format(script_name)
    # Read in the prior arguments as a dictionary
    if os.path.isfile(args_file):
        with open(args_file) as data_file:
            print("ffff",data_file)
            stored_args = json.load(data_file)
    parser = GooeyParser(description='Calculo de Due_Date de Base de datos')
    parser.add_argument('Archivo_Produccion',
                        action='store',
                        default=stored_args.get('cust_file'),
                        widget='FileChooser',
                        help='Ej. ReporteProduccionDB.xlsx')
    parser.add_argument('Directorio_de_trabajo',
                        action='store',
                        default=stored_args.get('data_directory'),
                        widget='DirChooser',
                        help="Directorio con los archivos .XLSX/.CSV ")
    args = parser.parse_args()
    # Store the values of the arguments so we have them next time we run
    with open(args_file, 'w') as data_file:
        # Using vars(args) returns the data as a dictionary
        json.dump(vars(args), data_file)
    return args

def main(Directorio_de_trabajo,ReporteProduccionDB):
  print(Directorio_de_trabajo+'\\Job no Drop Location.xlsx')
  merged_data=pd.read_excel(ReporteProduccionDB)
  print("Leyendo base de datos .....")
  print(Directorio_de_trabajo+'\\Job no Drop Location.xlsx')
  print("Borrando datos no necesarios .....")
  indexDeleted = merged_data[merged_data['Drop Location'] ==  'FOTOS-CHECKONLY'].index
  merged_data.drop(indexDeleted,inplace=True) 
  indexDeleted = merged_data[merged_data['Drop Location'] ==  'ACOMODOWC1'].index
  merged_data.drop(indexDeleted,inplace=True)
  merged_data_drop=merged_data.dropna(subset=['Drop Location'])
  print("Realizando copia de datos .....")
  dt = merged_data_drop.copy()
  print("Borrando datos nullos .....")
  merged_data = merged_data[merged_data['Drop Location'].isnull()]
  salida = Directorio_de_trabajo+'\\Job no Drop Location.xlsx'
  print("Creando archivo sin Drop Location.....")
  merged_data.to_excel(salida, index=False)
  print("Creando archivo de trabajos no encontrados.....")
  salida = Directorio_de_trabajo+'\\Job no encontrados en Produccion1.xlsx'
  dt.to_excel(salida, index=False)
  print("Creando archivo temporal.....") 
  dt.to_excel(r'temporal.xlsx', index=False)
  print("Leyendo archivo temporal.....")
  ds= pd.read_excel(r'temporal.xlsx')
  print("Removiendo archivo temporal.....")
  os.remove(r'temporal.xlsx')
  print("Iniciando procesamiento de datos.....")
  hora = 0 
  columnas=[12,16]
  nombre1 = nombre.split('.')
  nombre2 = nombre.split('_')
  nombre1 = nombre1[0] + "_Reporte.xlsx"

  # Define the Drive API client
  service = build("drive", "v3", credentials=credentials)

  # Define the URL to download the file from
  file_url = service.files().get(fileId=file_id0, fields="webContentLink").execute()["webContentLink"]
  parsed_url = urlparse(file_url)

  filename = f"cortes2023.xlsx"
  try:
      request = service.files().get_media(fileId=file_id0)
      file = io.BytesIO()
      downloader = io.BytesIO()
      downloader.write(request.execute())
      downloader.seek(0)
      with open(filename, "wb") as f:
          f.write(downloader.getbuffer())
      print(f"File downloaded as {filename}")
  except HttpError as error:
      print(f"An error occurred: {error}")

  file_url = service.files().get(fileId=file_id1, fields="webContentLink").execute()["webContentLink"]
  parsed_url = urlparse(file_url)

  filename = f"tiempos.xlsx"

  try:
      request = service.files().get_media(fileId=file_id1)
      file = io.BytesIO()
      downloader = io.BytesIO()
      downloader.write(request.execute())
      downloader.seek(0)
      with open(filename, "wb") as f:
          f.write(downloader.getbuffer())
      print(f"File downloaded as {filename}")
  except HttpError as error:
      print(f"An error occurred: {error}")    

  print("Leyendo archivos de Tiempos y Cortes.....")
  df = pd.read_excel(r'Tiempos.xlsx')
  dc = pd.read_excel(r'Cortes2023.xlsx')
  print("Calculando due date.....")
  df1 = pd.DataFrame({
      "Job #": '',
      "Interchange":'',
      "Stock #":'',
      "Due":'',
      "Delivery Time":'',
      "Due Date Calculado":'',
      "Dias de atraso":'',
      "Conciliacion":'',
      "Diferencia DueDates":''
  }, index=["Dummy"])

  df= df.set_index('Store')
  dc = dict(dc.set_index('DIA').groupby(level = 0).\
      apply(lambda x : x.to_dict(orient= 'list')))

  ds2 = time_fix(columnas,hora,ds)

  ds2['Fecha Compromiso']=" "
  ds2['Due Date']=" "
  ds2['Dias de atraso']=" "
  ds2['Dia']= ds2['Created'].dt.dayofweek
  ds2['Dia'].mask(ds2['Dia'] == 6, 0, inplace=True)

  ds2['tiempo'] = pd.to_datetime(ds2['Created']).dt.time
  ds2['Fecha'] = pd.to_datetime(ds2['Created']).dt.date
  ds2['Conciliacion']=" "
  dscompleto= ds2.copy()

  for i in range(len(ds2)) :

      Rt =ds2['Drop Location'][i]
      St =ds2['Part Store #'][i]

      if ( pd.isna(Rt)== False):
       ds2.loc[i,'Fecha Compromiso']=df.at[St,Rt]
      
  ds2['Conciliacion'].mask(ds2['Fecha Compromiso'] == 99, 'Revisar', inplace=True)    

  def tabla(i,tiempo,c,b):
   pd.options.mode.chained_assignment = None 
   if ds2['tiempo'][i] < tiempo.time() :
          a=dc.get(ds2['Dia'][i])
          delt = a.get(c)        
          ds2['Due Date'][i]= pd.to_datetime(ds2['Fecha'][i]) + timedelta(hours = delt[0])
          
   else :
          a=dc.get(ds2['Dia'][i])
          delt = a.get(b)      

          ds2['Due Date'][i]= pd.to_datetime(ds2['Fecha'][i]) + timedelta(hours = delt[0])
          
  def tabla1(i,tiempo,c,b):
   if ds2['tiempo'][i] < tiempo.time() :
          ds2['Due Date'][i]= pd.to_datetime(ds2['Fecha'][i]) + timedelta(hours = 0)     
   else :      
          ds2['Due Date'][i]= pd.to_datetime(ds2['Fecha'][i]) + timedelta(hours = 0)
          
  tiempo1 = datetime(2022,1,1,12,31,00) # asigno tiempos iniciales para comparar 12:31
  tiempo2 = datetime(2022,1,1,13,1,00) # asigno tiempos iniciales para comparar 13:01  USA Sabado
  tiempo3 = datetime(2022,1,1,14,1,00) # asigno tiempos iniciales para comparar 14:01
  tiempo4 = datetime(2022,1,1,16,1,00) # asigno tiempos iniciales para comparar 16:01
  tiempo5 = datetime(2022,1,1,17,1,00) # asigno tiempos iniciales para comparar 17:01  Todas las tiendas cierre 
  tiempo6 = datetime(2022,1,1,15,1,00) # asigno tiempos iniciales para comparar 15:01 Economy,Texas Sabado

  for i in range(len(ds2)):
   if ds2['Fecha Compromiso'][i] != 99:
       if ds2['Dia'][i] in range(0,6) :   
        if ds2['Fecha Compromiso'][i] == 1 and ds2['Dia'][i]==5: 
          tabla(i,tiempo2,'1.2','1.3')
        elif ds2['Fecha Compromiso'][i] == 1:
          tabla(i,tiempo4,1,'1.1')     
        if ds2['Fecha Compromiso'][i] == 2 and ds2['Dia'][i]==5: 
          tabla(i,tiempo2,'2.2','2.3')
        elif ds2['Fecha Compromiso'][i] == 2:  
          tabla(i,tiempo4,2,'2.1')
        if ds2['Fecha Compromiso'][i] == 3 and ds2['Dia'][i]==5:
          tabla(i,tiempo2,'3.2','3.3')
        elif ds2['Fecha Compromiso'][i] == 3:
          tabla(i,tiempo4,3,'3.1')      
        if ds2['Fecha Compromiso'][i] == 4: 
          tabla(i,tiempo3,4,'4.1')     
        if ds2['Fecha Compromiso'][i] == 5:    
          tabla(i,tiempo1,5,'5.1')  
        if ds2['Fecha Compromiso'][i] == 6:    
          tabla(i,tiempo4,6,'6.1')         
        if ds2['Fecha Compromiso'][i] == 7:    
          tabla(i,tiempo3,7,'7.1')  
        if ds2['Fecha Compromiso'][i] == 8:    
          tabla(i,tiempo1,8,'8.1')
        if ds2['Fecha Compromiso'][i] == 9:    
          tabla(i,tiempo4,9,'9.1')
        if ds2['Fecha Compromiso'][i] == 10:  
          tabla(i,tiempo4,10,'10.1')
        if ds2['Fecha Compromiso'][i] == 11: 
          tabla(i,tiempo4,11,'11.1') 
        if ds2['Fecha Compromiso'][i] == 12:    
          tabla(i,tiempo1,12,'12.1')
        if ds2['Fecha Compromiso'][i] == 13:
          tabla(i,tiempo4,13,'13.1')
        if ds2['Fecha Compromiso'][i] == 14:    
          tabla(i,tiempo3,14,'14.1')
        if ds2['Fecha Compromiso'][i] == 15:    
          tabla(i,tiempo1,15,'15.1')
        if ds2['Fecha Compromiso'][i] == 16:    
          tabla(i,tiempo4,16,'16.1')  

        if ds2['Fecha Compromiso'][i] == 17 and ds2['Dia'][i]==5: 
          tabla(i,tiempo3,'17.2','17.3')     
        elif ds2['Fecha Compromiso'][i] == 17: 
          tabla(i,tiempo5,17,'17.1') 
        if ds2['Fecha Compromiso'][i] == 18 and ds2['Dia'][i]==5:
          tabla(i,tiempo6,'18.2','18.3')           
        elif ds2['Fecha Compromiso'][i] == 18:     
          tabla(i,tiempo5,18,'18.1')
        if ds2['Fecha Compromiso'][i] == 19 and ds2['Dia'][i]==5: 
          tabla(i,tiempo2,'19.2','19.3')   
        elif ds2['Fecha Compromiso'][i] == 19:   
          tabla(i,tiempo5,19,'19.1') 
        if ds2['Fecha Compromiso'][i] == 20 and ds2['Dia'][i]==5: 
          tabla(i,tiempo6,'20.2','20.3')    
        elif ds2['Fecha Compromiso'][i] == 20:   
          tabla(i,tiempo5,20,'20.1')        
              
   elif ds2['Fecha Compromiso'][i] == 99: 
       tabla1(i,tiempo4,1,'1.1')

  ds2['Due Date'] = pd.to_datetime(ds2['Due Date']).dt.date
  ds2['temp1'] = pd.to_datetime(ds2['Pulled Finished']).dt.date
  ds2['Due'] = pd.to_datetime(ds2['Due']).dt.date
  
  ds2['Diferencia DueDates']= ds2['Due'] - ds2['Due Date']
  ds2['Dias de atraso']= ds2['temp1'] - ds2['Due Date']
  del ds2["Dia"]
  del ds2['tiempo']
  del ds2['Fecha']
  del ds2['temp1']
  del ds2['Fecha Compromiso']
  df1.to_excel("df.xlsx", index=False)
  ds2 = pd.concat([ds2, df1], axis=1)

  del ds2['Due Date Calculado']

  ds2 = ds2.rename(columns={'Due': 'Due_Date_Vendedor', 'Due Date': 'Due_Date_Calculado'})
  salida = Directorio_de_trabajo+'\\'+nombre1
  writer = pd.ExcelWriter(salida, engine='xlsxwriter')
  print("Creando archivo", nombre1)
  ds2.to_excel(writer, sheet_name='Due Date BD',header=True, index = False)

  while True:
      try:
          writer.close()
      except xlsxwriter.exceptions.FileCreateError as e:
          decision = input("Exception caught in workbook.close(): %s\n"
                           "Please close the file if it is open in Excel.\n"
                           "Try to write file again? [Y/n]: " % e)
          if decision != 'n':
              continue

      break

  insertRow = ["","","","","","","","","","","","","","","","","","","","","","","","","","","",]

if __name__ == '__main__':
  conf = parse_args()
  #main(conf.Directorio_de_trabajo,conf.Archivo_Produccion,conf.Archivo_Rutas)
  main(conf.Directorio_de_trabajo,conf.Archivo_Produccion)