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
def load_single_sheet_data(file):
    return pd.read_excel(file)

def salvar_planilhas(arquivo_usuarios, arquivo_acessos):
    """Salva as planilhas carregadas na pasta data"""
    try:
        # Criar pasta data se não existir
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        arquivos_salvos = {}
        
        if arquivo_usuarios is not None:
            nome_arquivo = f"data/usuarios_ambientes_{timestamp}.xlsx"
            with open(nome_arquivo, "wb") as f:
                f.write(arquivo_usuarios.getbuffer())
            arquivos_salvos['usuarios'] = nome_arquivo
            
        if arquivo_acessos is not None:
            nome_arquivo = f"data/acessos_{timestamp}.xlsx"
            with open(nome_arquivo, "wb") as f:
                f.write(arquivo_acessos.getbuffer())
            arquivos_salvos['acessos'] = nome_arquivo
        
        # Salvar informações dos últimos arquivos
        with open("data/ultimos_arquivos.txt", "w") as f:
            for tipo, caminho in arquivos_salvos.items():
                f.write(f"{tipo}:{caminho}\n")
        
        return arquivos_salvos
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {str(e)}")
    return {}

def carregar_ultimas_planilhas():
    """Carrega as últimas planilhas salvas"""
    try:
        arquivos = {}
        if os.path.exists("data/ultimos_arquivos.txt"):
            with open("data/ultimos_arquivos.txt", "r") as f:
                for linha in f:
                    if ':' in linha:
                        tipo, caminho = linha.strip().split(':', 1)
                        if os.path.exists(caminho):
                            arquivos[tipo] = caminho
        return arquivos
    except Exception as e:
        st.warning(f"Erro ao carregar últimas planilhas: {str(e)}")
    return {}

def processar_datas_modulos(df):
    """Processa as datas dos módulos, suportando formato com e sem hora"""
    if 'DataInicioModulo' in df.columns:
        # Tentar primeiro com formato de data e hora
        df['DataInicioModulo'] = pd.to_datetime(df['DataInicioModulo'], dayfirst=True, errors='coerce')
        # Se não funcionou, tentar formato apenas data
        mask_nulos = df['DataInicioModulo'].isna()
        if mask_nulos.any():
            df.loc[mask_nulos, 'DataInicioModulo'] = pd.to_datetime(
                df.loc[mask_nulos, 'DataInicioModulo'], 
                format='%d/%m/%Y', 
                errors='coerce'
            )
    
    if 'DataConclusaoModulo' in df.columns:
        # Tentar primeiro com formato de data e hora
        df['DataConclusaoModulo'] = pd.to_datetime(df['DataConclusaoModulo'], dayfirst=True, errors='coerce')
        # Se não funcionou, tentar formato apenas data
        mask_nulos = df['DataConclusaoModulo'].isna()
        if mask_nulos.any():
            df.loc[mask_nulos, 'DataConclusaoModulo'] = pd.to_datetime(
                df.loc[mask_nulos, 'DataConclusaoModulo'], 
                format='%d/%m/%Y', 
                errors='coerce'
            )
    
    return df

