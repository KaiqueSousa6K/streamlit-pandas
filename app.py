
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import streamlit as st
st.cache_data.clear()


def gerar_link_whatsapp(telefone, mensagem):
    telefone = ''.join(filter(str.isdigit, str(telefone)))
    mensagem_codificada = urllib.parse.quote(mensagem)
    return f"https://wa.me/{telefone}?text={mensagem_codificada}"


# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Sistema de Academia",
    page_icon="🏋️",
    layout="wide"
)
# ESTILO CUSTOMIZADO (CSS)
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
}
.stTextInput>div>div>input {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# BANCO
conn = sqlite3.connect("academia.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    telefone TEXT,
    data_inscricao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER,
    data_pagamento TEXT,
    proximo_vencimento TEXT
)
""")

conn.commit()
# BANCO LOGIN
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha TEXT
)
""")
conn.commit()
cursor.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
if cursor.fetchone() is None:
    cursor.execute(
        "INSERT INTO usuarios (username, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# TÍTULO
st.title("🏋️ Sistema de Gestão de Academia")
st.markdown("---")
# TELA DE LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 Login do Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = ? AND senha = ?",
            (usuario, senha)
        )
        user = cursor.fetchone()

        if user:
            st.session_state.logado = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

    st.stop()
# MENU
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Cadastrar Aluno",
    "Registrar Pagamento",
    "Ver Alunos",
    "Inadimplentes"
])
# BOTÃO DE LOGOUT
if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()
# DASHBOARD
if menu == "Dashboard":
    st.subheader("📊 Visão Geral")

    alunos_df = pd.read_sql("SELECT * FROM alunos", conn)
    pagamentos_df = pd.read_sql("SELECT * FROM pagamentos", conn)

    total_alunos = len(alunos_df)
    total_pagamentos = len(pagamentos_df)

    hoje = datetime.now()
    inadimplentes = 0

    for _, row in pagamentos_df.iterrows():
        vencimento = datetime.strptime(row["proximo_vencimento"], "%Y-%m-%d")
        if vencimento < hoje:
            inadimplentes += 1

    col1, col2, col3 = st.columns(3)

    col1.metric("👥 Alunos", total_alunos)
    col2.metric("💰 Pagamentos", total_pagamentos)
    col3.metric("⚠️ Inadimplentes", inadimplentes)

# CADASTRO
elif menu == "Cadastrar Aluno":
    st.subheader("➕ Novo Aluno")

    with st.form("form_aluno"):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")

        submit = st.form_submit_button("Cadastrar")

        if submit:
            data_inscricao = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO alunos (nome, telefone, data_inscricao) VALUES (?, ?, ?)",
                (nome, telefone, data_inscricao)
            )
            conn.commit()
            st.success("Aluno cadastrado com sucesso!")

# PAGAMENTO
elif menu == "Registrar Pagamento":
    st.subheader("💳 Registrar Pagamento")

    alunos = pd.read_sql("SELECT * FROM alunos", conn)

    if not alunos.empty:
        aluno_nome = st.selectbox("Aluno", alunos["nome"])
        aluno_id = alunos[alunos["nome"] == aluno_nome]["id"].values[0]

        if st.button("Registrar pagamento"):
            hoje = datetime.now()
            proximo = hoje + timedelta(days=30)

            cursor.execute("""
                INSERT INTO pagamentos (aluno_id, data_pagamento, proximo_vencimento)
                VALUES (?, ?, ?)
                """, (
                int(aluno_id),
                hoje.strftime("%Y-%m-%d"),
                proximo.strftime("%Y-%m-%d")
            ))

            conn.commit()
            st.success(
                f"Pagamento registrado! Próximo vencimento: {proximo.strftime('%d/%m/%Y')}")
    else:
        st.warning("Nenhum aluno cadastrado.")

# LISTA
elif menu == "Ver Alunos":
    st.subheader("📋 Lista de Alunos")

    df = pd.read_sql("SELECT * FROM alunos", conn)
    st.dataframe(df, use_container_width=True)

# INADIMPLENTES

elif menu == "Inadimplentes":
    st.subheader("📊 Status dos Alunos")

    query = """
    SELECT a.nome, a.telefone, MAX(p.proximo_vencimento) as vencimento
    FROM alunos a
    LEFT JOIN pagamentos p ON a.id = p.aluno_id
    GROUP BY a.id
    """

    df = pd.read_sql(query, conn)
    hoje = datetime.now()

    for _, row in df.iterrows():
        nome = row["nome"]
        telefone = row["telefone"]
        venc = row["vencimento"]

        # 📌 Caso nunca tenha pago
        if pd.isna(venc):
            mensagem = f"Olá {nome}, você ainda não possui pagamento registrado. Regularize sua mensalidade 😉"
            link = gerar_link_whatsapp(telefone, mensagem)

            st.error(f"🔴 {nome} - Nunca pagou")
            st.link_button("📩 Cobrar no WhatsApp", link)
            st.divider()
            continue

        # 📌 Converter data com segurança
        try:
            vencimento = datetime.strptime(str(venc), "%Y-%m-%d")
        except:
            st.error(f"Erro com data de {nome}")
            continue

        dias_restantes = (vencimento - hoje).days

        # 🔴 Atrasado
        if vencimento < hoje:
            mensagem = f"Olá {nome}, sua mensalidade está vencida desde {vencimento.strftime('%d/%m/%Y')}. Regularize por favor 😉"
            link = gerar_link_whatsapp(telefone, mensagem)

            st.error(
                f"🔴 {nome} - Atrasado (vencido em {vencimento.strftime('%d/%m/%Y')})")
            st.link_button("📩 Cobrar no WhatsApp", link)

        # 🟡 Vence em breve
        elif dias_restantes <= 5:
            mensagem = f"Olá {nome}, sua mensalidade vence em {dias_restantes} dias. Fique atento 😉"
            link = gerar_link_whatsapp(telefone, mensagem)

            st.warning(f"🟡 {nome} - Vence em {dias_restantes} dias")
            st.link_button("📩 Lembrar no WhatsApp", link)

        # 🟢 Em dia
        else:
            st.success(f"🟢 {nome} - Em dia (vence em {dias_restantes} dias)")

        st.divider()
