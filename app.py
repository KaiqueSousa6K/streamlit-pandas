import bcrypt
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import streamlit as st


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


def get_connection():
    return sqlite3.connect("academia.db", check_same_thread=False)


conn = get_connection()
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
    proximo_vencimento TEXT,
    valor REAL
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
cursor.execute(
    "SELECT * FROM usuarios WHERE username = ?",
    ("admin",)
)

if cursor.fetchone() is None:

    senha_hash = bcrypt.hashpw(
        "1234".encode('utf-8'),
        bcrypt.gensalt()
    )

    cursor.execute(
        "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
        ("admin", senha_hash)
    )

    conn.commit()

# TÍTULO

st.title("🏋️ Sistema de Gestão de Academia")
st.markdown("---")

# TELA DE LOGIN

if "logado" not in st.session_state:
    st.session_state.logado = False
st.markdown(
    "<h1 style='text-align: center;'>Sistema de Gestão</h1>",
    unsafe_allow_html=True
)
if not st.session_state.logado:

    st.markdown("""
    <style>
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }

    .login-box {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
        width: 350px;
    }

    .login-title {
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 20px;
    }

    .stTextInput input {
        border-radius: 10px;
        padding: 10px;
    }

    .stButton button {
        background: linear-gradient(90deg, #4CAF50, #2e7d32);
        color: white;
        border-radius: 10px;
        height: 45px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">🏋️ Login da Academia</div>',
                unsafe_allow_html=True)

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = ?",
            (usuario,)
        )

        user = cursor.fetchone()

        if user and bcrypt.checkpw(
            senha.encode('utf-8'),
            user[2]
        ):
            st.session_state.logado = True
            st.success("Login realizado!")
            st.rerun()

        else:
            st.error("Usuário ou senha incorretos")

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# MENU

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Cadastrar Aluno",
    "Registrar Pagamento",
    "Ver Alunos",
    "Histórico de Pagamentos",
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
    pagamentos_df["data_pagamento"] = pd.to_datetime(
        pagamentos_df["data_pagamento"]
    )

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    pagamentos_mes = pagamentos_df[
        (pagamentos_df["data_pagamento"].dt.month == mes_atual) &
        (pagamentos_df["data_pagamento"].dt.year == ano_atual)
    ]

    receita_mes = pagamentos_mes["valor"].sum()

    hoje = datetime.now()
    inadimplentes = 0

    for _, row in pagamentos_df.iterrows():
        vencimento = pd.to_datetime(row["proximo_vencimento"])
        if vencimento < hoje:
            inadimplentes += 1

    col1, col2, col3 = st.columns(3)

    col1.metric("👥 Alunos", total_alunos)
    col2.metric(
        "💰 Receita do mês",
        f"R$ {receita_mes:.2f}"
    )
    col3.metric("⚠️ Inadimplentes", inadimplentes)

# CADASTRO

elif menu == "Cadastrar Aluno":
    st.subheader("➕ Novo Aluno")

    with st.form("form_aluno"):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")

        submit = st.form_submit_button("Cadastrar")

        if submit:
            if not nome or not telefone:
                st.warning("Preencha todos os campos!")
            else:
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

        valor = st.number_input(
            "Valor Pago",
            min_value=0.0,
            value=100.0
        )

        if st.button("Registrar pagamento"):
            hoje = datetime.now()
            proximo = hoje + timedelta(days=30)

            cursor.execute("""
                INSERT INTO pagamentos (
                    aluno_id,
                    data_pagamento,
                    proximo_vencimento,
                    valor
                )
                VALUES (?, ?, ?, ?)
            """, (
                int(aluno_id),
                hoje.strftime("%Y-%m-%d"),
                proximo.strftime("%Y-%m-%d"),
                valor
            ))

            conn.commit()

            st.success(
                f"Pagamento registrado! Próximo vencimento: {proximo.strftime('%d/%m/%Y')}"
            )

    else:
        st.warning("Nenhum aluno cadastrado.")


# LISTA

# LISTA
elif menu == "Ver Alunos":
    st.subheader("Lista de Alunos")

    df = pd.read_sql("SELECT * FROM alunos", conn)

    aba1, aba2 = st.tabs(["Lista", "✏️ Editar / Excluir"])

    # ABA 1 — lista simples
    with aba1:
        st.dataframe(df, use_container_width=True)

    # ABA 2 — editar e excluir
    with aba2:
        if df.empty:
            st.warning("Nenhum aluno cadastrado.")
        else:
            # Selectbox com os nomes dos alunos
            aluno_nome = st.selectbox("Selecione o aluno", df["nome"])

            # Busca os dados atuais do aluno selecionado
            aluno = df[df["nome"] == aluno_nome].iloc[0]

            st.markdown("#### Dados atuais")

            # Formulário já preenchido com os dados do aluno
            with st.form("form_editar"):
                novo_nome = st.text_input("Nome", value=aluno["nome"])
                novo_telefone = st.text_input(
                    "Telefone", value=aluno["telefone"])

                col1, col2 = st.columns(2)

                salvar = col1.form_submit_button("💾 Salvar alterações")
                excluir = col2.form_submit_button("🗑️ Excluir aluno")

            # SALVAR
            if salvar:
                if not novo_nome or not novo_telefone:
                    st.warning("Preencha todos os campos!")
                else:
                    cursor.execute(
                        "UPDATE alunos SET nome = ?, telefone = ? WHERE id = ?",
                        (novo_nome, novo_telefone, int(aluno["id"]))
                    )
                    conn.commit()
                    st.success(f"Aluno '{novo_nome}' atualizado com sucesso!")
                    st.rerun()

            # EXCLUIR
            if excluir:
                cursor.execute(
                    "DELETE FROM pagamentos WHERE aluno_id = ?",
                    (int(aluno["id"]),)
                )
                cursor.execute(
                    "DELETE FROM alunos WHERE id = ?",
                    (int(aluno["id"]),)
                )
                conn.commit()
                st.success(f"Aluno '{aluno_nome}' excluído com sucesso!")
                st.rerun()

# HISTÓRICO DE PAGAMENTOS
elif menu == "Histórico de Pagamentos":
    st.subheader("📜 Histórico de Pagamentos")

    alunos = pd.read_sql("SELECT * FROM alunos", conn)

    if alunos.empty:
        st.warning("Nenhum aluno cadastrado.")
    else:
        # Selectbox pra escolher o aluno
        aluno_nome = st.selectbox("Selecione o aluno", alunos["nome"])
        aluno_id = alunos[alunos["nome"] == aluno_nome]["id"].values[0]

        # Busca os pagamentos daquele aluno específico
        query = """
        SELECT
            data_pagamento AS "Data do Pagamento",
            proximo_vencimento AS "Próximo Vencimento",
            valor AS "Valor (R$)"
        FROM pagamentos
        WHERE aluno_id = ?
        ORDER BY data_pagamento DESC
        """

        historico = pd.read_sql(query, conn, params=(int(aluno_id),))

        if historico.empty:
            st.warning(
                f"{aluno_nome} ainda não possui pagamentos registrados.")
        else:
            # Tabela com o histórico
            st.dataframe(historico, use_container_width=True)

            st.markdown("---")

            # Resumo financeiro
            total_pago = historico["Valor (R$)"].sum()
            total_pagamentos = len(historico)

            col1, col2 = st.columns(2)
            col1.metric("💰 Total pago", f"R$ {total_pago:.2f}")
            col2.metric("📅 Pagamentos realizados", total_pagamentos)

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
