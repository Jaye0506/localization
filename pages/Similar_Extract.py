import streamlit as st
import zipfile
import pandas as pd
from io import BytesIO
from collections import defaultdict
import re

def save_upload_file(uploaded_file):
    if uploaded_file.name.endswith('.zip'):
        # 使用BytesIO读取上传的ZIP文件
        bytes_data = uploaded_file.read()
        zip_stream = BytesIO(bytes_data)

        with zipfile.ZipFile(zip_stream, 'r') as zipped_file:
            # 获取压缩包内所有文件的列表
            zipped_file_namelist = zipped_file.namelist()
            excel_files = [f for f in zipped_file_namelist if f.endswith('.xlsx')]
            all_dataframes = []
            for excel_file_name in excel_files:
                with zipped_file.open(excel_file_name) as excel_file:
                    # 读取Excel文件中的每个工作表
                    xls = pd.ExcelFile(excel_file)
                    for sheet_name in xls.sheet_names:
                        # 读取工作表内容到DataFrame
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        # 新增一列来表示这个DataFrame来自于哪个文件的哪个工作表
                        df['Source'] = f"{excel_file_name} || {sheet_name}"
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
            # 新增一列来表示这个DataFrame来自于哪个文件的哪个工作表
            df['Source'] = f"{uploaded_file.name} || {sheet_name}"
            # 将读取的DataFrame添加到列表中
            df_list.append(df)
        merged_dataframe = pd.concat(df_list, ignore_index=True)
        return merged_dataframe
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        return df
    
def get_patterns():
    patterns = {
        'p1':{
            'regex': '100%',
            'description': '完全重复'
        },
        'p2':{
            'regex': r'\d+',
            'description': '数字不同'
        },
        'p3':{
            'regex': r'[零一二三四五六七八九十百千万亿]+',
            'description': '中文数字不同'
        },
        'p4':{
            'regex': r'\{.+?\}',
            'description': '{}内不同'
        },
        'p5':{
            'regex': r'<[^>]+>',
            'description': '<>内不同'
        },
        'p6':{
            'regex': r'\[[^\]]+\]',
            'description': '[]内不同'
        },
    }
    return patterns

def extract_similar_text(df, source_column:str, pattern_names:list=['p1','p2','p3','p4','p5']):
    patterns = get_patterns()
    df = df.copy()
    # 移除包含 NaN 的行
    df = df.dropna(subset=[source_column])
    # 计算同质化文本的总字数
    characters_total = df[source_column].str.len().sum()
    # 标记完全重复的文本
    handle_p1 = 'p1' in pattern_names and 'p1' in patterns
    if handle_p1:
        duplicated_mask = df.duplicated(subset=[source_column], keep=False)
        df['matched_patterns'] = df.apply(lambda x: patterns['p1']['description'] if duplicated_mask[x.name] else '', axis=1)
    else:
        df['matched_patterns'] = ''
        df = df.drop_duplicates(subset=[source_column])
    # 正则替换
    def replace_and_record_patterns(text, matched_patterns):
        pattern_list = []
        if matched_patterns:
            pattern_list.append(matched_patterns)
        for pattern_name in pattern_names:
            if pattern_name in patterns:
                pattern_regex = patterns[pattern_name]['regex']
                pattern_description = patterns[pattern_name]['description']
                if pattern_name != 'p1' and matched_patterns=='' and re.search(pattern_regex, text):
                    text = re.sub(pattern_regex, f'【{pattern_name}】', text)
                    pattern_list.append(pattern_description)
        return text, ';'.join(pattern_list)
    df['replaced_text'], df['matched_patterns'] = zip(
        *df.apply(lambda row: replace_and_record_patterns(row[source_column], row['matched_patterns']), axis=1)
    )
    # 将处理后的文本进行分组，以找出重复出现的模式
    pattern_dict = defaultdict(list)
    for original_text, replaced_text in zip(df[source_column], df['replaced_text']):
        pattern_dict[replaced_text].append(original_text)

    similar_text_total = 0
    similar_text_data = pd.DataFrame()
    for replaced_text, original_texts in pattern_dict.items():
        if len(original_texts) > 1:
            # 从第二次出现的文本开始计数
            # similar_text_total += (len(original_texts) - 1) * len(replaced_text)
            similar_text_total += sum(len(text) for text in original_texts[1:])
            matching_rows = df[df[source_column].isin(original_texts)]
            # print(f"{replaced_text}:{original_texts}")
            # 将找到的行添加到新的 DataFrame 中
            similar_text_data = pd.concat([similar_text_data, matching_rows], ignore_index=True)

    # 计算同质化文本率
    similar_text_rate = round((similar_text_total / characters_total) * 100, 2)
    
    print(f"同质化文本字数:{similar_text_total}\n原文列总字数:{characters_total}\n同质化文本率:{similar_text_rate}%", )
    return similar_text_data, characters_total, similar_text_total, similar_text_rate


# 设置页面标题
st.title('同质化文本抽取')

# 创建一个文件上传器
uploaded_file = st.file_uploader("可选择excel、csv或zip文件", type=["xlsx", "xls", "csv", "zip"])
if uploaded_file:
    merged_dataframe = save_upload_file(uploaded_file)
    # 显示结果
    st.write("合并总数据：")
    st.write(merged_dataframe)
    if not merged_dataframe.empty:
        col1, col2, col3 = st.columns(3)
        column_name = st.selectbox('请选择抽取同质化的文本列', merged_dataframe.columns)
        patterns = get_patterns()
        explanations = {
            'p1': "匹配完全重复的内容",
            'p2': "匹配大括号内的内容",
            'p3': "匹配数字",
            'p4': "匹配中文数字",
            'p5': "匹配尖括号内的HTML标签",
            'p6': "匹配方括号内的内容"
        }
        
        df = pd.DataFrame([(k, v['regex']) for k, v in patterns.items()], columns=['Pattern', 'Regex'])
        df['Explanation'] = df['Pattern'].map(explanations)
        pattern_names = st.multiselect('选择您需要匹配的模式', explanations.keys(), default=explanations.keys())
        st.table(df)
        button = st.button('抽取文本')
        if button:
            similar_text_data, characters_total, similar_text_total, similar_text_rate = extract_similar_text(merged_dataframe, column_name, pattern_names)
            st.write("原文列总字数：", characters_total)
            st.write("同质化文本字数：", similar_text_total)
            st.write(f"同质化文本率：{similar_text_rate}%")
            st.write(similar_text_data)
        
