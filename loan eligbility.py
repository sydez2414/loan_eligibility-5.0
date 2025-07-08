import streamlit as st
import pandas as pd
import math
import datetime
from io import BytesIO
from fpdf import FPDF
import base64

st.set_page_config(page_title="Loan Eligibility Checker", layout="wide")

st.markdown("""
    <style>
        .main-title {
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
        }
        .section-header {
            font-size: 22px;
            font-weight: 600;
            color: #2980b9;
            margin-top: 1em;
        }
        .stTextInput>label, .stNumberInput>label, .stSlider>label {
            font-weight: 500;
        }
        .stDataFrame, .stMarkdown {
            font-size: 16px;
        }
        .stButton>button {
            font-weight: 600;
            background-color: #3498db;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# PDF CLASS KEKAL (dari atas)

# ===================== INPUT FORM =====================
st.title("📋 Loan Eligibility Checker")

with st.form("loan_form"):
    st.subheader("Maklumat Pembeli")
    client_name = st.text_input("Nama Penuh")
    client_phone = st.text_input("Nombor Telefon")
    client_email = st.text_input("Emel")
    property_price = st.number_input("Harga Hartanah (RM)", min_value=10000.0, step=1000.0, format="%.2f")
    tenure = st.slider("Tempoh Pembiayaan (Tahun)", min_value=5, max_value=35, value=30)
    income = st.number_input("Pendapatan Bersih Bulanan (RM)", min_value=0.0, step=100.0)
    commitment = st.number_input("Jumlah Komitmen Bulanan (RM)", min_value=0.0, step=50.0)
    agent_name = st.text_input("Nama Ejen")
    agent_id = st.text_input("ID Ejen")
    agent_phone = st.text_input("Telefon Ejen")
    submitted = st.form_submit_button("📊 Kira Kelayakan")

# ===================== PROSES & KIRA =====================
if submitted:
    DSR_limit = 0.70  # 70% DSR standard
    banks = {
        "CIMB": 3.20,
        "MAYBANK": 3.20,
        "RHB": 3.10,
        "MBSB": 4.00,
        "B.ISLAM": 3.45,
        "MUAMALAT": 4.20,
        "HONG LEONG": 3.15,
        "RAKYAT": 3.50,
        "ALLIANCE": 3.15,
        "STANDCHART": 3.30,
        "AMBANK": 3.50
    }

    result = []
    for bank, rate in banks.items():
        r = (rate / 100) / 12
        n = tenure * 12
        loan_amount = property_price * 0.9
        if r > 0:
            installment = loan_amount * r * (1 + r)**n / ((1 + r)**n - 1)
        else:
            installment = loan_amount / n
        available_income = income - commitment - 1500  # Tolak NDI anggaran
        dsr = installment / income if income > 0 else 0
        status = "LULUS" if dsr <= DSR_limit else "TOLAK"
        result.append({
            "🏦 Bank": bank,
            "Kadar (%)": f"{rate:.2f}",
            "Ansuran (RM)": f"{installment:,.2f}",
            "DSR (%)": f"{dsr * 100:.2f}",
            "Status": status
        })

    df_result = pd.DataFrame(result)
    st.success("Hasil Penilaian Kelayakan:")
    st.dataframe(df_result)

    # ===================== MUAT TURUN PDF =====================
    pdf = PDF()
    pdf.generate_report(client_name, client_phone, client_email, property_price, tenure, df_result, agent_name, agent_phone, agent_id)
    buffer = BytesIO()
    pdf.output(buffer)
    st.download_button("📄 Muat Turun PDF", data=buffer.getvalue(), file_name="laporan_kelayakan.pdf", mime="application/pdf")
