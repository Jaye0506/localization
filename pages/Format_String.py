import streamlit as st
import re
import csv
import os
import pandas as pd

# 保存模板
def save_prompt(text, tags:list):
    file_name = 'prompts.csv'
    if not os.path.exists(file_name):
        with open(file_name,'w',encoding='utf-8-sig',newline='') as fp:
            writer = csv.writer(fp)
            writer.writerow(['prompt','tags'])
    with open(file_name,'a',encoding='utf-8-sig',newline='') as fp:
        writer = csv.writer(fp)
        tag = ';'.join(tags)
        writer.writerow([text,tag])

# 读取模板
def load_csv():
    if os.path.exists('prompts.csv'):
        st.session_state['df'] = pd.read_csv('prompts.csv')
    else:
        st.write('prompts文件不存在')

# 抽取格式化字符串
def find_placeholders(text):
    # 正则表达式匹配 {placeholder} 或 %s 或 %d
    pattern = re.compile(r"\{(.+?)\}|(?:%[sd])|%(\d*\.\d+)?f")
    matches = pattern.finditer(text)
    # 获取所有匹配项
    placeholders = [match.group(1) if match.group(1) is not None else match.group() for match in matches]
    print(placeholders)
    return placeholders

# 替换数据
def replace_placeholders(text, replacements):
    # 使用正则表达式来匹配浮点数的格式化占位符（如 %.2f）
    float_format_pattern = r'%(\d+)?\.?(\d+)?f'

    for key, val in replacements.items():
        if key == "%s":
            for s_val in val:
                text = text.replace("%s", s_val, 1)
        elif key == "%d":
            d_vals = list(map(int, val))
            for d_val in d_vals:
                text = text.replace("%d", str(d_val), 1)
        elif key == "%f" or re.match(float_format_pattern, key):
            f_vals = list(map(float, val))
            for f_val in f_vals:
                # 寻找第一个匹配的格式化浮点数占位符
                match = re.search(float_format_pattern, text)
                if match:
                    format_specifier = match.group()
                    # 使用字符串的格式化方法来格式化浮点数
                    formatted_value = format_specifier % f_val
                    # 替换文本中的占位符
                    text = text.replace(format_specifier, formatted_value, 1)
        else:
            text = text.replace(f"{{{key}}}", val)
    return text

st.title("文本参数格式化")

prompt = st.text_area(
    "示例文本", 
    '''
        恭喜你，{0}!
        你已经完成了第 %d 关。
        你的最终得分是 %f 分。
        真是厉害，%s！
        你用时 %.2f 小时完成了游戏。
    '''
    , height=300
)

col0, col1, col2, col3 = st.columns([0.4,0.2,0.2,0.2])
with col1:
    if st.button('保存示例模板'):
        save_prompt(prompt,find_placeholders(prompt))
        with col0:
            st.write('保存成功!')
with col2:
    st.button('读取示例模板', on_click=load_csv)
with col3:
    st.button('清除保存的示例模板',on_click=lambda : os.remove('prompts.csv') if os.path.exists('prompts.csv') else None)
if 'df' in st.session_state and st.session_state['df'] is not None:
    st.dataframe(st.session_state.pop('df'))

placeholders = find_placeholders(prompt)

replacements = {}

for i,placeholder in enumerate(placeholders):
    # 检查是否是格式化的浮点数占位符
    is_formatted_float = placeholder.endswith("f") and any(c in placeholder for c in "0123456789.")
    if placeholder == "%s":
        # 使用列表来存储所有的"%s"输入，如果键不存在，则初始化为空列表
        replacements.setdefault(placeholder, []).append(
            st.text_input(f'{placeholder}：可输入一段文本', key=f't_input_{i}')
        )
    elif placeholder == "%d":
        replacements.setdefault(placeholder, []).append(
            st.text_input(f'{placeholder}：可输入一个整数', key=f't_input_{i}')
        )
    elif placeholder == "%f" or is_formatted_float:
        replacements.setdefault(placeholder, []).append(
            st.text_input(f'{placeholder}：可输入一个数字', key=f't_input_{i}')
        )
    else:
        replacements[placeholder] = st.text_input(f'{placeholder}：可输入一个变量的值',key=f't_input_{i}')
print(replacements)

if st.button("结果"):

    formatted_text = replace_placeholders(prompt, replacements)
    print(formatted_text)
    st.write(formatted_text)
