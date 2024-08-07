import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Pie, Bar, Line
from streamlit_echarts import st_pyecharts
import streamlit as st
import random
import numpy as np
from copy import copy

def _col_counts_tuple(column: pd.Series, max_count):
    if column.isnull().all():
        return [("暂无数据", 0)]
    items = list(column.value_counts().items())
    if len(items) > max_count:
        return [(str(a), b) for a, b in items[:max_count]] + [
            ("other", sum(c for _, c in items[max_count:]))
        ]
    else:
        return [(str(a), b) for a, b in items]

def _col_counts_tuple_by_options(column: pd.Series, options_show):
    if column.isnull().all():
        return [("暂无数据", 0)]
    result = []
    other_count = 0
    items = list(column.value_counts().items())
    for a, b in items:
        if a in options_show:
            result.append((str(a), b))
        else:
            other_count += b
    if other_count > 0:
        result.append(('other', other_count))
    return result

def st_pie(df: pd.DataFrame, column, options_show, multi_option=False, title=None):
    if isinstance(column, int):
        _column = df.iloc[:, column]
        title = title if title else df.columns[column]
    else:
        _column = df[column]
        title = title if title else column
    if multi_option:
        _column = _column.str.split(';',expand=True).stack().reset_index(drop=True)
        _column = _column[_column != '']  # 过滤掉空字符串
    if len(options_show) == 0: 
        tuple_data = _col_counts_tuple(_column, 12)
    else:
        tuple_data = _col_counts_tuple_by_options(_column, options_show)
    print("tuple_data", tuple_data)
    pie = (
        Pie()
        .add("", tuple_data, radius=["0%", "50%"])
        .set_global_opts(
            title_opts=opts.TitleOpts(
                # title=title,
                # subtitle=f"总数:{df.shape[0]}",
                pos_left="center",
                pos_top="0%",
            ),
            # legend_opts=opts.LegendOpts(pos_top="bottom",type_="scroll"),
            legend_opts=opts.LegendOpts(pos_top="bottom"),
            # toolbox_opts=opts.ToolboxOpts(
            #     feature=opts.ToolBoxFeatureOpts(
            #         opts.ToolBoxFeatureSaveAsImageOpts(name='bbb.png')
            #     )
            # )
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{d}%"))
    )
    st_pyecharts(pie,key=f'pie_{title}_{random.randint(1,10000)}')
    return pie

def st_bar(df: pd.DataFrame, column, options_show, multi_option=False, title=None):
    if isinstance(column, int):
        _column = df.iloc[:, column]
        title = title if title else df.columns[column]
    else:
        _column = df[column]
        title = title if title else column
    if multi_option:
        _column = _column.str.split(';',expand=True).stack().reset_index(drop=True)
        _column = _column[_column != '']  # 过滤掉空字符串
    if len(options_show) == 0:
        tuple_data = _col_counts_tuple(_column, 12)
    else:
        tuple_data = _col_counts_tuple_by_options(_column, options_show)
    x_axis = []
    y_axis = []
    for language, count in tuple_data:
        x_axis.append(language)
        y_axis.append(count)
    # _value_counts = _column.value_counts()
    # x_axis = _value_counts.index.to_list()
    # y_axis = _value_counts.to_list()
    print('x_axis', x_axis)
    bar = (
        Bar()
        .add_xaxis(x_axis)
        .add_yaxis("数量", y_axis)
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{c}", position="top"))
    )
    st_pyecharts(bar,key=f'bar_{title}_{random.randint(1,10000)}')
    return bar


def st_line(df: pd.DataFrame, column, title=None):
    def convert_mm_dd(_col):
        if _col.dtype == np.dtype('datetime64[ns]'):
            return _col.dt.strftime('%Y-%m-%d')
        else:
            _col =_col.astype(str)
        _col = _col.str.replace("下午", "PM").str.replace("上午", "AM")
        try:
            _col = pd.to_datetime(_col, errors="raise").dt.strftime("%Y-%m-%d")
        except:
            ...
        return _col

    if isinstance(column, int):
        col = df.iloc[:, column]
        title = title if title else df.columns[column]
    else:
        col = df[column]
        title = title if title else column

    group_col = convert_mm_dd(col)
    chart_data = group_col.groupby(group_col).count().cumsum()
    line = (
        Line()
        .add_xaxis(chart_data.index.to_list())
        .add_yaxis(
            "问卷量", chart_data.to_list(), areastyle_opts=opts.AreaStyleOpts(opacity=0.5)
        )
        .set_global_opts(title_opts=opts.TitleOpts(title="问卷收集进度"))
    )
    st_pyecharts(line,key=f'line_{title}_{random.randint(1,10000)}')
    return line


def st_break_down_bar(df: pd.DataFrame, column, options_show, break_base, divide_options_show, multi_option=False, title=None):
    new_df  = copy(df)

    if isinstance(column, int):
        column_name = new_df.columns[column]
    else:
        column_name = column
    if column_name==break_base:
        st.write('Warning: 拆分与拆分依据相同')
        return
    if multi_option:
        new_df[column_name] = new_df[column_name].str.split(';')
        new_df_exp = new_df.explode(column_name)
    else:
        new_df_exp = new_df
    if len(options_show) == 0:
        column_options = _col_counts_tuple(new_df_exp[column_name], 12)
    else:
        column_options = _col_counts_tuple_by_options(new_df_exp[column_name], options_show)
    column_options_list = [item[0] for item in column_options if item[0].lower() != 'other']
    print("column_options_list", column_options_list)
    # 根据option_list把其他的选项用other替换
    new_df_exp['column_options'] = new_df_exp[column_name].apply(lambda x: x if (pd.isnull(x) or x in column_options_list) else 'other')
    filtered_df = new_df_exp[new_df_exp['column_options'].notna()].copy()
    
    if len(divide_options_show) == 0:
        break_base_options = _col_counts_tuple(filtered_df[break_base], 4)
    else:
        break_base_options = _col_counts_tuple_by_options(filtered_df[break_base], divide_options_show)
    break_base_options_list = [item[0] for item in break_base_options if item[0].lower() != 'other']
    # 根据break_base_options_list把其他的选项用other替换
    filtered_df['break_base_options'] = filtered_df[break_base].apply(lambda x: x if (pd.isnull(x) or x in break_base_options_list) else 'other')
    chunk_counts = (
        filtered_df[['column_options', 'break_base_options']]
        .groupby(['column_options', 'break_base_options'])
        .size()
        .unstack(fill_value=0)
    )
    chunk_counts['total'] = chunk_counts.sum(axis=1)
    chunk_counts_sorted = chunk_counts.sort_values('total', ascending=False)
    chunk_counts_sorted = chunk_counts_sorted.drop('total', axis=1)
    bar = (
        Bar()
        .add_xaxis(chunk_counts_sorted.index.tolist())
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-25)),
            yaxis_opts=opts.AxisOpts(),
        )
    )

    for chunk, counts in chunk_counts_sorted.items():
        bar.add_yaxis(chunk, counts.tolist())

    bar.set_global_opts(yaxis_opts=opts.AxisOpts(name="数量"))

    st_pyecharts(bar,key=f'breakdown_{title}_{random.randint(1,10000)}')
    return bar
