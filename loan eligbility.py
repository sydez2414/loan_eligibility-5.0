import streamlit as st
import pandas as pd
import math
import datetime
from io import BytesIO
from fpdf import FPDF
import base64
import qrcode
from PIL import Image
import os

st.set_page_config(page_title="Loan Eligibility Checker", layout="wide")

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Laporan Kelayakan Pinjaman', ln=True, align='C')
        self.ln(5)

    def add_client_info(self, name, phone, email, price, tenure):
        self.set_font('Arial', '', 11)
        self.cell(0, 10, f"Nama: {name}", ln=True)
        self.cell(0, 10, f"Telefon: {phone}  |  Emel: {email}", ln=True)
        self.cell(0, 10, f"Harga Hartanah: RM{price:,.0f}  |  Tempoh: {tenure} tahun", ln=True)
        self.ln(5)

    def add_table(self, df):
        self.set_font("Arial", 'B', 11)
        self.cell(50, 10, "Bank", 1, 0, 'C')
        self.cell(30, 10, "Kadar", 1, 0, 'C')
        self.cell(40, 10, "Ansuran", 1, 0, 'C')
        self.cell(25, 10, "DSR", 1, 0, 'C')
        self.cell(30, 10, "Status", 1, 1, 'C')
        self.set_font("Arial", '', 10)
        for _, row in df.iterrows():
            self.cell(50, 8, str(row['🏦 Bank']), 1)
            self.cell(30, 8, f"{row['Kadar (%)']}%", 1)
            self.cell(40, 8, f"RM{row['Ansuran (RM)']}", 1)
            self.cell(25, 8, f"{row['DSR (%)']}%", 1)
            self.cell(30, 8, row['Status'], 1, ln=True)

    def amortization_summary(self, P, rate, tenure):
        r = (rate / 100) / 12
        n = tenure * 12
        monthly = P * r * (1 + r)**n / ((1 + r)**n - 1) if r > 0 else P / n
        total = monthly * n
        interest = total - P
        self.ln(5)
        self.set_font("Arial", 'B', 11)
        self.cell(0, 10, "Ringkasan Amortization", ln=True)
        self.set_font("Arial", '', 10)
        self.cell(0, 10, f"Jumlah Bayaran Semula: RM{total:,.2f}  | Jumlah Faedah: RM{interest:,.2f}", ln=True)

    def add_footer(self, agent, phone, id):
        self.ln(10)
        self.set_font("Arial", 'I', 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Disediakan oleh: {agent} | ID: {id} | Telefon: {phone}", ln=True)
        self.cell(0, 8, "Penafian: Kelulusan akhir tertakluk kepada penilaian pihak bank.", ln=True)

    def add_qr(self, phone):
        qr = qrcode.make(f"https://wa.me/6{phone}")
        path = "/tmp/qr.png"
        qr.save(path)
        self.image(path, x=160, y=self.get_y(), w=30)
        if os.path.exists(path):
            os.remove(path)

    def generate_report(self, name, phone, email, price, tenure, df, agent, agent_phone, agent_id):
        self.add_page()
        self.add_client_info(name, phone, email, price, tenure)
        self.add_table(df)
        self.amortization_summary(price * 0.9, float(df.iloc[0]['Kadar (%)']), tenure)
        self.add_footer(agent, agent_phone, agent_id)
        self.add_qr(agent_phone)

with st.form("eligibility_form"):
    st.markdown("## Semakan Kelayakan Pinjaman")
    col1, col2 = st.columns(2)

    with col1:
        client_name = st.text_input("Nama Pembeli")
        client_phone = st.text_input("No Telefon")
        client_email = st.text_input("Alamat Emel")
        property_price = st.number_input("Harga Hartanah", min_value=50000.0, max_value=5000000.0, step=1000.0, format="%0.2f")
        tenure = st.slider("Tempoh Pembiayaan (tahun)", min_value=5, max_value=35, value=30)

    with col2:
        net_income = st.number_input("Gaji Pokok Bulanan", min_value=0.0, format="%0.2f")
        fixed_allowance = st.number_input("Elaun Tetap Bulanan", min_value=0.0, format="%0.2f")
        bonus = st.number_input("Bonus Bulanan", min_value=0.0, format="%0.2f")
        other_income = st.number_input("Pelbagai Elaun", min_value=0.0, format="%0.2f")
        total_income = net_income + fixed_allowance + bonus + other_income

    st.markdown("### Potongan Bulanan")
    pot1, pot2 = st.columns(2)
    with pot1:
        perkeso = st.number_input("PERKESO", min_value=0.0, format="%0.2f")
        sip = st.number_input("SIP", min_value=0.0, format="%0.2f")
    with pot2:
        cukai = st.number_input("Cukai", min_value=0.0, format="%0.2f")
        zakat = st.number_input("Zakat", min_value=0.0, format="%0.2f")
    total_deductions = perkeso + sip + cukai + zakat

    st.markdown("### Komitmen Sedia Ada")
    kom1, kom2 = st.columns(2)
    with kom1:
        loan_house = st.number_input("Pinjaman Perumahan", min_value=0.0, format="%0.2f")
        loan_car = st.number_input("Pinjaman Kereta", min_value=0.0, format="%0.2f")
        loan_personal = st.number_input("Pinjaman Peribadi", min_value=0.0, format="%0.2f")
    with kom2:
        loan_asb = st.number_input("Pembiayaan ASB", min_value=0.0, format="%0.2f")
        loan_ptptn = st.number_input("PTPTN", min_value=0.0, format="%0.2f")
        loan_cc = st.number_input("Kad Kredit / Overdraf", min_value=0.0, format="%0.2f")
    total_commitments = loan_house + loan_car + loan_personal + loan_asb + loan_ptptn + loan_cc

    col_btn = st.columns([1, 1])
    with col_btn[0]:
        submitted = st.form_submit_button("📈 KIRA")
    with col_btn[1]:
        if st.form_submit_button("🔁 RESET"):
            st.experimental_rerun()

if submitted:
    st.write("### Jumlah Pendapatan Bersih: RM{:.2f}".format(total_income))
    st.write("### Jumlah Potongan: RM{:.2f}".format(total_deductions))
    st.write("### Jumlah Komitmen: RM{:.2f}".format(total_commitments))
    # Fungsi asal dikekalkan di bawah untuk keputusan kelayakan
