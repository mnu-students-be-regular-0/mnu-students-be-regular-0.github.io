import streamlit as st
import os
import subprocess
import sys

# أمر لضمان تثبيت مكتبة groq إذا فشل النظام في تحميلها تلقائياً
try:
    from groq import Groq
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "groq"])
    from groq import Groq

from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد الصفحة
st.set_page_config(page_title="محول المحاضرات", page_icon="🎙️")
st.title("🎙️ محول الصوت إلى PDF")

api_key = st.text_input("أدخل مفتاح Groq API الخاص بك:", type="password")
uploaded_file = st.file_uploader("ارفع ملف الصوت هنا", type=["mp3", "wav", "m4a"])

if uploaded_file and api_key:
    if st.button("بدء التحويل"):
        try:
            client = Groq(api_key=api_key)
            with st.spinner("جاري التحويل..."):
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=(uploaded_file.name, uploaded_file.read()),
                    language="ar"
                )
                text = transcription.text
                st.success("تم التحويل بنجاح!")
                st.text_area("النص الناتج:", text, height=200)

                # إنشاء PDF
                pdf = FPDF()
                pdf.add_page()
                
                # استخدام الاسم الصحيح للخط بعد تعديله في جيت هاب
                font_file = "Amiri-Regular.ttf"
                if os.path.exists(font_file):
                    pdf.add_font("Amiri", "", font_file)
                    pdf.set_font("Amiri", size=14)
                else:
                    pdf.set_font("Arial", size=12)

                reshaped_text = arabic_reshaper.reshape(text)
                pdf.multi_cell(0, 10, get_display(reshaped_text), align='R')
                
                pdf.output("output.pdf")
                with open("output.pdf", "rb") as f:
                    st.download_button("📥 تحميل ملف PDF", f, file_name="lecture.pdf")
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
