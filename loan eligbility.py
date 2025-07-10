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
        property_price = float(st.text_input("Harga Hartanah", "0"))
        tenure = st.slider("Tempoh Pembiayaan (tahun)", min_value=5, max_value=35, value=30)

    with col2:
        net_income = float(st.text_input("Pendapatan Bersih", "0"))
        joint_income = float(st.text_input("Pendapatan Bersama (jika ada)", "0"))
        commitments_main = float(st.text_input("Komitmen Pembeli", "0"))
        commitments_joint = float(st.text_input("Komitmen Bersama", "0"))

    col_btn = st.columns([1, 1])
    with col_btn[0]:
        submitted = st.form_submit_button("📈 KIRA")
    with col_btn[1]:
        if st.form_submit_button("🔁 RESET"):
            st.experimental_rerun()

if submitted:
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

    loan_amount = property_price * 0.9
    total_income = net_income + joint_income
    total_commitments = commitments_main + commitments_joint
    fixed_ndi = 1500

    results = []
    for bank, rate in banks.items():
        monthly_rate = (rate / 100) / 12
        months = tenure * 12
        installment = loan_amount * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)
        dsr = ((total_commitments + installment + fixed_ndi) / total_income) * 100
        status = "LULUS" if dsr <= 70 else "TIDAK LULUS"
        results.append({
            "🏦 Bank": bank,
            "Kadar (%)": f"{rate:.2f}",
            "Ansuran (RM)": f"{installment:,.2f}",
            "DSR (%)": f"{dsr:,.2f}",
            "Status": status
        })

    df_result = pd.DataFrame(results)
    st.markdown("## 📋 KEPUTUSAN")
    st.dataframe(df_result)

    pdf = PDF()
    pdf.generate_report(client_name, client_phone, client_email, property_price, tenure, df_result, "Agent Name", "0123456789", "PEA1234")
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer = BytesIO(pdf_bytes)

    col_dl = st.columns([1, 1, 1])
    with col_dl[0]:
        st.download_button("📄 Muat Turun PDF", data=buffer.getvalue(), file_name="laporan_kelayakan.pdf", mime="application/pdf")
    with col_dl[1]:
        csv_data = pd.DataFrame([{ "Nama": client_name, "Telefon": client_phone, "Email": client_email, "Harga": property_price, "Gaji": net_income, "Komitmen": total_commitments, "Tarikh": datetime.date.today() }])
        csv = csv_data.to_csv(index=False).encode('utf-8')
        st.download_button("📁 Muat Turun CSV", csv, "data_pembeli.csv", "text/csv")
    with col_dl[2]:
        if st.button("🗓️ Amortization"):
            r = (banks[list(banks.keys())[0]] / 100) / 12
            n = tenure * 12
            P = loan_amount
            monthly = P * r * (1 + r)**n / ((1 + r)**n - 1)
            total = monthly * n
            interest = total - P
            st.markdown(f"**Ansuran Bulanan:** RM{monthly:,.2f}")
            st.markdown(f"**Jumlah Faedah:** RM{interest:,.2f}")
            st.markdown(f"**Jumlah Bayaran:** RM{total:,.2f}")

    st.markdown("### 📤 Kongsi")
    col3, col4 = st.columns([1, 1])
    with col3:
        st.markdown("[![WhatsApp](https://img.icons8.com/color/48/000000/whatsapp--v1.png)](https://wa.me/?text=Sila%20semak%20laporan%20kelayakan%20yang%20dilampirkan)")
    with col4:
        email_url = f"mailto:{client_email}?subject=Laporan%20Kelayakan&body=Sila%20semak%20laporan%20yang%20dilampirkan"
        st.markdown(f"[![Email](https://img.icons8.com/fluency/48/000000/email.png)]({email_url})", unsafe_allow_html=True)
