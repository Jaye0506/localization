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
        "序号": ["1", "2"],
        "工具": ["Format_String", "Similar_Extract"],
        "说明": ["文本参数格式化", "同质化文本抽取"],
    }
    # 在 Streamlit 应用中创建一个表格
    st.table(data)


if __name__ == "__main__":
    run()
