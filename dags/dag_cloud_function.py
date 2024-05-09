from airflow import models
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator

import os
import google.auth
from google.auth.transport.requests import Request
import requests
import google.auth.transport.requests
from  google.oauth2.id_token import fetch_id_token

class GcpFunction:
    def __init__(self, function_url) -> None:
        self.function_url = function_url
    
    def call(self, payload):
        token = self._get_id_token()

        #Set up the headers with the ID token
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'  # Set the content type as needed
        }

        try:
          resp = requests.post(self.function_url, json=payload, headers=headers)
          resp.raise_for_status()
        #   print(resp.status_code)
        #   print(resp.json)
          print('Request Done With Sucess')
        except Exception as ex:
            print(f"GcpFunction.call {self.function_url} failed. {ex}")
            raise

        try:
            return resp.json()
        except ValueError:
            # If the response is not valid JSON, return the response content as a string
            return resp.text

    def _get_id_token(self):
        credentials, _ = google.auth.default()
        token_req = Request()
        credentials.refresh(token_req)
        
        # If running locally, will find id_token on credentials object, otherwise need to call fetch_id_token.
        id_token = credentials.id_token if hasattr(credentials, 'id_token') else fetch_id_token(token_req, self.function_url)

        return id_token

def call_cloud_function():
    project_id  = "enduring-branch-413218"
    region = "us-central1"
    payload = {}
    function_id = 'function-google-drive-terraform'
    function_url = f"https://{region}-{project_id}.cloudfunctions.net/{function_id}"
    cloud_function = GcpFunction(function_url=function_url)
    chamada = cloud_function.call(payload)
    print(chamada)
    return chamada

with models.DAG(
    'Cloud_Functions',
    schedule_interval=None,
    start_date = days_ago(2),
    catchup=False,
) as dag_cloud_function:
    invoke_cloud_function = PythonOperator(
        task_id="INVOKE_CLOUD_FUNCTION",
        python_callable=call_cloud_function
    )
    invoke_cloud_function