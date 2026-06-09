import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import io

st.set_page_config(page_title="Retenção Preditiva - Jumbo CDP", page_icon="🧠", layout="wide")
st.title("🧠 Máquina de Retenção Preditiva — Jumbo CDP")
st.markdown("Gatilhos calculados a partir da **mediana real de recompra** de cada unidade prisional — 5 meses · 15.497 pedidos · 167 unidades mapeadas.")

# ─── WEBHOOKS ───────────────────────────────────────────────────────────────
WEBHOOK_ANTECIPACAO = "https://n8n.corcaqui.com.br/webhook/regua_antecipacao"
WEBHOOK_MEDIANA     = "https://n8n.corcaqui.com.br/webhook/regua_mediana_foco"
WEBHOOK_CRITICO     = "https://n8n.corcaqui.com.br/webhook/regua_alerta_critico"

# ─── MAPEAMENTO REAL: (antecipação, mediana, crítico) em dias ───────────────
# Fonte: análise de 15.497 pedidos — janeiro a maio de 2026
# Fórmula: antecipação = mediana × 0.6 | crítico = mediana × 1.7
MAPEAMENTO_UNIDADES = {
    'Penitenciária Limeira': (3, 1, 2),
    'Penitenciária Balbinos 2': (3, 1, 2),
    'Penitenciária Reginópolis 2': (3, 2, 3),
    'Penitenciária Pacaembu': (3, 2, 3),
    'International Prisoners - Sant\'Ana - Women': (3, 3, 6),
    'CDP São Vicente': (3, 4, 7),
    'CDP Vila Independência': (3, 4, 7),
    'Penitenciária Capela do Alto 2': (3, 5, 8),
    'CR Limeira': (3, 5, 8),
    'CR Ourinhos': (3, 5, 9),
    'Hospital Franco da Rocha 1': (4, 6, 10),
    'Penitenciária Getulina': (4, 6, 10),
    'CDP Americana': (4, 6, 11),
    'CDP São José dos Campos': (4, 6, 11),
    'CPP Franco da Rocha - Castelinho': (4, 7, 12),
    'Détenus Français - Sant\'Ana': (4, 7, 12),
    'Penitenciária Itapetininga 1': (4, 7, 12),
    'Penitenciária São Vicente 1': (4, 7, 12),
    'Penitenciária Gália 2': (4, 7, 13),
    'CDP Bauru': (4, 7, 13),
    'CDP Pinheiros 2': (4, 7, 13),
    'Penitenciária Guareí 1': (4, 7, 13),
    'CDP Guarulhos 2': (5, 8, 14),
    'Penitenciária Adriano Marrey': (5, 8, 14),
    'CDP Caraguatatuba': (5, 8, 14),
    'CDP Guarulhos 1': (5, 8, 14),
    'CPP Guariba': (5, 8, 14),
    'CDP Diadema': (5, 8, 14),
    'Penitenciária Votorantim Feminina': (5, 8, 14),
    'CDP Sorocaba': (5, 8, 14),
    'CPP Pacaembu': (5, 8, 14),
    'Penitenciária Iaras': (5, 8, 14),
    'Penitenciária Avaré 2': (5, 9, 15),
    'CDP Praia Grande': (5, 9, 15),
    'Penitenciária Guareí 2': (5, 9, 15),
    'Penitenciária Assis': (5, 9, 15),
    'CPP Hortolândia': (5, 9, 15),
    'CDP Taubaté': (5, 9, 15),
    'CDP Mogi das Cruzes': (5, 9, 15),
    'Penitenciária Lavínia 3': (6, 10, 17),
    'Penitenciária Dracena': (6, 10, 17),
    'Penitenciária Guarulhos 2': (6, 10, 17),
    'Penitenciária Serra Azul 3': (6, 10, 17),
    'CPP Bauru 3': (6, 10, 17),
    'CDP Suzano': (6, 10, 17),
    'CDP Pinheiros 3': (6, 10, 17),
    'CDP Pacaembu 2': (6, 10, 17),
    'CDP Jundiaí': (6, 10, 18),
    'Penitenciária Piracicaba': (6, 10, 18),
    'Penitenciária Registro': (6, 10, 18),
    'CR Atibaia': (6, 10, 18),
    'CDP Pontal': (6, 10, 18),
    'CDP Osasco 1': (6, 10, 18),
    'CDP Hortolândia': (7, 11, 19),
    'Penitenciária Franco da Rocha 3': (7, 11, 19),
    'CDP Ribeirão Preto': (7, 11, 19),
    'CDP Icém': (7, 11, 19),
    'Penitenciária Osvaldo Cruz': (7, 11, 20),
    'CDP Aguaí': (7, 11, 20),
    'CPP Mongaguá': (7, 11, 20),
    'CPP Castelinho': (7, 11, 20),
    'CDP Caiuá': (7, 11, 20),
    'CDP Tijuco Preto': (7, 12, 20),
    'CPP Tremembé': (7, 12, 20),
    'Détenus Français Penit. Guarulhos II': (7, 12, 20),
    'Penitenciária Balbinos 1': (7, 12, 20),
    'CDP São José do Rio Preto': (7, 12, 20),
    'CDP Itapecerica da Serra': (7, 12, 20),
    'Penitenciária Sorocaba 2': (7, 12, 20),
    'Penitenciária Potim 1': (7, 12, 20),
    'Penitenciária Andradina': (8, 12, 21),
    'CDP Paulo de Faria': (8, 12, 21),
    'Penitenciária Florínea': (8, 12, 21),
    'Penitenciária Hortolândia 4': (8, 13, 22),
    'Penitenciária Araraquara': (8, 13, 22),
    'Penitenciária Martinópolis': (8, 13, 22),
    'Penitenciária Tremembé 2 Feminina': (8, 13, 22),
    'Penitenciária Casa Branca': (8, 13, 22),
    'P5 Hortolândia': (8, 13, 22),
    'Penitenciária Taquarituba': (8, 13, 22),
    'CDP Santo André': (8, 13, 23),
    'CDP Piracicaba': (8, 13, 23),
    'Penitenciária da Capital': (8, 13, 23),
    'Penitenciária Lavínia 1': (8, 14, 24),
    'Penitenciária Presidente Bernardes': (8, 14, 24),
    'Penitenciária Pracinha': (8, 14, 24),
    'CDP Belém 2': (8, 14, 24),
    'CDP Franco da Rocha': (8, 14, 24),
    'CDP Mauá': (8, 14, 24),
    'Penitenciaria Pontal': (8, 14, 24),
    'Penitenciária Bernardino de Campos': (8, 14, 24),
    'Penitenciária Potim 2': (9, 14, 25),
    'Penitenciária Guarulhos 1': (9, 14, 25),
    'CDP Pinheiros 4': (9, 14, 25),
    'Penitenciária Franco da Rocha 1': (9, 15, 26),
    'CDP Pinheiros 1': (9, 15, 26),
    'CDP Belém 1': (9, 15, 26),
    'CPP Jardinópolis': (9, 15, 26),
    'Penitenciária Hortolândia 2': (9, 15, 26),
    'Penitenciária Marabá Paulista': (9, 15, 26),
    'Penitenciária Tremembé 2': (9, 15, 26),
    'CPP Butantan Feminino': (9, 15, 26),
    'CR Jaú': (10, 16, 27),
    'CDP Riolândia': (10, 16, 27),
    'Penitenciária Cerqueira César 2': (10, 16, 27),
    'CR Marília': (10, 16, 27),
    'CPP São Vicente': (10, 16, 28),
    'CPP Porto Feliz': (10, 16, 28),
    'CR Itapetininga': (10, 16, 28),
    'Penitenciária Paraguaçu Paulista': (10, 16, 28),
    'Penitenciária Pirajuí 2': (10, 17, 29),
    'Penitenciária José Parada Neto': (10, 17, 29),
    'Penitenciária Taiúva': (10, 17, 30),
    'Penitenciária Tremembé 1 Feminina': (10, 17, 30),
    'Penitenciária Presidente Prudente': (11, 18, 31),
    'CPP Bauru 1': (11, 18, 31),
    'Penitenciária Capela do Alto 1': (11, 18, 31),
    'Détenus Français - Itaí': (11, 18, 31),
    'Penitenciária Reginópolis 1': (11, 18, 31),
    'CDP São Bernardo do Campo': (11, 19, 32),
    'CDP Lavínia': (11, 19, 32),
    'Penitenciaria Itatinga': (11, 19, 32),
    'Penitenciária Mogi Guaçu Feminina': (12, 20, 34),
    'Penitenciária Mairinque': (12, 20, 34),
    'CDP Osasco 2': (12, 20, 34),
    'Penitenciária Sant\'Ana Feminina': (12, 20, 34),
    'Penitenciária Tremembé 1': (12, 20, 34),
    'Penitenciária Tupi Paulista': (13, 21, 36),
    'Penitenciária Parelheiros': (13, 21, 37),
    'Penitenciária Serra Azul 2': (14, 22, 38),
    'CDP Nova Independência': (14, 23, 39),
    'Hospital de Custódia Taubaté': (14, 23, 39),
    'Penitenciária Gália 1': (14, 23, 39),
    'Penitenciária Itapetininga 2': (14, 23, 39),
    'Penitenciária Itirapina 2': (14, 23, 39),
    'Penitenciária Hortolândia 1': (14, 23, 40),
    'Penitenciária Cerqueira César 1': (15, 25, 43),
    'Penitenciária Irapuru': (16, 26, 44),
    'Penitenciária Riolândia': (16, 26, 45),
    'CR Birigui': (16, 27, 46),
    'Penitenciária Presidente Venceslau 1': (16, 27, 47),
    'Penitenciária Franca': (17, 28, 48),
    'Penitenciária Iperó': (17, 28, 48),
    'Penitenciária Pirajuí 1': (17, 28, 48),
    'Penitenciária São Vicente 2': (17, 29, 49),
    'CDP Campinas': (17, 29, 49),
    'Penitenciária Flórida Paulista': (17, 29, 49),
    'Penitenciária Lucélia': (18, 30, 51),
    'Penitenciária de Itirapina 1': (18, 30, 51),
    'Penitenciária Pirajuí Feminina': (18, 30, 51),
    'Penitenciária Itaí': (19, 31, 53),
    'CR Bragança Paulista': (19, 32, 54),
    'Penitenciária Avanhandava': (19, 32, 54),
    'Penitenciária Lavínia 2': (19, 32, 54),
    'Penitenciária Sorocaba 1': (19, 32, 54),
    'Penitenciária Álvaro de Carvalho 2': (20, 32, 55),
    'Penitenciaria Caiuá': (20, 32, 55),
    'CR de Araraquara': (20, 33, 56),
    'Penitenciária Marília': (20, 34, 58),
    'José Parada Neto – Semiaberto (RSA)': (20, 34, 58),
    'Penitenciária Hortolândia 3': (22, 36, 61),
    'CPP Bauru 2': (23, 38, 65),
    'CPP de Campinas -Professor Ataliba Nogueira': (28, 46, 78),
    'CDP Pacaembu 1': (28, 47, 80),
    'Penitenciária Serra Azul 1': (28, 47, 80),
    'Penitenciária Álvaro de Carvalho': (28, 47, 80),
}

