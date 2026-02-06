import streamlit as st
import os
from groq import Groq
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="مساعد الصيدلة الذكي - برو", page_icon="💊", layout="wide")
st.title("🎙️ منصة التفريغ الذكي (نظام التبديل التلقائي)")

# 1. جلب المفاتيح من Secrets
# يمكنك إضافة مفاتيح قد ما تحب في قائمة
API_KEYS = [
    st.secrets.get("groq_api_key_1"),
    st.secrets.get("groq_api_key_2")
]
# إزالة أي مفتاح فارغ
API_KEYS = [key for key in API_KEYS if key]

if not API_KEYS:
    st.error("⚠️ لم يتم العثور على أي مفاتيح API في الإعدادات.")
    st.stop()

uploaded_file = st.file_uploader("ارفع ملف المحاضرة", type=["mp3", "wav", "m4a"])

if uploaded_file:
    if st.button("بدء المعالجة الذكية"):
        raw_text = None
        
        # محاولة التحويل باستخدام المفاتيح المتاحة بالتناوب
        for i, key in enumerate(API_KEYS):
            try:
                client = Groq(api_key=key)
                with st.spinner(f"جاري المعالجة باستخدام الحساب رقم ({i+1})..."):
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=(uploaded_file.name, uploaded_file.read()),
                        language="ar"
                    )
                    raw_text = transcription.text
                    break  # إذا نجح التحويل، اخرج من الحلقة (Loop)
            except Exception as e:
                if "rate_limit_exceeded" in str(e):
                    st.warning(f"⚠️ الحساب رقم ({i+1}) وصل للحد الأقصى، جاري التبديل للحساب التالي...")
                    continue # جرب المفتاح التالي
                else:
                    st.error(f"❌ حدث خطأ غير متوقع: {e}")
                    st.stop()
        
        if not raw_text:
            st.error("❌ للأسف، جميع الحسابات المضافة وصلت للحد الأقصى للساعة. يرجى الانتظار 30 دقيقة.")
            st.stop()

        # المرحلة التالية: التلخيص (باستخدام المفتاح الذي نجح)
        try:
            with st.spinner("جاري تنقيح النص وتلخيصه صيدلانياً..."):
                system_prompt = "أنت مساعد صيدلي مصري. لخص هذه المحاضرة في نقاط مع تصحيح المصطلحات الطبية الإنجليزية."
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": raw_text[:15000]}
                    ]
                )
                refined_summary = completion.choices[0].message.content

            st.success("✅ تمت العملية بنجاح!")
            
            # عرض التبويبات (نفس الكود السابق)
            tab1, tab2 = st.tabs(["📝 الملخص", "📄 النص الكامل"])
            with tab1: st.markdown(refined_summary)
            with tab2: st.write(raw_text)

            # (كود الـ PDF كما هو في النسخ السابقة)
            # ... [PDF Generation Code] ...

        except Exception as e:
            st.error(f"حدث خطأ أثناء التلخيص: {e}")
