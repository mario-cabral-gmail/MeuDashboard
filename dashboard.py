import streamlit as st
import engajamento_01 as engajamento
import acessos_02 as acessos
import acessos_dispositivo_03 as acessos_dispositivo
import performance_modulos_04 as performance_modulos
import engajamento_modulos_05 as engajamento_modulos
import horas_treinadas_06 as horas_treinadas
import ambientes_mais_participacoes_07 as ambientes_mais_participacoes
import usuarios_mais_engajados_08 as usuarios_mais_engajados
import pandas as pd
import altair as alt
import locale
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Acessos",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)


# Configuração de cache para melhor performance
@st.cache_data(ttl=3600)
def load_excel_data(file):
    return pd.read_excel(file, sheet_name=None)

@st.cache_data(ttl=3600)
def process_data(abas):
    if 'UsuariosAmbientes' in abas and 'Acessos' in abas:
        return abas['UsuariosAmbientes'], abas['Acessos']
    return None, None

def salvar_planilha(arquivo):
    """Salva a planilha carregada na pasta data"""
    try:
        if arquivo is not None:
            # Criar pasta data se não existir
            os.makedirs("data", exist_ok=True)
            
            # Salvar arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"data/planilha_{timestamp}.xlsx"
            
            with open(nome_arquivo, "wb") as f:
                f.write(arquivo.getbuffer())
            
            # Salvar nome do último arquivo
            with open("data/ultimo_arquivo.txt", "w") as f:
                f.write(nome_arquivo)
            
            return nome_arquivo
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {str(e)}")
    return None

def carregar_ultima_planilha():
    """Carrega a última planilha salva"""
    try:
        if os.path.exists("data/ultimo_arquivo.txt"):
            with open("data/ultimo_arquivo.txt", "r") as f:
                ultimo_arquivo = f.read().strip()
                if os.path.exists(ultimo_arquivo):
                    return ultimo_arquivo
    except Exception as e:
        st.warning(f"Erro ao carregar última planilha: {str(e)}")
    return None

