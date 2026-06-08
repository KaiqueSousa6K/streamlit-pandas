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
/* Fundo geral */
.main {
    background-color: #0d0d0d;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111111;
    border-right: 2px solid #FF6B00;
}

/* Texto geral */
html, body, [class*="css"] {
    color: #f0f0f0;
}

/* Botões */
.stButton>button {
    background: linear-gradient(90deg, #FF6B00, #FF8C00);
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    border: none;
    font-weight: bold;
    transition: 0.3s;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #FF8C00, #FFA500);
    transform: scale(1.02);
}

/* Inputs */
.stTextInput>div>div>input {
    border-radius: 10px;
    background-color: #1a1a1a;
    color: #f0f0f0;
    border: 1px solid #FF6B00;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: #FF6B00;
}
.stTabs [aria-selected="true"] {
    border-bottom: 2px solid #FF6B00;
}

/* Métricas */
[data-testid="metric-container"] {
    background-color: #1a1a1a;
    border: 1px solid #FF6B00;
    border-radius: 10px;
    padding: 15px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #FF6B00;
    border-radius: 10px;
}

/* Divisor */
hr {
    border-color: #FF6B00;
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
st.sidebar.image("logo.jpg", use_container_width=True)
st.markdown(
    "<h1 style='text-align: center; color: #FF6B00; font-weight: bold;'>⚡ ENERGYM FIT</h1>",
    unsafe_allow_html=True
)
st.markdown("<hr>", unsafe_allow_html=True)

# TELA DE LOGIN

if "logado" not in st.session_state:
    st.session_state.logado = False

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
    background: #1a1a1a;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0px 0px 30px rgba(255, 107, 0, 0.3);
    width: 350px;
    border: 1px solid #FF6B00;
}
.login-title {
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #FF6B00;
}
.stTextInput input {
    border-radius: 10px;
    background-color: #111111;
    color: white;
    border: 1px solid #FF6B00;
}
.stButton button {
    background: linear-gradient(90deg, #FF6B00, #FF8C00);
    color: white;
    border-radius: 10px;
    height: 45px;
    font-weight: bold;
    border: none;
}
</style>
""", unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.markdown(
        "<div class='login-title'>⚡ ENERGYM FIT</div>",
        unsafe_allow_html=True
    )

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
    "Inadimplentes",
    "Alterar Senha"
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

    inadimplentes_query = """
    SELECT COUNT(*) as total
    FROM (
        SELECT a.id, MAX(p.proximo_vencimento) as ultimo_vencimento
        FROM alunos a
        LEFT JOIN pagamentos p ON a.id = p.aluno_id
        GROUP BY a.id
    )
    WHERE ultimo_vencimento < ? OR ultimo_vencimento IS NULL
    """

    inadimplentes = pd.read_sql(
        inadimplentes_query,
        conn,
        params=(hoje.strftime("%Y-%m-%d"),)
    )["total"].values[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Alunos", total_alunos)
    col2.metric("💰 Receita do mês", f"R$ {receita_mes:.2f}")
    col3.metric("⚠️ Inadimplentes", inadimplentes)

    # GRÁFICO DE RECEITA MENSAL
    st.markdown("---")
    st.markdown("#### 📈 Receita dos últimos 6 meses")

    grafico_query = """
    SELECT
        strftime('%Y-%m', data_pagamento) as mes,
        SUM(valor) as total
    FROM pagamentos
    GROUP BY mes
    ORDER BY mes DESC
    LIMIT 6
    """

    grafico_df = pd.read_sql(grafico_query, conn)

    if grafico_df.empty:
        st.info("Nenhum pagamento registrado ainda.")
    else:
        # Inverte a ordem pra ficar do mais antigo pro mais recente
        grafico_df = grafico_df.iloc[::-1].reset_index(drop=True)

        # Formata o mês pra ficar mais legível (ex: 2026-06 → Jun/2026)
        grafico_df["mes"] = pd.to_datetime(
            grafico_df["mes"]
        ).dt.strftime("%b/%Y")

        # Define o mês como índice pro gráfico
        grafico_df = grafico_df.set_index("mes")

        st.bar_chart(grafico_df["total"])

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
# LISTA
elif menu == "Ver Alunos":
    st.subheader("📋 Lista de Alunos")

    aba1, aba2 = st.tabs(["📋 Lista", "✏️ Editar / Excluir"])

    # ABA 1 — lista com busca
    with aba1:
        busca = st.text_input("🔍 Buscar por nome",
                              placeholder="Digite o nome do aluno...")

        if busca:
            df = pd.read_sql(
                "SELECT * FROM alunos WHERE nome LIKE ?",
                conn,
                params=(f"%{busca}%",)
            )
        else:
            df = pd.read_sql("SELECT * FROM alunos", conn)

        if df.empty:
            st.warning("Nenhum aluno encontrado.")
        else:
            st.dataframe(df, use_container_width=True)

    # ABA 2 — editar e excluir
    with aba2:
        df_todos = pd.read_sql("SELECT * FROM alunos", conn)

        if df_todos.empty:
            st.warning("Nenhum aluno cadastrado.")
        else:
            aluno_nome = st.selectbox("Selecione o aluno", df_todos["nome"])
            aluno = df_todos[df_todos["nome"] == aluno_nome].iloc[0]

            st.markdown("#### Dados atuais")

            with st.form("form_editar"):
                novo_nome = st.text_input("Nome", value=aluno["nome"])
                novo_telefone = st.text_input(
                    "Telefone", value=aluno["telefone"])

                col1, col2 = st.columns(2)
                salvar = col1.form_submit_button("💾 Salvar alterações")
                excluir = col2.form_submit_button("🗑️ Excluir aluno")

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

# ALTERAR SENHA
elif menu == "Alterar Senha":
    st.subheader("🔒 Alterar Senha")

    with st.form("form_senha"):
        senha_atual = st.text_input("Senha atual", type="password")
        nova_senha = st.text_input("Nova senha", type="password")
        confirmar_senha = st.text_input(
            "Confirmar nova senha", type="password")

        salvar = st.form_submit_button("💾 Salvar nova senha")

    if salvar:
        # Verifica se algum campo tá vazio
        if not senha_atual or not nova_senha or not confirmar_senha:
            st.warning("Preencha todos os campos!")

        # Verifica se a nova senha e a confirmação batem
        elif nova_senha != confirmar_senha:
            st.error("A nova senha e a confirmação não coincidem!")

        # Verifica se a nova senha tem pelo menos 4 caracteres
        elif len(nova_senha) < 4:
            st.warning("A nova senha deve ter pelo menos 4 caracteres!")

        else:
            # Busca o usuário admin no banco
            cursor.execute(
                "SELECT * FROM usuarios WHERE username = ?",
                ("admin",)
            )
            user = cursor.fetchone()

            # Verifica se a senha atual está correta
            if not bcrypt.checkpw(senha_atual.encode('utf-8'), user[2]):
                st.error("Senha atual incorreta!")
            else:
                # Gera o hash da nova senha e salva no banco
                novo_hash = bcrypt.hashpw(
                    nova_senha.encode('utf-8'),
                    bcrypt.gensalt()
                )
                cursor.execute(
                    "UPDATE usuarios SET senha = ? WHERE username = ?",
                    (novo_hash, "admin")
                )
                conn.commit()
                st.success("Senha alterada com sucesso!")
