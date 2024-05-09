import os.path
import io
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
import tempfile

from classes.google_drive import GoogleDrive
from classes.cloud_storage import CloudStorage
from classes.secret_manager import SecretManager

def main(request):
    #os.environ["GOOGLE_APPLICATION_CREDENTIALS"] =  '../gcp_account.json'

    #google_drive_folder_id = '1GCcM5adyxuJo_ayz6z7Zhze6m4U5Nu3R'

    bucket_name = "projeto-dataproc-breno"
    # folder_cloud_storage_name = 'logs_drive'
    # file_name_list_files = 'list_files.parquet'

    #Contacts
    folder_cloud_storage_contacts_name = 'contacts'
    file_name_list_files_contacts = 'list_files_contacts.parquet'
    google_drive_folder_contacts_id = '13G6rZ2Eq3qkFfQHcOIjlY8bv57m2dlku'
    #Crowdfunding
    folder_cloud_storage_crowd_name = 'crowdfunding'
    file_name_list_files_crowd = 'list_files_crowd.parquet'
    google_drive_folder_crowd_id = '1NsobUp-5kk7GVKLvYF9lOXJwW-AQGv3w'

    secret_manager = SecretManager()
    cloud_storage_connector = CloudStorage()
    temp_dir_file_parquet = tempfile.TemporaryDirectory()
    temp_dir_log_folder = tempfile.TemporaryDirectory()

    secret_token_google_drive_name = "google_drive_token"
    secret_credentials_google_drive_name = 'credentials_google_drive' 
    project_id = 'enduring-branch-413218'

    temp_dir_creds_google_drive_folder = tempfile.TemporaryDirectory()
    token_google_drive = secret_manager.access_secret_json_file(project_id, secret_token_google_drive_name )
    credentials_google_drive = secret_manager.access_secret_json_file(project_id, secret_credentials_google_drive_name)
    token_path =  f"{temp_dir_creds_google_drive_folder.name}/token.json"
    credentials_path = f"{temp_dir_creds_google_drive_folder.name}/credentials.json"
    with open(token_path, 'w') as file:
        json.dump(token_google_drive, file)
    with open(credentials_path, 'w') as file:
        json.dump(credentials_google_drive, file)

    google_drive_connector = GoogleDrive(credentials_path, token_path)

    def download_files(file_name_list_files, folder_cloud_storage_name, google_drive_folder_id):
        try:
            cloud_storage_connector.download_object(bucket_name, file_name_list_files, f"{temp_dir_file_parquet.name}/{file_name_list_files}")  
            df_files_hist = pd.read_parquet(f"{temp_dir_file_parquet.name}/{file_name_list_files}")
            date_start = df_files_hist['createdTime'].max()
            date_start = datetime.fromisoformat(date_start.replace('Z', '+00:00'))
        except:
            date_start = None 
            df_files_hist = None

        query = google_drive_connector.generate_query(folder_id = google_drive_folder_id, date_start= date_start )
        df_files = google_drive_connector.list_files(query) 
        

        if len(df_files) > 0:
            df_files_final = pd.concat([df_files_hist, df_files])
            dict_files = dict( zip( list(df_files['id']) , (list(df_files['name']))))
            for key, value in dict_files.items():
                file_byte = google_drive_connector.download_file(key, value, temp_dir_log_folder.name)
                file_path = f"{temp_dir_log_folder.name}/{value}"
                with open(file_path, 'w') as file:
                    file.write(file_byte.decode('utf-8'))
                    #json.dump(json.loads(file_byte.decode('utf-8')), file)
                cloud_storage_connector.upload_object(bucket_name, value, file_path, folder_cloud_storage_name)
            df_files_final.to_parquet(f"{temp_dir_file_parquet.name}/{file_name_list_files}")
            cloud_storage_connector.upload_object(bucket_name, file_name_list_files, f"{temp_dir_file_parquet.name}/{file_name_list_files}") 
        else:
            print('Sem Arquivos de Logs Novos')
        
    #Contacts
    download_files(file_name_list_files_contacts, folder_cloud_storage_contacts_name, google_drive_folder_contacts_id)
    #Crowdfunding
    download_files(file_name_list_files_crowd, folder_cloud_storage_crowd_name, google_drive_folder_crowd_id)

    return ('Script executed with sucess')
