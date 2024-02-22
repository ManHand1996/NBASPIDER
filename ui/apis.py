import re
import os
import pandas as pd
from utils import sp_client
from setting import PROJECT_NAME, PROJECT_DIR, SCRAPYD_URL
import streamlit as st
import requests
import json
from urllib.parse import urljoin

def get_process(spider, log_id):
    try:
        log_path = os.path.join(PROJECT_DIR, 'logs', PROJECT_NAME, spider, f'{log_id}.log')
        with open(log_path, 'rb') as f:
            s = f.read().decode('utf-8')
            mt = re.search(r'(?s:.*)ProcessStatus\:response\:(\d+), request\:(\d+)', s)
            mt_end = re.search(r'(?s:.*)Spider closed \(finished\)', s)
            
            if mt_end:
                return 100
            if mt:
                return round(eval(mt.groups()[0]+ '/' + mt.groups()[1]),2) * 100
            return 0
    except FileNotFoundError:
        return None

def cancel_job(job_id):
    
    requests.get(urljoin(SCRAPYD_URL, 'cancel.json'), data=json.dumps({'project': PROJECT_NAME, 'job': job_id}))

def get_jobs_list():
    
    jobs_info = sp_client.jobs('nba_crawler')
    # print(jobs_info)
    if jobs_info['status'] != 'ok':
        return None
    data_list = []
    for k,v_list in jobs_info.items():
        if k in ['finished','pending', 'running']:
            for job in v_list:
                
                if k == 'pending':
                    process = 0
                else:
                    # print(job)
                    process = get_process(job['spider'],job['id'])
                    
                job.update({'status': k, 'process': process})
                if process:
                    data_list.append(job)
    
    df = pd.DataFrame(data=data_list, 
                        columns={'id': str,'spider': str, 
                        'start_time':'datetime64ns', 
                        'end_time': 'datetime64ns',
                        'status': str,
                        'process': str}
                        )
    # df['cancel'] = "st.button('cancel job')"
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    
    # n_df = df.drop_duplicates('id',keep='last', inplace=True)
    # print(df)
    return df