def get_filtros_gerais(dados_usuarios, dados_acessos):
    """Retorna todos os filtros disponíveis a partir dos DataFrames"""
    if dados_usuarios is not None and dados_acessos is not None:
        df_ambientes = dados_usuarios.copy()
        df_acessos = dados_acessos.copy()
        
        # Processar datas dos módulos
        df_ambientes = processar_datas_modulos(df_ambientes)
        
        # Verificações de colunas essenciais
        colunas_essenciais_acessos = ['DataAcesso', 'UsuarioID']
        colunas_essenciais_ambientes = ['UsuarioID']
        
        for col in colunas_essenciais_acessos:
            if col not in df_acessos.columns:
                st.error(f"A coluna '{col}' não foi encontrada nos dados de 'Acessos'.")
                return None
        for col in colunas_essenciais_ambientes:
            if col not in df_ambientes.columns:
                st.error(f"A coluna '{col}' não foi encontrada nos dados de 'UsuariosAmbientes'.")
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
        datas_inicio_modulo = df_ambientes['DataInicioModulo'].dropna() if 'DataInicioModulo' in df_ambientes.columns else pd.Series([])
        data_inicio_total = min(datas_acesso.min(), datas_inicio_modulo.min()) if not datas_inicio_modulo.empty else datas_acesso.min()
        data_fim_total = max(datas_acesso.max(), datas_inicio_modulo.max()) if not datas_inicio_modulo.empty else datas_acesso.max()
        data_inicio_total = pd.to_datetime(data_inicio_total).date()
        data_fim_total = pd.to_datetime(data_fim_total).date()
        
        # Usar data atual para cálculos de períodos recentes
        data_hoje = pd.to_datetime('today').date()
        
        ano_atual = data_hoje.year
        ano_passado = ano_atual - 1
        inicio_ano_atual = pd.to_datetime(f"01/01/{ano_atual}", dayfirst=True).date()
        fim_ano_atual = pd.to_datetime(f"31/12/{ano_atual}", dayfirst=True).date()
        inicio_ano_passado = pd.to_datetime(f"01/01/{ano_passado}", dayfirst=True).date()
        fim_ano_passado = pd.to_datetime(f"31/12/{ano_passado}", dayfirst=True).date()
        
        opcoes_periodo = {
            'Período completo': (data_inicio_total, data_fim_total),
            'Últimos 7 dias': (data_hoje - pd.Timedelta(days=6), data_hoje + pd.Timedelta(days=1)),
            'Últimos 30 dias': (data_hoje - pd.Timedelta(days=29), data_hoje + pd.Timedelta(days=1)),
            'Este mês': (data_hoje.replace(day=1), data_hoje),
            'Mês passado': ((data_hoje.replace(day=1) - pd.Timedelta(days=1)).replace(day=1), data_hoje.replace(day=1) - pd.Timedelta(days=1)),
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
        st.error("É necessário carregar os dados de 'UsuariosAmbientes' e 'Acessos'.")
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

# Interface de upload flexível
st.header("📊 Dashboard de Acessos")
st.markdown("---")

dados_usuarios = None
dados_acessos = None

# Tentar carregar dados salvos automaticamente
ultimas_planilhas = carregar_ultimas_planilhas()
if ultimas_planilhas and 'usuarios' in ultimas_planilhas and 'acessos' in ultimas_planilhas:
    try:
        dados_usuarios = pd.read_excel(ultimas_planilhas['usuarios'])
        dados_acessos = pd.read_excel(ultimas_planilhas['acessos'])
        st.success("✅ Dados carregados automaticamente da última sessão!")
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar dados salvos: {str(e)}")

# Interface de upload de planilhas separadas
st.subheader("📋 Carregar Dados")

col1, col2 = st.columns(2)

with col1:
    st.info("👥 Dados de Usuários e Ambientes")
    arquivo_usuarios = st.file_uploader(
        "Upload da planilha UsuariosAmbientes", 
        type=["xlsx"], 
        key="usuarios"
    )
    
    if arquivo_usuarios:
        try:
            dados_usuarios = load_single_sheet_data(arquivo_usuarios)
            st.success("✅ Dados de usuários carregados!")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados de usuários: {str(e)}")

with col2:
    st.info("🔐 Dados de Acessos")
    arquivo_acessos = st.file_uploader(
        "Upload da planilha Acessos", 
        type=["xlsx"], 
        key="acessos"
    )
    
    if arquivo_acessos:
        try:
            dados_acessos = load_single_sheet_data(arquivo_acessos)
            st.success("✅ Dados de acessos carregados!")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados de acessos: {str(e)}")

# Salvar arquivos automaticamente quando ambos forem carregados
if arquivo_usuarios and arquivo_acessos and dados_usuarios is not None and dados_acessos is not None:
    arquivos_salvos = salvar_planilhas(
        arquivo_usuarios=arquivo_usuarios, 
        arquivo_acessos=arquivo_acessos
    )
    st.success("💾 Dados salvos automaticamente para a próxima sessão!")

# Processar dados se disponíveis
if dados_usuarios is not None and dados_acessos is not None:
    filtros_disponiveis = get_filtros_gerais(dados_usuarios, dados_acessos)
    if filtros_disponiveis is not None:
        # Criar as abas
        tab1, tab2 = st.tabs(["Visão Geral", "Acessos"])
        
        with tab1:
            st.header("Visão Geral")
            st.markdown("""
            Painel com os principais dados sobre desempenho nos treinamentos: participações, finalizações, horas dedicadas e usuários ou ambientes mais ativos. Use os filtros para explorar os resultados por perfil, trilha, módulo ou período.
            
            Para mais informações sobre este relatório, clique aqui.
            """)
            filtros_visao_geral = mostrar_filtros_visao_geral(filtros_disponiveis)
            
            # Primeira linha de gráficos: 04 e 05, proporção 60/40
            col_g4, col_g5 = st.columns([3,2])
            with col_g4:
                performance_modulos.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_visao_geral)
            with col_g5:
                engajamento_modulos.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_visao_geral)
            
            st.markdown('---')
            
            # Segunda linha de gráficos: 06, 07 e 08
            col_g6, col_g7, col_g8 = st.columns(3)
            with col_g6:
                horas_treinadas.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_visao_geral)
            with col_g7:
                ambientes_mais_participacoes.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_visao_geral)
            with col_g8:
                usuarios_mais_engajados.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_visao_geral)
        
        with tab2:
            st.header("Acessos")
            st.markdown("""
            Mostra como os usuários estão acessando a trilha: nível de engajamento, frequência de acessos e tipo de dispositivo usado. Ideal para entender o comportamento de uso ao longo do tempo.
            
            Para mais informações sobre este relatório, clique aqui.
            """)
            filtros_acessos = mostrar_filtros_acessos(filtros_disponiveis)
            
            # Gráficos de acessos
            col1, col2, col3 = st.columns(3)
            with col1:
                engajamento.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_acessos)
            with col2:
                acessos.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_acessos)
            with col3:
                acessos_dispositivo.app({'UsuariosAmbientes': dados_usuarios, 'Acessos': dados_acessos}, filtros_acessos)
else:
    st.info("📋 Para começar, faça upload das duas planilhas acima ou aguarde o carregamento automático dos dados salvos.")