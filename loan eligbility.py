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

# PDF KEMAS
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, 'Laporan Kelayakan Pinjaman Pembeli', ln=True, align='C')
        self.ln(5)

    def add_client_info(self, name, phone, email, price, tenure):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"Nama: {name}", ln=True)
        self.cell(0, 10, f"Telefon: {phone}  |  Emel: {email}", ln=True)
        self.cell(0, 10, f"Harga Hartanah: RM{price:,.0f}  |  Tempoh: {tenure} tahun", ln=True)
        self.ln(5)

    def add_table(self, df):
        self.set_font("Arial", 'B', 11)
        self.set_fill_color(230, 230, 250)
        self.cell(50, 10, "Bank", 1, 0, 'C', 1)
        self.cell(30, 10, "Kadar", 1, 0, 'C', 1)
        self.cell(40, 10, "Ansuran", 1, 0, 'C', 1)
        self.cell(25, 10, "DSR", 1, 0, 'C', 1)
        self.cell(30, 10, "Status", 1, 1, 'C', 1)

        self.set_font("Arial", '', 10)
        for _, row in df.iterrows():
            self.cell(50, 8, str(row['🏦 Bank']), 1)
            self.cell(30, 8, f"{row['Kadar (%)']}%", 1)
            self.cell(40, 8, f"RM{row['Ansuran (RM)']}", 1)
            self.cell(25, 8, f"{row['DSR (%)']}%", 1)
            self.cell(30, 8, row['Status'], 1, ln=True)

    def add_footer(self, agent, phone, id):
        self.ln(10)
        self.set_font("Arial", 'I', 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Disediakan oleh: {agent} | ID: {id} | Telefon: {phone}", ln=True)
        self.cell(0, 8, "Nota: Kelulusan akhir tertakluk kepada penilaian pihak bank.", ln=True)

    def amortization_summary(self, P, rate, tenure):
        r = (rate / 100) / 12
        n = tenure * 12
        if r > 0:
            monthly = P * r * (1 + r)**n / ((1 + r)**n - 1)
        else:
            monthly = P / n
        total = monthly * n
        interest = total - P
        self.ln(5)
        self.set_font("Arial", 'B', 11)
        self.cell(0, 10, "Ringkasan Amortization", ln=True)
        self.set_font("Arial", '', 10)
        self.cell(0, 10, f"Jumlah Bayaran Semula: RM{total:,.2f}  | Jumlah Faedah: RM{interest:,.2f}", ln=True)

    def generate_report(self, name, phone, email, price, tenure, df, agent, agent_phone, agent_id):
        self.add_page()
        self.add_client_info(name, phone, email, price, tenure)
        self.add_table(df)
        self.amortization_summary(price, float(df.iloc[0]['Kadar (%)']), tenure)
        self.add_footer(agent, agent_phone, agent_id)

# 🔗 Integrasi PDF Generator
if 'df_result' in locals():
    pdf = PDF()
    pdf.generate_report(client_name, client_phone, client_email, property_price, tenure, df_result, agent_name, agent_phone, agent_id)
    buffer = BytesIO()
    pdf.output(buffer)
    st.download_button("📄 Muat Turun PDF", buffer.getvalue(), file_name="laporan_kelayakan.pdf", mime="application/pdf"), file_name="laporan_kelayakan.pdf", mime="application/pdf")
