import streamlit as st
import os
import subprocess
import sys

# 1. أمر لضمان تثبيت مكتبة groq إذا فشل النظام في تحميلها تلقائياً
try:
    from groq import Groq
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "groq"])
    from groq import Groq

from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# 2. إعداد الصفحة
st.set_page_config(page_title="محول المحاضرات الذكي", page_icon="🎙️")
st.title("🎙️ محول الصوت إلى PDF")

# 3. التحقق من وجود المفتاح في Secrets أو طلبه يدوياً
# سيبحث الكود عن اسم 'groq_api_key' في إعدادات Streamlit Cloud
if "groq_api_key" in st.secrets:
    api_key = st.secrets["groq_api_key"]
else:
    api_key = st.text_input("أدخل مفتاح Groq API الخاص بك:", type="password", help="لإخفاء هذه الخانة، أضف المفتاح في Secrets")

# 4. واجهة رفع الملف
uploaded_file = st.file_uploader("ارفع ملف الصوت هنا (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

if uploaded_file and api_key:
    if st.button("بدء التحويل"):
        try:
            client = Groq(api_key=api_key)
            
            with st.spinner("جاري معالجة الصوت وتحويله لنص..."):
                # طلب التحويل من Groq
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=(uploaded_file.name, uploaded_file.read()),
                    language="ar"
                )
                text = transcription.text
                st.success("تم التحويل بنجاح!")
                st.text_area("النص الناتج:", text, height=200)

                # 5. إنشاء ملف PDF
                pdf = FPDF()
                pdf.add_page()
                
                # التأكد من اسم ملف الخط المرفوع في GitHub
                font_file = "Amiri-Regular.ttf"
                if os.path.exists(font_file):
                    pdf.add_font("Amiri", "", font_file)
                    pdf.set_font("Amiri", size=14)
                else:
                    st.warning("تنبيه: لم يتم العثور على ملف الخط، سيتم استخدام الخط الافتراضي.")
                    pdf.set_font("Arial", size=12)

                # معالجة النصوص العربية (القلب والتشكيل)
                reshaped_text = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped_text)
                
                pdf.multi_cell(0, 10, bidi_text, align='R')
                
                # مخرج الـ PDF
                pdf_output = "lecture_summary.pdf"
                pdf.output(pdf_output)
                
                with open(pdf_output, "rb") as f:
                    st.download_button(
                        label="📥 تحميل ملف PDF المنسق",
                        data=f,
                        file_name="lecture.pdf",
                        mime="application/pdf"
                    )
        
        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة: {e}")
