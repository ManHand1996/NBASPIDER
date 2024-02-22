import streamlit as st
import streamlit.components.v1 as components
from streamlit_modal import Modal
# from widgets import schedule_modal
from utils import sp_client
from datetime import datetime


def add_schedule(btn):
    empty_p = st.empty()
    # with empty_p.container():
    schedule_modal = Modal(
        "Demo Modal", 
        key="demo-modal",
        # Optional
        padding=10,    # default value
        max_width=544  # default value
    )

    
    if btn:
        schedule_modal.open()
    # print('FUCKU')
    if schedule_modal.is_open():
        with schedule_modal.container():
            st.write("Text goes here")
            schedule_form = st.form('Schedule Form', True, border=False)
            
            with schedule_form:
                project = st.selectbox('project', options=sp_client.projects())
                if project:
                    spider = st.selectbox('spiders', options=sp_client.spiders(project))
                season_from = st.selectbox('season_from', options=[i for i in range(datetime.today().year, 1970, -1)])
                season_to = st.selectbox('season_to', options=[i for i in range(datetime.today().year, 1970, -1)])
                get_schedule = st.toggle('get season schedule', False)
                
                submit_btn = st.form_submit_button("Submit")
                if submit_btn:
                    s_args = {'season_from': season_from, 
                            'season_to': season_to,
                            'get_schedule': get_schedule
                            }
                    sp_client.schedule(project, spider, s_args)
                    schedule_modal.close(True)
                    # st.rerun()
            # html_string = '''
            # <h1>HTML string in RED</h1>

            # <script language="javascript">
            #     document.querySelector("h1").style.color = "red";
            # </script>
            # '''
            # components.html(html_string)
        
        