
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

# Adiciona colunas novas na tabela alunos
for coluna, tipo in [
    ("data_nascimento", "TEXT"),
    ("genero", "TEXT"),
    ("peso", "TEXT"),
    ("objetivo", "TEXT"),
    ("historico_medico", "INTEGER DEFAULT 0"),
    ("historico_medico_obs", "TEXT"),
    ("medicamentos", "INTEGER DEFAULT 0"),
    ("medicamentos_obs", "TEXT"),
    ("condicionamento", "TEXT"),
    ("condicionamento_obs", "TEXT"),
]:
    try:
        cursor.execute(f"ALTER TABLE alunos ADD COLUMN {coluna} {tipo}")
        conn.commit()
    except:
        pass

# Tabela de medidas corporais
cursor.execute("""
CREATE TABLE IF NOT EXISTS medidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER,
    data_medicao TEXT,
    ombro REAL,
    biceps REAL,
    peito REAL,
    cintura REAL,
    quadriceps REAL,
    gluteo REAL,
    panturrilha REAL
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
    "Ficha do Aluno",
    "Medidas Corporais",
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

        col_graf1, col_graf2, col_graf3 = st.columns([0.5, 3, 0.5])
        with col_graf2:
            st.bar_chart(grafico_df["total"], height=250)

# CADASTRO
elif menu == "Cadastrar Aluno":
    st.subheader("➕ Novo Aluno")

    with st.form("form_aluno"):

        st.markdown("#### 👤 Informações Pessoais")
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome completo")
        telefone = col2.text_input("Telefone")

        col3, col4, col5 = st.columns(3)
        data_nascimento = col3.text_input(
            "Data de nascimento",
            placeholder="DD/MM/AAAA",
            max_chars=10,
            help="Formato: DD/MM/AAAA"
        )
        genero = col4.selectbox("Gênero", ["Masculino", "Feminino", "Outro"])
        peso = col5.text_input("Peso (kg)", placeholder="Ex: 75.5")

        objetivo = st.text_input(
            "Objetivo", placeholder="Ex: Ganho de massa, emagrecimento...")

        st.markdown("---")
        st.markdown("#### 🏥 Informações de Saúde (Anamnese)")

        col6, col7 = st.columns([1, 3])
        historico_medico = col6.checkbox(
            "Histórico médico? (diabetes, hipertensão, problemas cardíacos...)")
        historico_medico_obs = col7.text_input(
            "Observações do histórico médico", disabled=not historico_medico)

        col8, col9 = st.columns([1, 3])
        medicamentos = col8.checkbox("Uso de medicamentos controlados?")
        medicamentos_obs = col9.text_input(
            "Quais medicamentos?", disabled=not medicamentos)

        condicionamento = st.selectbox(
            "Nível de condicionamento físico atual",
            ["Sedentário", "Iniciante", "Ativo", "Atleta"]
        )
        condicionamento_obs = st.text_input(
            "Observações sobre condicionamento",
            placeholder="Detalhes adicionais..."
        )

        submit = st.form_submit_button("✅ Cadastrar Aluno")

    if submit:
        if not nome or not telefone:
            st.warning("Nome e telefone são obrigatórios!")
        else:
            data_inscricao = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO alunos (
                    nome, telefone, data_inscricao,
                    data_nascimento, genero, peso, objetivo,
                    historico_medico, historico_medico_obs,
                    medicamentos, medicamentos_obs,
                    condicionamento, condicionamento_obs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nome, telefone, data_inscricao,
                data_nascimento, genero, peso, objetivo,
                int(historico_medico), historico_medico_obs,
                int(medicamentos), medicamentos_obs,
                condicionamento, condicionamento_obs
            ))
            conn.commit()
            st.success(f"Aluno '{nome}' cadastrado com sucesso!")

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

            with st.form("form_editar"):
                st.markdown("#### 👤 Informações Pessoais")
                col1, col2 = st.columns(2)
                novo_nome = col1.text_input(
                    "Nome", value=str(aluno["nome"] or ""))
                novo_telefone = col2.text_input(
                    "Telefone", value=str(aluno["telefone"] or ""))

                col3, col4, col5 = st.columns(3)
                novo_nascimento = col3.text_input(
                    "Data de nascimento", value=str(aluno.get("data_nascimento") or ""))
                novo_genero = col4.selectbox(
                    "Gênero",
                    ["Masculino", "Feminino", "Outro"],
                    index=["Masculino", "Feminino",
                           "Outro"].index(aluno["genero"])
                    if aluno.get("genero") in ["Masculino", "Feminino", "Outro"] else 0
                )
                novo_peso = col5.text_input(
                    "Peso (kg)", value=str(aluno.get("peso") or ""))
                novo_objetivo = st.text_input(
                    "Objetivo", value=str(aluno.get("objetivo") or ""))

                st.markdown("---")
                st.markdown("#### 🏥 Anamnese")

                col6, col7 = st.columns([1, 3])
                novo_hist = col6.checkbox(
                    "Histórico médico?", value=bool(aluno.get("historico_medico")))
                novo_hist_obs = col7.text_input("Observações histórico", value=str(
                    aluno.get("historico_medico_obs") or ""))

                col8, col9 = st.columns([1, 3])
                novo_med = col8.checkbox(
                    "Medicamentos controlados?", value=bool(aluno.get("medicamentos")))
                novo_med_obs = col9.text_input(
                    "Quais medicamentos?", value=str(aluno.get("medicamentos_obs") or ""))

                novo_cond = st.selectbox(
                    "Condicionamento físico",
                    ["Sedentário", "Iniciante", "Ativo", "Atleta"],
                    index=["Sedentário", "Iniciante", "Ativo",
                           "Atleta"].index(aluno["condicionamento"])
                    if aluno.get("condicionamento") in ["Sedentário", "Iniciante", "Ativo", "Atleta"] else 0
                )
                novo_cond_obs = st.text_input("Observações condicionamento", value=str(
                    aluno.get("condicionamento_obs") or ""))

                col_btn1, col_btn2 = st.columns(2)
                salvar = col_btn1.form_submit_button("💾 Salvar alterações")
                excluir = col_btn2.form_submit_button("🗑️ Excluir aluno")

            # SALVAR
            if salvar:
                if not novo_nome or not novo_telefone:
                    st.warning("Preencha nome e telefone!")
                else:
                    cursor.execute("""
                        UPDATE alunos SET
                            nome = ?, telefone = ?,
                            data_nascimento = ?, genero = ?, peso = ?, objetivo = ?,
                            historico_medico = ?, historico_medico_obs = ?,
                            medicamentos = ?, medicamentos_obs = ?,
                            condicionamento = ?, condicionamento_obs = ?
                        WHERE id = ?
                    """, (
                        novo_nome, novo_telefone,
                        novo_nascimento, novo_genero, novo_peso, novo_objetivo,
                        int(novo_hist), novo_hist_obs,
                        int(novo_med), novo_med_obs,
                        novo_cond, novo_cond_obs,
                        int(aluno["id"])
                    ))
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
                        "DELETE FROM pagamentos WHERE aluno_id = ?", (aluno_id_excluir,))
                    cursor.execute(
                        "DELETE FROM alunos WHERE id = ?", (aluno_id_excluir,))
                    conn.commit()
                    st.session_state["confirmando_exclusao"] = False
                    st.success(
                        f"Aluno '{nome_confirmacao}' excluído com sucesso!")
                    st.rerun()

                if col_nao.button("❌ Cancelar"):
                    st.session_state["confirmando_exclusao"] = False
                    st.rerun()

# FICHA DO ALUNO
elif menu == "Ficha do Aluno":
    st.subheader("📋 Ficha do Aluno")

    alunos = pd.read_sql("SELECT * FROM alunos", conn)

    if alunos.empty:
        st.warning("Nenhum aluno cadastrado.")
    else:
        aluno_nome = st.selectbox("Selecione o aluno", alunos["nome"])
        aluno = alunos[alunos["nome"] == aluno_nome].iloc[0]

        st.markdown("---")

        # INFORMAÇÕES PESSOAIS
        st.markdown("#### 👤 Informações Pessoais")
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Nome:** {aluno['nome']}")
        col1.markdown(f"**Telefone:** {aluno['telefone']}")
        # Calcula a idade
        data_nasc_str = aluno.get('data_nascimento')
        idade_texto = "—"
        data_nasc_formatada = data_nasc_str or "—"

        if data_nasc_str:
            try:
                # Remove tudo que não for número
                numeros = ''.join(filter(str.isdigit, data_nasc_str))

                # Tenta montar a data se tiver 8 dígitos
                if len(numeros) == 8:
                    data_nasc_str = f"{numeros[:2]}/{numeros[2:4]}/{numeros[4:8]}"
                    data_nasc_formatada = data_nasc_str

                data_nasc = datetime.strptime(data_nasc_str, "%d/%m/%Y")
                hoje_calc = datetime.now()
                idade = hoje_calc.year - data_nasc.year - (
                    (hoje_calc.month, hoje_calc.day) < (
                        data_nasc.month, data_nasc.day)
                )
                idade_texto = f"{idade} anos"
            except:
                idade_texto = "Data inválida"

        col2.markdown(f"**Data de nascimento:** {data_nasc_formatada}")
        col2.markdown(f"**Idade:** {idade_texto}")
        col2.markdown(f"**Gênero:** {aluno.get('genero') or '—'}")

        # INFORMAÇÕES DE SAÚDE
        st.markdown("#### 🏥 Informações de Saúde (Anamnese)")

        # Histórico médico
        tem_hist = bool(aluno.get("historico_medico"))
        st.markdown(
            f"**Histórico médico:** {'✅ Sim' if tem_hist else '❌ Não'}")
        if tem_hist and aluno.get("historico_medico_obs"):
            st.info(f"📝 {aluno['historico_medico_obs']}")

        # Medicamentos
        tem_med = bool(aluno.get("medicamentos"))
        st.markdown(
            f"**Medicamentos controlados:** {'✅ Sim' if tem_med else '❌ Não'}")
        if tem_med and aluno.get("medicamentos_obs"):
            st.info(f"📝 {aluno['medicamentos_obs']}")

        # Condicionamento
        st.markdown(
            f"**Condicionamento físico:** {aluno.get('condicionamento') or '—'}")
        if aluno.get("condicionamento_obs"):
            st.info(f"📝 {aluno['condicionamento_obs']}")

        st.markdown("---")

        # ÚLTIMA MEDIÇÃO
        st.markdown("#### 📏 Última Medição Corporal")

        ultima_medida = pd.read_sql("""
            SELECT * FROM medidas
            WHERE aluno_id = ?
            ORDER BY data_medicao DESC
            LIMIT 1
        """, conn, params=(int(aluno["id"]),))

        if ultima_medida.empty:
            st.warning("Nenhuma medição registrada ainda.")
        else:
            m = ultima_medida.iloc[0]
            st.caption(f"Registrada em: {m['data_medicao']}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ombro", f"{m['ombro']} cm")
            col1.metric("Bíceps", f"{m['biceps']} cm")
            col2.metric("Peito", f"{m['peito']} cm")
            col2.metric("Cintura", f"{m['cintura']} cm")
            col3.metric("Quadríceps", f"{m['quadriceps']} cm")
            col3.metric("Glúteo", f"{m['gluteo']} cm")
            col4.metric("Panturrilha", f"{m['panturrilha']} cm")

# MEDIDAS CORPORAIS
elif menu == "Medidas Corporais":
    st.subheader("📏 Medidas Corporais")

    alunos = pd.read_sql("SELECT * FROM alunos", conn)

    if alunos.empty:
        st.warning("Nenhum aluno cadastrado.")
    else:
        aluno_nome = st.selectbox("Selecione o aluno", alunos["nome"])
        aluno_id = alunos[alunos["nome"] == aluno_nome]["id"].values[0]

        aba1, aba2 = st.tabs(["📊 Histórico", "➕ Nova Medição"])

        # ABA 1 — histórico de medições
        with aba1:
            historico_med = pd.read_sql("""
                SELECT
                    data_medicao AS "Data",
                    ombro AS "Ombro (cm)",
                    biceps AS "Bíceps (cm)",
                    peito AS "Peito (cm)",
                    cintura AS "Cintura (cm)",
                    quadriceps AS "Quadríceps (cm)",
                    gluteo AS "Glúteo (cm)",
                    panturrilha AS "Panturrilha (cm)"
                FROM medidas
                WHERE aluno_id = ?
                ORDER BY data_medicao DESC
            """, conn, params=(int(aluno_id),))

            if historico_med.empty:
                st.warning("Nenhuma medição registrada ainda.")
            else:
                st.dataframe(historico_med, use_container_width=True)

                # Gráfico de evolução da cintura como exemplo
                st.markdown("---")
                st.markdown("#### 📈 Evolução da Cintura")

                evolucao = pd.read_sql("""
                    SELECT data_medicao as data, cintura
                    FROM medidas
                    WHERE aluno_id = ?
                    ORDER BY data_medicao ASC
                """, conn, params=(int(aluno_id),))

                if len(evolucao) > 1:
                    evolucao = evolucao.set_index("data")
                    st.line_chart(evolucao["cintura"])
                else:
                    st.info("Registre pelo menos 2 medições para ver a evolução.")

        # ABA 2 — nova medição
        with aba2:
            with st.form("form_medidas"):
                st.markdown("#### Insira as medidas em centímetros")

                col1, col2, col3 = st.columns(3)
                ombro = col1.number_input(
                    "Ombro (cm)", min_value=0.0, step=0.1)
                biceps = col2.number_input(
                    "Bíceps (cm)", min_value=0.0, step=0.1)
                peito = col3.number_input(
                    "Peito (cm)", min_value=0.0, step=0.1)

                col4, col5, col6 = st.columns(3)
                cintura = col4.number_input(
                    "Cintura (cm)", min_value=0.0, step=0.1)
                quadriceps = col5.number_input(
                    "Quadríceps (cm)", min_value=0.0, step=0.1)
                gluteo = col6.number_input(
                    "Glúteo (cm)", min_value=0.0, step=0.1)

                panturrilha = st.number_input(
                    "Panturrilha (cm)", min_value=0.0, step=0.1)

                salvar_med = st.form_submit_button("💾 Salvar medições")

            if salvar_med:
                data_medicao = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""
                    INSERT INTO medidas (
                        aluno_id, data_medicao,
                        ombro, biceps, peito, cintura,
                        quadriceps, gluteo, panturrilha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(aluno_id), data_medicao,
                    ombro, biceps, peito, cintura,
                    quadriceps, gluteo, panturrilha
                ))
                conn.commit()
                st.success("Medições salvas com sucesso!")
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