def get_filtros_gerais(arquivo):
    """Retorna todos os filtros disponíveis"""
    if isinstance(arquivo, str):
        abas = pd.read_excel(arquivo, sheet_name=None)
    else:
        abas = pd.read_excel(arquivo, sheet_name=None)
    
    if 'UsuariosAmbientes' in abas and 'Acessos' in abas:
        df_ambientes = abas['UsuariosAmbientes']
        df_acessos = abas['Acessos']
        
        # Verificações de colunas essenciais
        colunas_essenciais_acessos = ['DataAcesso', 'UsuarioID']
        colunas_essenciais_ambientes = ['UsuarioID']
        
        for col in colunas_essenciais_acessos:
            if col not in df_acessos.columns:
                st.error(f"A coluna '{col}' não foi encontrada na aba 'Acessos'.")
                return None
        for col in colunas_essenciais_ambientes:
            if col not in df_ambientes.columns:
                st.error(f"A coluna '{col}' não foi encontrada na aba 'UsuariosAmbientes'.")
                return None
        
        # Preparação dos dados para filtros
        ambientes_unicos = sorted(df_ambientes['NomeAmbiente'].dropna().unique()) if 'NomeAmbiente' in df_ambientes.columns else []
        perfis_unicos = sorted(df_ambientes['PerfilNaTrilha'].dropna().unique()) if 'PerfilNaTrilha' in df_ambientes.columns else []
        default_perfis = [p for p in ['Obrigatório', 'Participa'] if p in perfis_unicos]
        trilhas_unicas = sorted(df_ambientes['NomeTrilha'].dropna().unique()) if 'NomeTrilha' in df_ambientes.columns else []
        modulos_unicos = sorted(df_ambientes['NomeModulo'].dropna().unique()) if 'NomeModulo' in df_ambientes.columns else []
        grupos_unicos = sorted(df_ambientes['TodosGruposUsuario'].dropna().unique()) if 'TodosGruposUsuario' in df_ambientes.columns else []
        status_unicos = sorted(df_acessos['StatusUsuario'].dropna().unique()) if 'StatusUsuario' in df_acessos.columns else []
        
        # Cálculo do período
        datas_acesso = pd.to_datetime(df_acessos['DataAcesso'], dayfirst=True, errors='coerce').dropna()
        datas_inicio_modulo = pd.to_datetime(df_ambientes['DataInicioModulo'], format='%d/%m/%Y', errors='coerce').dropna() if 'DataInicioModulo' in df_ambientes.columns else pd.Series([])
        data_inicio_total = min(datas_acesso.min(), datas_inicio_modulo.min()) if not datas_inicio_modulo.empty else datas_acesso.min()
        data_fim_total = max(datas_acesso.max(), datas_inicio_modulo.max()) if not datas_inicio_modulo.empty else datas_acesso.max()
        data_inicio_total = pd.to_datetime(data_inicio_total).date()
        data_fim_total = pd.to_datetime(data_fim_total).date()
        
        ano_atual = data_fim_total.year
        ano_passado = ano_atual - 1
        inicio_ano_atual = pd.to_datetime(f"01/01/{ano_atual}", dayfirst=True).date()
        fim_ano_atual = pd.to_datetime(f"31/12/{ano_atual}", dayfirst=True).date()
        inicio_ano_passado = pd.to_datetime(f"01/01/{ano_passado}", dayfirst=True).date()
        fim_ano_passado = pd.to_datetime(f"31/12/{ano_passado}", dayfirst=True).date()
        
        inicio_ano_atual = max(inicio_ano_atual, data_inicio_total)
        fim_ano_atual = min(fim_ano_atual, data_fim_total)
        inicio_ano_passado = max(inicio_ano_passado, data_inicio_total)
        fim_ano_passado = min(fim_ano_passado, data_fim_total)
        
        opcoes_periodo = {
            'Período completo': (data_inicio_total, data_fim_total),
            'Últimos 7 dias': (data_fim_total - pd.Timedelta(days=6), data_fim_total),
            'Últimos 30 dias': (data_fim_total - pd.Timedelta(days=29), data_fim_total),
            'Este mês': (data_fim_total.replace(day=1), data_fim_total),
            'Mês passado': ((data_fim_total.replace(day=1) - pd.Timedelta(days=1)).replace(day=1), data_fim_total.replace(day=1) - pd.Timedelta(days=1)),
            'Este ano': (inicio_ano_atual, fim_ano_atual),
            'Ano passado': (inicio_ano_passado, fim_ano_passado),
            'Personalizado': None
        }
        
        return {
            'ambientes': ambientes_unicos,
            'perfis': perfis_unicos,
            'default_perfis': default_perfis,
            'trilhas': trilhas_unicas,
            'modulos': modulos_unicos,
            'grupos': grupos_unicos,
            'status': status_unicos,
            'opcoes_periodo': opcoes_periodo,
            'data_inicio_total': data_inicio_total,
            'data_fim_total': data_fim_total
        }
    else:
        st.error("Sua planilha precisa ter as abas 'UsuariosAmbientes' e 'Acessos'.")
        return None

def mostrar_filtros_visao_geral(filtros_disponiveis):
    """Mostra os filtros para a aba Visão Geral"""
    colf1, colf2, colf3, colf4, colf5, colf6, colf7, colf8 = st.columns(8)
    
    ambiente_selecionado = colf1.multiselect("Filtrar por ambiente:", filtros_disponiveis['ambientes'], key="ambiente_visao_geral")
    perfil_selecionado = colf2.multiselect("Filtrar por perfil:", filtros_disponiveis['perfis'], default=filtros_disponiveis['default_perfis'], key="perfil_visao_geral")
    trilha_selecionada = colf3.multiselect("Filtrar por trilha:", filtros_disponiveis['trilhas'], key="trilha_visao_geral")
    modulo_selecionado = colf4.multiselect("Filtrar por módulo:", filtros_disponiveis['modulos'], key="modulo_visao_geral")
    grupo_selecionado = colf5.multiselect("Filtrar por grupo:", filtros_disponiveis['grupos'], key="grupo_visao_geral")
    status_selecionado = colf6.multiselect("Status do Usuário:", filtros_disponiveis['status'], default=[s for s in filtros_disponiveis['status'] if s.lower() == 'ativo'], key="status_visao_geral")
    
    with colf7:
        escolha_periodo = st.selectbox("Período:", list(filtros_disponiveis['opcoes_periodo'].keys()), index=0, key="periodo_visao_geral")
        if escolha_periodo != 'Personalizado':
            periodo = filtros_disponiveis['opcoes_periodo'][escolha_periodo]
        else:
            periodo = st.date_input(
                "Selecione o período:",
                value=(filtros_disponiveis['data_inicio_total'], filtros_disponiveis['data_fim_total']),
                min_value=filtros_disponiveis['data_inicio_total'],
                max_value=filtros_disponiveis['data_fim_total'],
                format="DD/MM/YYYY",
                key="periodo_personalizado_visao_geral"
            )
    
    with colf8:
        incluir_sem_data = st.checkbox("Incluir registros sem data", value=False, key="sem_data_visao_geral")
    
    return {
        "ambiente": ambiente_selecionado,
        "perfil": perfil_selecionado,
        "trilha": trilha_selecionada,
        "modulo": modulo_selecionado,
        "grupo": grupo_selecionado,
        "status_usuario": status_selecionado,
        "periodo": periodo,
        "incluir_sem_data": incluir_sem_data
    }

