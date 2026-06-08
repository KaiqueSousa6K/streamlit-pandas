
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import urllib.parse
import bcrypt

# CONFIGURAÇÕES DE PLANOS
PLANOS = {
    "Diária - R$ 7,00":    {"valor": 7.0,  "dias": 1},
    "Semanal - R$ 20,00":  {"valor": 20.0, "dias": 7},
    "Mensal - R$ 65,00":   {"valor": 65.0, "dias": 30},
}


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
    border-radius: 8px;
    background-color: #1a1a1a;
    color: #f0f0f0;
    border: 1px solid #333333;
}
.stTextInput>div>div>input:focus {
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


@st.cache_resource
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

# Adiciona coluna plano se ainda não existir
try:
    cursor.execute(
        "ALTER TABLE pagamentos ADD COLUMN plano TEXT DEFAULT 'Mensal - R$ 65,00'")
    conn.commit()
except:
    pass

try:
    cursor.execute(
        "ALTER TABLE pagamentos ADD COLUMN forma_pagamento TEXT DEFAULT 'Dinheiro'")
    conn.commit()
except:
    pass

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

st.sidebar.markdown(
    "<h2 style='text-align: center; color: #FF6B00; font-weight: bold; padding: 20px 0;'>⚡ ENERGYM FIT</h2>",
    unsafe_allow_html=True
)

# TELA DE LOGIN

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    # Esconde a sidebar na tela de login
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="collapsedControl"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 10px 0 30px 0;'>
                <span style='font-size: 48px; font-weight: 900; color: #FF6B00;
                letter-spacing: 3px;'>⚡ ENERGYM FIT</span><br>
                <span style='font-size: 16px; color: #aaaaaa;'>Sistema de Gestão</span>
            </div>
        """, unsafe_allow_html=True)

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

        # Selectbox com os planos disponíveis
        plano_nome = st.selectbox("Plano", list(PLANOS.keys()))
        plano = PLANOS[plano_nome]

        forma_pagamento = st.selectbox(
            "Forma de Pagamento",
            ["Dinheiro 💵", "Pix 📲", "Cartão 💳"]
        )
        # Mostra o valor e duração do plano selecionado
        col1, col2 = st.columns(2)
        col1.info(f"💰 Valor: R$ {plano['valor']:.2f}")
        col2.info(f"📅 Duração: {plano['dias']} dia(s)")

        if st.button("Registrar pagamento"):
            hoje = datetime.now()
            proximo = hoje + timedelta(days=plano["dias"])

            cursor.execute("""
                INSERT INTO pagamentos (
                    aluno_id,
                    data_pagamento,
                    proximo_vencimento,
                    valor,
                    plano,
                    forma_pagamento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                int(aluno_id),
                hoje.strftime("%Y-%m-%d"),
                proximo.strftime("%Y-%m-%d"),
                plano["valor"],
                plano_nome,
                forma_pagamento
            ))

            conn.commit()
            st.success(
                f"Pagamento registrado! Próximo vencimento: {proximo.strftime('%d/%m/%Y')}"
            )

    else:
        st.warning("Nenhum aluno cadastrado.")


# LISTA

elif menu == "Ver Alunos":
    st.subheader("📋 Lista de Alunos")

    aba1, aba2 = st.tabs(["📋 Lista", "✏️ Editar / Excluir"])

    # ABA 1 — lista com busca e filtro
    with aba1:
        col_busca, col_filtro = st.columns([2, 1])

        busca = col_busca.text_input(
            "🔍 Buscar por nome",
            placeholder="Digite o nome do aluno..."
        )

        filtro = col_filtro.selectbox(
            "📌 Filtrar por status",
            ["Todos", "Em dia", "Inadimplentes", "Nunca pagou"]
        )

        # Busca todos os alunos com o último vencimento
        query_lista = """
        SELECT
            a.id,
            a.nome,
            a.telefone,
            a.data_inscricao,
            MAX(p.proximo_vencimento) as vencimento
        FROM alunos a
        LEFT JOIN pagamentos p ON a.id = p.aluno_id
        GROUP BY a.id
        """

        df = pd.read_sql(query_lista, conn)
        hoje = datetime.now()

        # Classifica cada aluno com um status
        def classificar(venc):
            if pd.isna(venc):
                return "Nunca pagou"
            elif pd.to_datetime(venc) < hoje:
                return "Inadimplentes"
            else:
                return "Em dia"

        df["status"] = df["vencimento"].apply(classificar)

        # Aplica o filtro de busca por nome
        if busca:
            df = df[df["nome"].str.contains(busca, case=False, na=False)]

        # Aplica o filtro de status
        if filtro != "Todos":
            df = df[df["status"] == filtro]

        if df.empty:
            st.warning("Nenhum aluno encontrado.")
        else:
            # Mostra a tabela sem a coluna de vencimento e id
            st.dataframe(
                df[["nome", "telefone", "data_inscricao", "status"]],
                use_container_width=True
            )

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

            # EXCLUIR — confirmação em duas etapas
            if excluir:
                st.session_state["confirmando_exclusao"] = True
                st.session_state["aluno_para_excluir_id"] = int(aluno["id"])
                st.session_state["aluno_para_excluir_nome"] = aluno_nome

            if st.session_state.get("confirmando_exclusao"):
                nome_confirmacao = st.session_state["aluno_para_excluir_nome"]
                st.warning(
                    f"⚠️ Tem certeza que deseja excluir **{nome_confirmacao}**? Essa ação não pode ser desfeita.")

                col_sim, col_nao = st.columns(2)

                if col_sim.button("✅ Sim, excluir"):
                    aluno_id_excluir = st.session_state["aluno_para_excluir_id"]
                    cursor.execute(
                        "DELETE FROM pagamentos WHERE aluno_id = ?",
                        (aluno_id_excluir,)
                    )
                    cursor.execute(
                        "DELETE FROM alunos WHERE id = ?",
                        (aluno_id_excluir,)
                    )
                    conn.commit()
                    st.session_state["confirmando_exclusao"] = False
                    st.success(
                        f"Aluno '{nome_confirmacao}' excluído com sucesso!")
                    st.rerun()

                if col_nao.button("❌ Cancelar"):
                    st.session_state["confirmando_exclusao"] = False
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
            plano AS "Plano",
            forma_pagamento AS "Forma de Pagamento",
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
