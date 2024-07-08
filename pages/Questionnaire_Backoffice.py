import pandas as pd
import streamlit as st
from pyecharts import options as opts
from pyecharts.charts import Pie, Bar
import zipfile
import os
import io
import subprocess
from pathlib import Path
import numpy as np
from copy import copy
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
import sys
sys.path.append('utils/qb_utils')
from option_list import OptionList
from util import st_bar, st_pie, st_line,st_break_down_bar

def read_sheet():
    # 获取data目录下最新修改的文件
    data_directory = Path("pages/data")
    files = list(data_directory.glob('*'))
    print('读取文件后的文件列表', files)

    files = Path("pages/data").glob('*')
    sorted_files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    file = sorted_files[0] if sorted_files else None
    if not file:
        return
    print("file是", file.name)
    # file = os.listdir("data")[-1]
    if file.name.endswith('csv'):
        df = pd.read_csv(f"pages/data/{file.name}")
    elif file.name.endswith('xlsx') or file.name.endswith('xls'):
        df = pd.read_excel(f"pages/data/{file.name}")
    else:
        return
    print(f'data loaded form {file.name}')
    return df, file.name
def save_upload_file(upload_file):
    print(upload_file.name)
    if upload_file.name.endswith('zip'):
        with zipfile.ZipFile(upload_file, 'r') as zipped_file:
            zipped_file_namelist = zipped_file.namelist()
            csv_files = [f for f in zipped_file_namelist if f.endswith('.csv')]
            if csv_files:
                # 只保存压缩包中第一个csv文件
                csv_file_name = csv_files[0]
                with zipped_file.open(csv_file_name) as csv_file:
                    # 创建一个BytesIO对象，此对象可以被写入硬盘
                    with io.BytesIO(csv_file.read()) as data:
                        # 将数据写入硬盘
                        with open(f'pages/data/{csv_file_name}', 'wb') as f:
                            f.write(data.getvalue())         
    else:
        with open(f'pages/data/{upload_file.name}', 'wb') as f:
            f.write(upload_file.getvalue())
    upload_file.close()
    # st.write(f"上传文件已更新：{upload_file.name}")

title = st.title('通用问卷分析展示')
upload_file = st.file_uploader('将最新问卷数据放入',type=['csv','xlsx', 'xls', 'zip'])
# read_data = read_sheet()
if upload_file:
    save_upload_file(upload_file)
    # subprocess.Popen(["rerun.bat"], shell=True)
sheet_data, current_file_name = read_sheet()
st.write(f"当前读取的文件为：{current_file_name}")
selected_columns = []
with st.sidebar:
    for i, col in enumerate(sheet_data.columns):
        is_checked = st.checkbox(col)
        if is_checked:
            selected_columns.append((i,col))
# OptionList计数
options_list_num = 0
for i, label in selected_columns:
    st.markdown(f'## {label}')
    divide_option = None
    col1, col2, col3= st.columns([0.4,0.2,0.4])
    with col1:
        keys = [f'pie_btn_{i}',f'bar_btn_{i}']
        selection_box = st.selectbox('选择图表类型',['饼图','柱状图','折线图'],key=f'selection_{i}')
        if selection_box=='柱状图':
            divide_option = st.selectbox('选择基于哪一列拆分模块',['无']+list([col for col in sheet_data.columns if col != label]),key=f'divide_box_{i}')
    with col2:  
        radio_select = st.radio('是否为多选题',['否','是'],key=f'radio_{i}')
        download_btn = st.button('导出', key=f'download_btn_{i}')
    with col3:
        if radio_select=='否':
            column = sheet_data[label].dropna().value_counts().index.to_numpy().tolist()
        else:
            split = sheet_data[label].str.split(';',expand=True).stack().reset_index(drop=True)
            column = split[split != ''].dropna().value_counts().index.to_numpy().tolist()
        # options_show = st.multiselect("选择展示的选项", column)
        options_list_num = options_list_num + 1
        options_list = OptionList(column, '选择展示的选项',options_list_num)
        options_show = [t[1] for t in options_list.options if t[-1] == True]
        if divide_option and divide_option != '无':
                if radio_select=='否':
                    new_df_exp = copy(sheet_data)
                else:
                    new_df  = copy(sheet_data)
                    new_df[label] = new_df[label].str.split(';')
                    new_df_exp = new_df.explode(label)
            
                filtered_df = new_df_exp[new_df_exp[label].notnull()][[label, divide_option]]
                column = filtered_df[divide_option].dropna().value_counts().index.to_numpy().tolist()
                # st.multiselect("选择拆分列展示的选项", column)
                options_list_num = options_list_num + 1
                divide_options_list = OptionList(column, '选择拆分列展示的选项',options_list_num)
                divide_options_show = [t[1] for t in divide_options_list.options if t[-1] == True]
    if selection_box=='饼图':
        if radio_select=='否':
            chart = st_pie(sheet_data,label,options_show)
        else:
            chart = st_pie(sheet_data,label,options_show,True)
    elif selection_box=='柱状图':
        if divide_option=='无':
            if radio_select=='否':
                chart = st_bar(sheet_data,label,options_show)
            else:
                chart = st_bar(sheet_data,label,options_show,True)
        else:
            if radio_select =='否':
                chart = st_break_down_bar(sheet_data,label,options_show,divide_option,divide_options_show)
            else:
                chart = st_break_down_bar(sheet_data,label,options_show,divide_option,divide_options_show,True)
    elif selection_box=='折线图':
        chart = st_line(sheet_data,label)
    

    save_directory = "pages/images"
    base_name, extension = os.path.splitext(current_file_name)
    sub_directory = os.path.join(save_directory, base_name)
    if not os.path.exists(sub_directory):
        os.makedirs(sub_directory)
    # 导出
    if download_btn:
        if chart:
            # 检查是否需要拆分选项
            if not divide_option or divide_option == '无':
                file_name = f"{label}_【{selection_box}】.png"
            else:
                file_name = f"{label}_【{selection_box}_拆分】_{divide_option}.png"
            file_path = os.path.join(sub_directory, file_name)
            print('file_path', file_path)
            make_snapshot(snapshot, chart.render(), file_path)
            st.success(f"图表已经保存至本地目录'{sub_directory}': {file_name}")
        
  