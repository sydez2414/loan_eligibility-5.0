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
        self.cell(0, 8, "Nota: Kelulusan akhir tertakluk kepada penilaian pihak bank.", ln=True)

    def generate_report(self, name, phone, email, price, tenure, df, agent, agent_phone, agent_id):
        self.add_page()
        self.add_client_info(name, phone, email, price, tenure)
        self.add_table(df)
        self.amortization_summary(price * 0.9, float(df.iloc[0]['Kadar (%)']), tenure)
        self.add_footer(agent, agent_phone, agent_id)

# ===================== FORM INPUT =====================
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

    co_name = st.text_input("👥 Nama Pembeli Bersama (Jika Ada)")
    co_income = st.number_input("Pendapatan Bersih Pembeli Bersama (RM)", min_value=0.0, step=100.0)

    col1, col2 = st.columns([1,1])
    with col1:
        submitted = st.form_submit_button("📈 KIRA")
    with col2:
        st.form_submit_button("🔁 Reset", on_click=lambda: st.experimental_rerun())

# Simulasi login ejen (akan datang: sistem login penuh)
agent_name = "Syed Fadzil"
agent_id = "PEA2641"
agent_phone = "013-3632414"

# ===================== KIRAAN =====================
if submitted:
    DSR_limit = 0.70
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
    total_income = income + co_income
    for bank, rate in banks.items():
        r = (rate / 100) / 12
        n = tenure * 12
        loan_amount = property_price * 0.9
        installment = loan_amount * r * (1 + r)**n / ((1 + r)**n - 1) if r > 0 else loan_amount / n
        dsr = installment / (commitment + 1500 + installment) if total_income > 0 else 0
        status = "LULUS" if dsr <= DSR_limit else "TOLAK"
        result.append({
            "🏦 Bank": bank,
            "Kadar (%)": f"{rate:.2f}",
            "Ansuran (RM)": f"{installment:,.2f}",
            "DSR (%)": f"{dsr * 100:.2f}",
            "Status": status
        })
    df_result = pd.DataFrame(result)
    st.success("📊 KEPUTUSAN")
    st.dataframe(df_result)

    # Simpan CSV
    csv_data = pd.DataFrame([{ 
        "Nama": client_name,
        "Emel": client_email,
        "Telefon": client_phone,
        "Harga": property_price,
        "Tenure": tenure,
        "Pendapatan": income,
        "Pendapatan Bersama": co_income,
        "Komitmen": commitment,
        "Ejen": agent_name,
        "Telefon Ejen": agent_phone,
        "Tarikh": datetime.datetime.now().strftime("%Y-%m-%d")
    }])
    csv = csv_data.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Muat Turun CSV Buyer", csv, "rekod_pembeli.csv", "text/csv")

    # PDF
    pdf = PDF()
    pdf.generate_report(client_name, client_phone, client_email, property_price, tenure, df_result, agent_name, agent_phone, agent_id)
    buffer = BytesIO()
    pdf.output(buffer)
    st.download_button("📄 Muat Turun PDF", data=buffer.getvalue(), file_name="laporan_kelayakan.pdf", mime="application/pdf")

    # Share Link
    st.subheader("📤 Kongsi Hasil Kelayakan")
    share_text = f"Hi {client_name}, berikut adalah hasil semakan kelayakan pinjaman rumah anda."
    whatsapp_url = f"https://wa.me/{client_phone.replace('+','').replace(' ','')}?text={share_text.replace(' ', '%20')}"
    email_url = f"mailto:{client_email}?subject=Hasil%20Semakan%20Kelayakan&body={share_text.replace(' ', '%20')}"
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"[📲 Hantar ke WhatsApp]({whatsapp_url})", unsafe_allow_html=True)
    with col4:
        st.markdown(f"[✉️ Hantar ke Emel]({email_url})", unsafe_allow_html=True)
