import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )

    st.write("# Leiting-Localization! 👋")
    st.markdown(
    """
        欢迎使用本地化工具网页端服务！！！
    """
    )
    data = {
        "序号": ["1", "2", "3", "4", "5"],
        "工具": ["Font Viewer", "Format String", "Questionnaire Backoffice", "Similar Extract", "Terminology Check"],
        "说明": ["字体渲染", "文本参数格式化", "问卷后台", "同质化文本抽取", "术语检查"],
    }
    # 在 Streamlit 应用中创建一个表格
    st.table(data)


if __name__ == "__main__":
    run()
