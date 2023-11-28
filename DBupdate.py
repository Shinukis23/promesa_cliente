###Programa Funcional OK Mayo 23/2023
import os
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import gspread
import sys
import warnings
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import gspread_dataframe as gd
from googleapiclient.http import MediaFileUpload
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)

scopes = [
'https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive'
]
credentials = ServiceAccountCredentials.from_json_keyfile_name("monitor-eficiencia-3a13458926a2.json", scopes) #access the json key you downloaded earlier 
file = gspread.authorize(credentials)# authenticate the JSON key with gspread
directory = os.getcwd()

dfs = []

###################
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def reemplazar_archivo_en_drive(nombre_archivo, ruta_archivo):
    drive = build('drive', 'v3', credentials=credentials)
    
    # Buscar el archivo por su nombre
    carpeta_id = '117ZVbhyZ9xHtSdo7wkQ2Otww1boRC-Vc'
    archivo_list = drive.files().list(q=f"'{carpeta_id}' in parents and name='{nombre_archivo}' and trashed=false").execute().get('files', [])

    if archivo_list:
        archivo_drive = archivo_list[0]
        archivo_id = archivo_drive['id']
        
        # Actualizar el archivo con el nuevo contenido
        media_body = MediaFileUpload(ruta_archivo, resumable=True)
        archivo_actualizado = drive.files().update(fileId=archivo_id, media_body=media_body).execute()
        
        print(f"Archivo {nombre_archivo} actualizado en Google Drive")
    else:
        print(f"No se encontró el archivo {nombre_archivo} en Google Drive")

for file_name in os.listdir(directory):
    if (file_name.startswith('JobsReport_')&file_name.endswith('_Logistica.xlsx')) or (file_name.startswith('ReporteProduccionDB')&file_name.endswith('resultado.xlsx')):
        file_path = os.path.join(directory, file_name)
        print(file_path)
        data = pd.read_excel(file_path)
        indexDeleted = data[(data['Job Type'].str.upper().str.contains('CHECK'))|(data['Drop Location'].str.upper().str.contains('FOTOS'))].index
        data.drop(indexDeleted,inplace=True)
        dfs.append(data)

concatenated_data = pd.concat(dfs, ignore_index=True)
concatenated_data.sort_values("Created", inplace=True)
concatenated_data.to_excel(r'ReporteProduccionDBsort2.xlsx', index=False)


concatenated_data.drop_duplicates(subset='Job #',keep='first', inplace=True)
concatenated_data.sort_values("Created",ascending=False, inplace=True)
output_file_path = os.path.join(directory, 'ReporteProduccionDBresultado.xlsx')
concatenated_data.to_excel(output_file_path, index=False)
nombre_archivo = "ReporteProduccionDBresultado.xlsx"  # Nombre del archivo en Google Drive
ruta_archivo = "ReporteProduccionDBresultado.xlsx"  # Ruta local del nuevo archivo Excel
reemplazar_archivo_en_drive(nombre_archivo, ruta_archivo)