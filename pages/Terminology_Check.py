import streamlit as st
import zipfile
from io import BytesIO
import pandas as pd
from collections import defaultdict
import re

CHECK_TYPE_1 = 1
CHECK_TYPE_2 = 2
CHECK_TYPE_ERROR = 0

def save_upload_file(uploaded_file):
    if uploaded_file.name.endswith('.zip'):
        # 使用BytesIO读取上传的ZIP文件
        bytes_data = uploaded_file.read()
        zip_stream = BytesIO(bytes_data)
        all_dataframes = []
        with zipfile.ZipFile(zip_stream, 'r') as zipped_file:
            # 获取压缩包内所有文件的列表
            zipped_file_namelist = zipped_file.namelist()
            excel_files = [f for f in zipped_file_namelist if f.endswith('.xlsx') or f.endswith('.xls')]
            for excel_file_name in excel_files:
                with zipped_file.open(excel_file_name) as excel_file:
                    # 读取Excel文件中的每个工作表
                    xls = pd.ExcelFile(excel_file)
                    for sheet_name in xls.sheet_names:
                        # 读取工作表内容到DataFrame
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        # 将读取的DataFrame添加到列表中
                        all_dataframes.append(df)

        # 合并所有DataFrame成一个单一的DataFrame
        merged_dataframe = pd.concat(all_dataframes, ignore_index=True)
        return merged_dataframe
    elif uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
        df_list = []
        xls = pd.ExcelFile(uploaded_file)
        for sheet_name in xls.sheet_names:
            # 读取工作表内容到DataFrame
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
            # 将读取的DataFrame添加到列表中
            df_list.append(df)
        merged_dataframe = pd.concat(df_list, ignore_index=True)
        return merged_dataframe
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        return df

def deal_df(df):
    if df.iloc[3,0] == '#':
        df = df.drop(df.index[:3])
        pattern = r"\n\{\[@.*?@\]\}"
        df.iloc[0] = df.iloc[0].replace(pattern, "", regex=True)
        df.columns = df.iloc[0]
        df = df[1:]
        df.reset_index(drop=True, inplace=True)
    return df

def get_check_type(column_name):
    check_type1 = ['English', 'German', 'Spanish', 'French', 'Indonesian', 'Italian', 'Korean', 'Portuguese', 'Vietnamese', 'Turkish', 'Russian']
    check_type2 = ['Chinese', 'Japanese', 'Thai']
    column_name = re.sub(r'\s*\(.*?\)', '', column_name)
    if column_name in check_type1:
        return CHECK_TYPE_1
    elif column_name in check_type2:
        return CHECK_TYPE_2
    else:
        return CHECK_TYPE_ERROR

def load_glossaries(df, source_col_name, target_col_name):
    df = df.dropna(subset=[source_col_name, target_col_name])
    # 将原文和译文列转为字符串类型
    df[source_col_name] = df[source_col_name].astype(str)
    df[target_col_name] = df[target_col_name].astype(str)
    # 去除原文列和译文列完全重复的行
    df = df.drop_duplicates(subset=[source_col_name, target_col_name])
    glossary_dict = defaultdict(list)
    for index, row in df.iterrows():
        source_term = row[source_col_name]
        target_term = row[target_col_name]
        glossary_dict[source_term].append(target_term)
    return glossary_dict

def process_term_check(source_term, target_terms, target_text, check_results, check_results_case, check_type):
    if check_type == CHECK_TYPE_1:
        if not any(re.search(r'\b{}\b'.format(re.escape(target_term)), target_text) for target_term in target_terms):
            expected_translations = "', '".join(target_terms)
            check_results.append(f"'{source_term}' 的译文应为以下的一项： '{expected_translations}'")
            if check_results_case == '' and any(re.search(r'\b{}\b'.format(re.escape(target_term.lower())), target_text.lower()) for target_term in target_terms):
                check_results_case = '大小写'
    elif check_type == CHECK_TYPE_2:
        if not any(target_term in target_text for target_term in target_terms):
            expected_translations = "', '".join(target_terms)
            check_results.append(f"'{source_term}' 的译文应为以下的一项： '{expected_translations}'")
    return check_results, check_results_case

def check_glossaries(df, source_col_name, target_col_name, glossary_dict):
    results_col_name = f'{target_col_name}术语检查'
    results_col_name_case = f'{target_col_name}术语检查_大小写'
    df[results_col_name] = ''
    df[results_col_name_case] = ''
    # 判断语种使用的检测类型
    source_check_type = get_check_type(source_col_name)
    target_check_type = get_check_type(target_col_name)
    for index, row in df.iterrows():
        check_results = []
        check_results_case = ''
        source_text = str(row[source_col_name])
        target_text = str(row[target_col_name])
        if source_check_type == CHECK_TYPE_ERROR or target_check_type == CHECK_TYPE_ERROR:
            raise ValueError('语种信息出错，请联系支撑组！')
        if source_check_type == CHECK_TYPE_1:
            for source_term, target_terms in glossary_dict.items():
                if re.search(r'\b{}\b'.format(re.escape(source_term.lower())), source_text.lower()) is not None:
                    check_results, check_results_case = process_term_check(
                        source_term, target_terms, target_text, check_results, check_results_case, target_check_type
                    )
        elif source_check_type == CHECK_TYPE_2:
            for source_term, target_terms in glossary_dict.items():
                if source_term in source_text:
                    check_results, check_results_case = process_term_check(
                        source_term, target_terms, target_text, check_results, check_results_case, target_check_type
                    )
        df.at[index, results_col_name] = '\n'.join(check_results)
        if check_results_case:
            df.at[index, results_col_name_case] = check_results_case
    return df

# 设置页面标题
st.title('术语检查')

# 创建一个文件上传器
terminology_file = st.file_uploader("请上传术语表文件", type=["xlsx", "xls", "csv", "zip"])
if terminology_file:
    terminology_df = save_upload_file(terminology_file)
    # 显示结果
    # st.write("术语表数据：")
    # st.write(terminology_df)
    if not terminology_df.empty:
        term_df_col1, term_df_col2 = st.columns(2)
        with term_df_col1:
            terminology_source_name = st.selectbox('请选择术语表原文列', terminology_df.columns)
        with term_df_col2:
            terminology_target_name = st.selectbox('请选择术语表译文列', terminology_df.columns)
        check_file = st.file_uploader('请上传检测文件', type=['xlsx', 'xls', 'csv'])
        if check_file:
            check_df = save_upload_file(check_file)
            check_df = deal_df(check_df)
            st.write(check_df)
            check_df_col1, check_df_col2 = st.columns(2)
            with check_df_col1:
                check_source_name = st.selectbox('请选择检测文件原文列', check_df.columns)
            with check_df_col2:
                check_target_name = st.selectbox('请选择术语表译文列', check_df.columns)
            check_btn_col1, check_btn_col2, check_btn_col3 = st.columns(3)
            with check_btn_col2:
                check_btn = st.button('执行术语检测')
            if check_btn:
                # 抽取术语表
                glossary = load_glossaries(terminology_df, terminology_source_name, terminology_target_name)
                # 判断语种使用那种方法进行检测
                # check_type = get_check_type(check_target_name)
                # if check_type == CHECK_TYPE_ERROR:
                #     raise ValueError('暂不支持该语种，请联系支撑组！')
                # else:
                result_df = check_glossaries(check_df, check_source_name, check_target_name, glossary)
                st.write('术语检查成功，请下载csv文件到本地粘贴结果！')
                st.write(result_df)
                    