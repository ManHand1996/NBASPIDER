"""streamlit
"""
import streamlit as st
import pandas as pd
import time

import subprocess
import streamlit.components.v1 as components
from threading import Thread
from widget_callback import add_schedule
from widgets import schedule_modal
from utils import sp_client
from datetime import datetime
from apis import get_jobs_list, cancel_job
from queue import Queue
# from utils import sp_client
# from widgets import modal

# st.set_page_config(layout="wide")


# df = pd.DataFrame(data=[job for job in sp_client.jobs('nba_crawler')])
# print(df)
# def list_jobs():
#     st.title("Spider Jobs:")
#     headers = ['project', 'spider', 'start_time', 'end_time',
#                'log_url', 'items_url']
    
    
#     placeholder = st.empty()
#     sch_btn = st.button('schedule')
#     # schedule btn callback
#     add_schedule(sch_btn)
    
#         # with placeholder.container():
#     end_job = False       
#     while not end_job:
#         with placeholder.container():
#             df = get_jobs_list()
#             if len(df[~df['end_time'].notna()]) == 0:
#                 end_job = True
#             st.dataframe(df, hide_index=True, column_config={
#                 'status': st.column_config.ProgressColumn('status', format='%f%%', min_value=0, max_value=100)
#             })
#             time.sleep(1.5)
#             # option = st.selectbox(
#             # 'Which number do you like best?',df['id']
#             # )

#             # 'You selected: ', option
#             # return df
            
#             # st.write(st_df)
JOBS_DF = None


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True), 
                       'id': None,
                'status': st.column_config.ProgressColumn('status', format='%f%%', min_value=0, max_value=100)
                       },
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def loop_jobs():
    global JOBS_DF
    placeholder = st.empty()
    selected_jobid = ''
    end_job = False
    while not end_job:
        with placeholder.container():
            JOBS_DF = get_jobs_list()
            st.dataframe(JOBS_DF,
                hide_index=True,
                column_config={
                            # 'id': None,
                        'process': st.column_config.ProgressColumn('process', format='%f%%', min_value=0, max_value=100)
                            },
                # disabled=df.columns,
            )
            col = placeholder.columns([0.1])
            
            for i, job_id in enumerate(JOBS_DF['id']):
                with col[0]:
                    st.button('cancel')

            # st.button('cancel', on_click=cancel_job, args=(st.selectbox('spider list',options=JOBS_DF['id'].to_list()),))
            
            # selected_jobid = 
            
            # if len(df[~df['end_time'].notna()]) == 0:
            #     end_job = True
            
            # queue_data.put(selected_raw)
        time.sleep(1.5)
        # col.clear()

def list_jobs():
    loop_thread = Thread(target=loop_jobs)
    st.title("Spider Jobs:")
    # sch_btn = st.button('schedule')
    # schedule btn callback
    job_cols = st.columns(4)
    submit_col = st.columns([0.2,0.2])
    with job_cols[0]:
        
        project = st.selectbox('project', options=sp_client.projects())
    with job_cols[1]:
        if project:
            spider = st.selectbox('spiders', options=sp_client.spiders(project))
    with job_cols[2]:
        season_from = st.selectbox('season_from', options=[i for i in range(datetime.today().year, 1970, -1)])
    with job_cols[3]:
        season_to = st.selectbox('season_to', options=[i for i in range(datetime.today().year, 1970, -1)])
    with submit_col[0]:
        get_schedule = st.toggle('get season schedule', False)
    with submit_col[1]:
        submit_btn = st.button('submit')
        if submit_btn:
            s_args = {'season_from': season_from, 
                    'season_to': season_to,
                    'get_schedule': get_schedule
                    }
            sp_client.schedule(project, spider, s_args)
    loop_thread.run()
    loop_thread.join()


def home():
    option = st.selectbox('type', options=['', 'schedule', 'history'])
    save_btn = st.button('save to db')
    if save_btn:
        content = subprocess.Popen(f'python store_db.py {option}', shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        st.write(content)

if __name__ == '__main__':
    # list_jobs()
    home()
    