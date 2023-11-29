import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Pie, Bar, Line
from streamlit_echarts import st_pyecharts
import streamlit as st
import random
import numpy as np
from copy import copy
def _col_counts_tuple(column: pd.Series):
    if column.isnull().all():
        return [("暂无数据", 0)]
    items = list(column.value_counts().items())
    if len(items) > 14:
        return [(str(a), b) for a, b in items[:14]] + [
            ("other", sum(c for _, c in items[14:]))
        ]
    else:
        return [(str(a), b) for a, b in items]


def st_pie(df: pd.DataFrame, column, title=None):
    if isinstance(column, int):
        tuple_data = _col_counts_tuple(df.iloc[:, column])
        title = title if title else df.columns[column]
    else:
        tuple_data = _col_counts_tuple(df[column])
        title = title if title else column
    pie = (
        Pie()
        .add("", tuple_data, radius=["0%", "60%"])
        .set_global_opts(
            title_opts=opts.TitleOpts(
                # title=title,
                # subtitle=f"总数:{df.shape[0]}",
                pos_left="center",
                pos_top="0%",
            ),
            legend_opts=opts.LegendOpts(pos_top="bottom"),
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{d}%"))
    )
    return st_pyecharts(pie,key=f'pie_{title}_{random.randint(1,10000)}')


def st_bar(df: pd.DataFrame, column, multi_option=False ,title=None):
    if isinstance(column, int):
        _column = df.iloc[:, column]
        title = title if title else df.columns[column]
    else:
        _column = df[column]
        title = title if title else column

    if multi_option:
        _column = _column.str.split(', ',expand=True).stack().reset_index(drop=True)
    _value_counts = _column.value_counts()
    x_axis = _value_counts.index.to_list()
    y_axis = _value_counts.to_list()
    bar = (
        Bar()
        .add_xaxis(x_axis)
        .add_yaxis("数量", y_axis)
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{c}", position="top"))
    )
    return st_pyecharts(bar,key=f'bar_{title}_{random.randint(1,10000)}')


def st_line(df: pd.DataFrame, column, title=None):
    def convert_mm_dd(_col):
        if _col.dtype == np.dtype('datetime64[ns]'):
            return _col.dt.strftime('%m-%d')
        else:
            _col =_col.astype(str)
        _col = _col.str.replace("下午", "PM").str.replace("上午", "AM")
        try:
            _col = pd.to_datetime(_col, errors="raise").dt.strftime("%m-%d")
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
    return st_pyecharts(line,key=f'line_{title}_{random.randint(1,10000)}')


def st_break_down_bar(df: pd.DataFrame, column, break_base, multi_option=False, title=None):
    new_df  = copy(df)

    if isinstance(column, int):
        column_name = new_df.columns[column]
    else:
        column_name = column
    if column_name==break_base:
        st.write('Warning: 拆分与拆分依据相同')
        return
    if multi_option:
        new_df[column_name] = new_df[column_name].str.split(', ')
        new_df_exp = new_df.explode(column_name)
    else:
        new_df_exp = new_df
    
    chunk_counts = (
        new_df_exp[[column_name, break_base]]
        .groupby([column_name, break_base])
        .size()
        .unstack(fill_value=0)
    )

    bar = (
        Bar()
        .add_xaxis(chunk_counts.index.tolist())
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
            yaxis_opts=opts.AxisOpts(),
        )
    )

    for chunk, counts in chunk_counts.items():
        bar.add_yaxis(chunk, counts.tolist())

    bar.set_global_opts(yaxis_opts=opts.AxisOpts(name="数量"))

    return st_pyecharts(bar,key=f'breakdown_{title}_{random.randint(1,10000)}')
