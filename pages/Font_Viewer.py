import streamlit as st
from PIL import ImageFont, ImageDraw, Image
upload_file = st.file_uploader('请将字体文件放入',type=['otf','ttf'])

texts = st.text_input('输入需要渲染的文字')

if texts:
    if upload_file:
        imageFont = ImageFont.truetype(r'C:\Users\liyz3\AppData\Local\Microsoft\Windows\Fonts\simhei.ttf', 64)
        image = Image.new(mode='L', size=(1080,128), color=224)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), texts, font=imageFont)
        st.image(image) 
    