# ─── FUNÇÕES AUXILIARES ──────────────────────────────────────────────────────
def converter_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lote_Disparo')
    return output.getvalue()

def normalizar_unidade(nome):
    """Remove espaços extras e normaliza o nome da unidade."""
    return str(nome).strip()

def obter_gatilhos(unidade):
    """Retorna (ant, med, cri) para a unidade. Tenta match exato, depois fallback."""
    if unidade in MAPEAMENTO_UNIDADES:
        return MAPEAMENTO_UNIDADES[unidade], True

    # Fallback: busca por substring para lidar com variações de espaço
    for chave, gatilhos in MAPEAMENTO_UNIDADES.items():
        if chave.lower() in unidade.lower() or unidade.lower() in chave.lower():
            return gatilhos, True

    # Fallback final: mediana geral da operação (14 dias)
    return (8, 14, 24), False

def enviar_webhook(url, dados, nome_lote):
    """Envia dados para webhook e retorna (sucesso, mensagem)."""
    try:
        res = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(dados, default=str),
            timeout=15
        )
        if res.status_code in [200, 201]:
            return True, f"✅ {len(dados)} contatos enviados para {nome_lote}!"
        else:
            return False, f"❌ Erro em {nome_lote}. Status HTTP: {res.status_code}"
    except requests.exceptions.Timeout:
        return False, f"❌ Timeout em {nome_lote} — o n8n demorou mais de 15s."
    except Exception as e:
        return False, f"❌ Falha de conexão em {nome_lote}: {e}"

