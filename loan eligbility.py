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

EJEN_FILE = "ejen.csv"

EXPECTED_COLUMNS = ["nama", "telefon", "password"]

def daftar_ejen(nama, telefon, password):
    if not os.path.exists(EJEN_FILE):
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        df = pd.read_csv(EJEN_FILE)

        # Reset if columns do not match
        if sorted(df.columns) != sorted(EXPECTED_COLUMNS):
            df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    if (df["telefon"] == telefon).any():
        return False, "Ejen telah berdaftar."

    new_row = pd.DataFrame([[nama, telefon, password]], columns=EXPECTED_COLUMNS)
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(EJEN_FILE, index=False)
    return True, "Pendaftaran berjaya."

def semak_login(telefon, password):
    if not os.path.exists(EJEN_FILE):
        return False, "Tiada data ejen."
    df = pd.read_csv(EJEN_FILE)
    if list(df.columns) != EXPECTED_COLUMNS:
        return False, "Struktur data tidak sah."
    match = df[(df["telefon"] == telefon) & (df["password"] == password)]
    if not match.empty:
        return True, match.iloc[0].to_dict()
    return False, "Maklumat tidak sah."

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Laporan Kelayakan Pinjaman', ln=True, align='C')
        self.ln(5)

    def add_client_info(self, name, phone, email, price, margin, tenure):
        self.set_font('Arial', '', 11)
        self.cell(0, 10, f"Nama: {name}", ln=True)
        self.cell(0, 10, f"Telefon: {phone}  |  Emel: {email}", ln=True)
        self.cell(0, 10, f"Harga Hartanah: RM{price:,.0f}  | Margin: {margin}%  | Tempoh: {tenure} tahun", ln=True)
        self.ln(5)

    def add_table(self, df):
        self.set_font("Arial", 'B', 11)
        self.cell(50, 10, "Bank", 1, 0, 'C')
        self.cell(30, 10, "Kadar", 1, 0, 'C')
        self.cell(40, 10, "Ansuran", 1, 0, 'C')
        self.cell(25,  10, "DSR", 1, 0, 'C')
        self.cell(30, 10, "Status", 1, 1, 'C')
        self.set_font("Arial", '', 10)
        for _, row in df.iterrows():
            self.cell(50, 8, str(row['\U0001f3e6 Bank']), 1)
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

    def generate_report(self, name, phone, email, price, margin, tenure, df, agent, agent_phone, agent_id):
        self.add_page()
        self.add_client_info(name, phone, email, price, margin, tenure)
        self.add_table(df)
        if not df.empty:
            try:
                self.amortization_summary(price * (margin / 100), float(df.iloc[0]['Kadar (%)']), tenure)
            except:
                pass
        self.add_footer(agent, agent_phone, agent_id)
        self.add_qr(agent_phone)

# Login/Register UI
st.sidebar.markdown("### Ejen")
menu = st.sidebar.radio("", ["Log Masuk", "Daftar Ejen", "Lupa Kata Laluan"], horizontal=False)

if menu == "Daftar Ejen":
    st.subheader("Pendaftaran Ejen")
    name = st.text_input("Nama Ejen")
    phone = st.text_input("No Telefon")
    pwd = st.text_input("Kata Laluan", type="password")
    if st.button("Daftar"):
        ok, msg = daftar_ejen(name, phone, pwd)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

elif menu == "Log Masuk":
    st.subheader("Log Masuk Ejen")
    phone = st.text_input("No Telefon")
    pwd = st.text_input("Kata Laluan", type="password")
    st.caption("Belum berdaftar? Pilih 'Daftar Ejen' di menu atas.")
    if st.button("Log Masuk"):
        ok, result = semak_login(phone, pwd)
        if ok:
            st.session_state.logged_in = True
            st.session_state.agent_name = result['nama']
            st.session_state.agent_id = result['telefon']
            st.session_state.agent_phone = result['telefon']
            st.success("Log masuk berjaya!")
            st.experimental_rerun()
        else:
            st.error(result)

elif menu == "Lupa Kata Laluan":
    st.subheader("Lupa Kata Laluan")
    st.info("Sila hubungi admin untuk set semula kata laluan anda.")

if st.session_state.get("logged_in"):
    exec(open("loan_eligibility_main.py").read())