def mostrar_filtros_acessos(filtros_disponiveis):
    """Mostra os filtros para a aba Acessos"""
    colf1, colf2, colf3, colf4 = st.columns(4)
    
    perfil_selecionado = colf1.multiselect("Filtrar por perfil na trilha:", filtros_disponiveis['perfis'], default=filtros_disponiveis['default_perfis'], key="perfil_acessos")
    grupo_selecionado = colf2.multiselect("Filtrar por grupo:", filtros_disponiveis['grupos'], key="grupo_acessos")
    status_selecionado = colf3.multiselect("Status do Usuário:", filtros_disponiveis['status'], default=[s for s in filtros_disponiveis['status'] if s.lower() == 'ativo'], key="status_acessos")
    
    with colf4:
        escolha_periodo = st.selectbox("Período:", list(filtros_disponiveis['opcoes_periodo'].keys()), index=0, key="periodo_acessos")
        if escolha_periodo != 'Personalizado':
            periodo = filtros_disponiveis['opcoes_periodo'][escolha_periodo]
        else:
            periodo = st.date_input(
                "Selecione o período:",
                value=(filtros_disponiveis['data_inicio_total'], filtros_disponiveis['data_fim_total']),
                min_value=filtros_disponiveis['data_inicio_total'],
                max_value=filtros_disponiveis['data_fim_total'],
                format="DD/MM/YYYY",
                key="periodo_personalizado_acessos"
            )
    
    return {
        "perfil": perfil_selecionado,
        "grupo": grupo_selecionado,
        "status_usuario": status_selecionado,
        "periodo": periodo,
        "incluir_sem_data": False
    }

# Carregar última planilha se existir
ultima_planilha = carregar_ultima_planilha()

# Upload de nova planilha
arquivo = st.file_uploader("Faça upload da planilha Excel", type=["xlsx"])

# Se houver upload de nova planilha, salva e usa ela
if arquivo:
    nome_arquivo = salvar_planilha(arquivo)
    arquivo_atual = arquivo
# Se não houver upload mas existir última planilha, usa ela
elif ultima_planilha:
    arquivo_atual = ultima_planilha
    st.success("Carregando última planilha salva...")
# Se não houver upload nem última planilha, tenta carregar data/Carga.xlsx
elif os.path.exists("data/Carga.xlsx"):
    arquivo_atual = "data/Carga.xlsx"
    st.info("Carregando planilha padrão: data/Carga.xlsx")
else:
    arquivo_atual = None

if arquivo_atual:
    filtros_disponiveis = get_filtros_gerais(arquivo_atual)
    if filtros_disponiveis is not None:
        # Criar as abas
        tab1, tab2 = st.tabs(["Visão Geral", "Acessos"])
        
        with tab1:
            st.header("Visão Geral")
            filtros_visao_geral = mostrar_filtros_visao_geral(filtros_disponiveis)
            
            # Primeira linha de gráficos
            col_g4, col_g5, col_g6 = st.columns(3)
            with col_g4:
                performance_modulos.app(arquivo_atual, filtros_visao_geral)
            with col_g5:
                engajamento_modulos.app(arquivo_atual, filtros_visao_geral)
            with col_g6:
                horas_treinadas.app(arquivo_atual, filtros_visao_geral)
            
            st.markdown('---')
            
            # Segunda linha de gráficos
            col_g7, col_g8 = st.columns(2)
            with col_g7:
                ambientes_mais_participacoes.app(arquivo_atual, filtros_visao_geral)
            with col_g8:
                usuarios_mais_engajados.app(arquivo_atual, filtros_visao_geral)
        
        with tab2:
            st.header("Acessos")
            filtros_acessos = mostrar_filtros_acessos(filtros_disponiveis)
            
            # Gráficos de acessos
            col1, col2, col3 = st.columns(3)
            with col1:
                engajamento.app(arquivo_atual, filtros_acessos)
            with col2:
                acessos.app(arquivo_atual, filtros_acessos)
            with col3:
                acessos_dispositivo.app(arquivo_atual, filtros_acessos)
else:
    st.info("Por favor, faça upload da planilha Excel original.")