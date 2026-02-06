import streamlit as st
import os
from groq import Groq
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# 1. إعدادات الصفحة والواجهة
st.set_page_config(page_title="مساعد الصيدلة الذكي Pro", page_icon="💊", layout="wide")
st.title("🎙️ منصة تفريغ وتلخيص المحاضرات الصيدلانية")
st.markdown("---")

# 2. جلب مفاتيح API من الأسرار (Secrets)
# تأكد من إضافة groq_api_key_1 و groq_api_key_2 في إعدادات Streamlit Cloud
api_keys = [
    st.secrets.get("groq_api_key_1"),
    st.secrets.get("groq_api_key_2")
]
# تنظيف القائمة من أي مفاتيح فارغة
api_keys = [k for k in api_keys if k]

if not api_keys:
    st.error("⚠️ خطأ: لم يتم العثور على مفاتيح API. يرجى إضافتها في الإعدادات.")
    st.stop()

# 3. رفع الملف
uploaded_file = st.file_uploader("ارفع ملف المحاضرة (يفضل مضغوط وأقل من 25MB)", type=["mp3", "wav", "m4a"])

if uploaded_file:
    if st.button("🚀 بدء المعالجة الذكية"):
        raw_text = ""
        success_client = None
        
        # محاولة التحويل مع نظام التبديل التلقائي
        for i, key in enumerate(api_keys):
            try:
                client = Groq(api_key=key)
                with st.spinner(f"جاري التفريغ باستخدام الحساب رقم ({i+1})..."):
                    # إرسال كلمات مفتاحية (Prompt) لـ Whisper لتحسين دقة المصطلحات الطبية
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=(uploaded_file.name, uploaded_file.read()),
                        language="ar",
                        prompt="Pharmacology, Mechanism of action, Dosage, Side effects, Clinical pharmacy"
                    )
                    raw_text = transcription.text
                    success_client = client
                    break # نجحت العملية، اخرج من الحلقة
            except Exception as e:
                if "rate_limit_exceeded" in str(e):
                    st.warning(f"⚠️ الحساب رقم ({i+1}) وصل للحد الأقصى، جاري الانتقال للحساب التالي...")
                    continue
                else:
                    st.error(f"❌ حدث خطأ تقني: {e}")
                    st.stop()
        
        if not raw_text:
            st
