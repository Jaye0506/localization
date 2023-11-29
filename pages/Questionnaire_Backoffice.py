import pandas as pd
import streamlit as st
from pyecharts import options as opts
from pyecharts.charts import Pie, Bar
import os
print(os.getcwd())
import sys
sys.path.append(os.getcwd())
from utils.utils import st_bar, st_pie, st_line,st_break_down_bar
import zipfile

import io
import subprocess

# @st.cache_data
def read_sheet():
    path = 'pages/data'
    file = os.listdir(path)[-1]
    if file.endswith('csv'):
        df = pd.read_csv(f"{path}/{file}")
    elif file.endswith('xlsx'):
        df = pd.read_excel(f"{path}/{file}")
    else:
        return
    print(f'data loaded form {file}')
    return df
def save_upload_file(upload_file):
    print(upload_file.name)
    path = 'pages/data'
    if upload_file.name.endswith('zip'):
        with zipfile.ZipFile(upload_file, 'r') as zipped_file:
            zipped_file_namelist = zipped_file.namelist()
            csv_files = [f for f in zipped_file_namelist if f.endswith('.csv')]
            if csv_files:
                csv_file_name = csv_files[0]
                with zipped_file.open(csv_file_name) as csv_file:
                    # 创建一个BytesIO对象，此对象可以被写入硬盘
                    with io.BytesIO(csv_file.read()) as data:
                        # 将数据写入硬盘
                        with open(f'{path}/{csv_file_name}', 'wb') as f:
                            f.write(data.getvalue())         
    else:
        with open(f'{path}/{upload_file.name}', 'wb') as f:
            f.write(upload_file.getvalue())
    upload_file.close()
    st.write(f"文件内容已更新：{upload_file.name}")
    st.write('等待3秒后重启')

title = st.title('通用问卷分析展示')
upload_file = st.file_uploader('将最新问卷数据放入',type=['csv','zip','xlsx'])
sheet_data = read_sheet()
if upload_file:
    save_upload_file(upload_file)
    # subprocess.Popen(["rerun.bat"], shell=True)
    sheet_data = read_sheet()

for i, label in enumerate(sheet_data.columns):
    st.markdown(f'## {label}')
    col1, col2 = st.columns([0.2,0.8])
    with col1:
        keys = [f'pie_btn_{i}',f'bar_btn_{i}']
        selection_box = st.selectbox('选择图表类型',['饼图','柱状图','折线图','隐藏'],key=f'selection_{i}')
        if selection_box=='柱状图':
            radio_select = st.radio('是否为多选题',['否','是'],key=f'radio_{i}')
    with col2:
        if selection_box=='饼图':
            st_pie(sheet_data,label)
        elif selection_box=='柱状图':
            divide_option = st.selectbox('选择基于哪一列拆分模块',['无']+list(sheet_data.columns),key=f'divide_box_{i}')
            
            if divide_option=='无':
                if radio_select=='否':
                    st_bar(sheet_data,label)
                else:
                    st_bar(sheet_data,label,True)
            else:
                if radio_select =='否':
                    st_break_down_bar(sheet_data,label,divide_option)
                else:
                    st_break_down_bar(sheet_data,label,divide_option,True)
        elif selection_box=='折线图':
            st_line(sheet_data,label)
        elif selection_box=='隐藏':
            st.write('已隐藏')