def exibir_lote(df_grupo, titulo, nome_arquivo, cor_badge):
    st.subheader(titulo)
    if not df_grupo.empty:
        st.dataframe(df_grupo, use_container_width=True)
        dados_excel = converter_para_excel(df_grupo)
        st.download_button(
            label=f"📥 Baixar {titulo} (.xlsx)",
            data=dados_excel,
            file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info(f"Nenhum cliente elegível para {titulo} hoje.")
    st.divider()

# ─── UPLOAD ──────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Arraste o relatório de vendas aqui (CSV ou Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:
    try:
        df = None

        # Tentativa 1: Excel
        try:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file)
        except Exception:
            pass

        # Tentativa 2: CSV com múltiplos encodings
        if df is None or df.shape[1] <= 1:
            for sep, enc in [(';', 'utf-8-sig'), (';', 'iso-8859-1'), (',', 'utf-8'), (';', 'utf-8'), (',', 'iso-8859-1')]:
                try:
                    uploaded_file.seek(0)
                    temp = pd.read_csv(uploaded_file, sep=sep, encoding=enc, on_bad_lines='skip')
                    if temp.shape[1] > 1:
                        df = temp
                        break
                except Exception:
                    continue

        if df is None or 'Data' not in df.columns:
            st.error("❌ Arquivo não reconhecido. Verifique se a coluna 'Data' existe.")
            st.stop()

        # ─── LIMPEZA ─────────────────────────────────────────────────────────
        # Normalizar nomes de colunas para evitar variações de case/espaço
        df.columns = df.columns.str.strip()

        # Filtro: apenas clientes com pedidos realmente enviados
        col_env = next((c for c in df.columns if c.lower().strip() == 'quant. pedidos enviados'), None)
        if col_env:
            df = df[df[col_env] >= 1].copy()

        # Conversão de data forçando padrão brasileiro
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True).dt.tz_localize(None)
        today = pd.to_datetime(datetime.now().date())
        df['Days_Since'] = (today - df['Data']).dt.days

        # Normalizar nomes de unidade
        df['Unidade Prisional'] = df['Unidade Prisional'].apply(normalizar_unidade)

        # Manter apenas o pedido mais recente por cliente
        df = df.sort_values('Data', ascending=False).drop_duplicates(subset=['Codigo Cliente'], keep='first')

        # ─── SIDEBAR ─────────────────────────────────────────────────────────
        todas_unidades = sorted(df['Unidade Prisional'].dropna().unique())
        unidades_nao_mapeadas = set()

        st.sidebar.metric("🏢 Unidades no relatório", f"{len(todas_unidades)} unidades")
        st.sidebar.metric("👥 Clientes únicos", f"{df['Codigo Cliente'].nunique():,}")
        unidade_selecionada = st.sidebar.selectbox(
            "🔍 Auditar unidade específica:",
            ["Ver Todas"] + todas_unidades
        )

        # ─── MOTOR DE CLASSIFICAÇÃO ───────────────────────────────────────────
        lote_antecipacao, lote_mediana, lote_critico = [], [], []

        for _, row in df.iterrows():
            dias = row['Days_Since']
            unidade = row['Unidade Prisional']
            (ant, med, cri), mapeado = obter_gatilhos(unidade)

            if not mapeado:
                unidades_nao_mapeadas.add(unidade)

            # Janela de ±1 dia para não perder clientes em dias sem execução
            if ant - 1 <= dias <= ant + 1:
                lote_antecipacao.append(row)
            elif med - 1 <= dias <= med + 1:
                lote_mediana.append(row)
            elif cri - 1 <= dias <= cri + 1:
                lote_critico.append(row)

        # Avisar sobre unidades no fallback
        if unidades_nao_mapeadas:
            st.sidebar.warning(
                f"⚠️ {len(unidades_nao_mapeadas)} unidade(s) usando mediana geral (14 dias):\n\n" +
                "\n".join(f"• {u}" for u in sorted(unidades_nao_mapeadas))
            )

        # ─── MONTAR DATAFRAMES ───────────────────────────────────────────────
        cols_drop = ['Days_Since']

        df_ant = pd.DataFrame(lote_antecipacao).drop(columns=cols_drop, errors='ignore') if lote_antecipacao else pd.DataFrame()
        df_med = pd.DataFrame(lote_mediana).drop(columns=cols_drop, errors='ignore') if lote_mediana else pd.DataFrame()
        df_cri = pd.DataFrame(lote_critico).drop(columns=cols_drop, errors='ignore') if lote_critico else pd.DataFrame()

        # Filtro de auditoria por unidade
        if unidade_selecionada != "Ver Todas":
            df_ant = df_ant[df_ant['Unidade Prisional'] == unidade_selecionada] if not df_ant.empty else df_ant
            df_med = df_med[df_med['Unidade Prisional'] == unidade_selecionada] if not df_med.empty else df_med
            df_cri = df_cri[df_cri['Unidade Prisional'] == unidade_selecionada] if not df_cri.empty else df_cri

        # ─── MÉTRICAS ────────────────────────────────────────────────────────
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📋 Clientes processados", f"{len(df):,}")
        col2.metric("📅 Lote 1 — Antecipação", f"{len(df_ant)} contatos")
        col3.metric("🎯 Lote 2 — Mediana", f"{len(df_med)} contatos")
        col4.metric("🚨 Lote 3 — Crítico", f"{len(df_cri)} contatos")
        st.divider()

        # ─── EXIBIÇÃO DOS LOTES ───────────────────────────────────────────────
        exibir_lote(df_ant, "1. Lote Antecipação", "lote_antecipacao", "blue")
        exibir_lote(df_med, "2. Lote Mediana de Precisão", "lote_mediana", "green")
        exibir_lote(df_cri, "3. Lote Alerta Crítico", "lote_critico", "red")

        # ─── DISPARO PARA O n8n ───────────────────────────────────────────────
        st.subheader("🔥 Central de Disparo Automatizado")

        total_contatos = len(df_ant) + len(df_med) + len(df_cri)
        if total_contatos == 0:
            st.info("Nenhum cliente elegível para disparo hoje. Tente amanhã ou revise o período do relatório.")
        else:
            st.info(f"**{total_contatos} contatos** prontos para disparo nos 3 fluxos do n8n.")
            if st.button("🚀 Disparar Mensagens Inteligentes para o n8n", type="primary", use_container_width=True):
                resultados = []
                sucesso_geral = True

                if not df_ant.empty:
                    ok, msg = enviar_webhook(WEBHOOK_ANTECIPACAO, df_ant.to_dict(orient='records'), "Antecipação")
                    resultados.append((ok, msg))
                    if not ok: sucesso_geral = False

                if not df_med.empty:
                    ok, msg = enviar_webhook(WEBHOOK_MEDIANA, df_med.to_dict(orient='records'), "Mediana")
                    resultados.append((ok, msg))
                    if not ok: sucesso_geral = False

                if not df_cri.empty:
                    ok, msg = enviar_webhook(WEBHOOK_CRITICO, df_cri.to_dict(orient='records'), "Crítico")
                    resultados.append((ok, msg))
                    if not ok: sucesso_geral = False

                for ok, msg in resultados:
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

                if sucesso_geral:
                    st.balloons()
                    st.success("🎉 Todos os fluxos foram enviados com sucesso ao n8n!")

    except Exception as e:
        st.error(f"Erro crítico no processamento: {e}")
        st.exception(e)
