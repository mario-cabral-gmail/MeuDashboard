import streamlit as st
import grafico1
import grafico2
import pandas as pd
import altair as alt
import locale

# Configuração da página
st.set_page_config(page_title="Dashboard de Acessos", layout="wide", page_icon="📊")

arquivo = st.file_uploader("Faça upload da planilha Excel", type=["xlsx"])

# Centralizar filtros no topo
def get_filtros(arquivo):
    abas = pd.read_excel(arquivo, sheet_name=None)
    if 'UsuariosAmbientes' in abas and 'Acessos' in abas:
        df_ambientes = abas['UsuariosAmbientes']
        df_acessos = abas['Acessos']
        ambientes_unicos = sorted(df_ambientes['NomeAmbiente'].dropna().unique()) if 'NomeAmbiente' in df_ambientes.columns else []
        perfis_unicos = sorted(df_ambientes['PerfilNaTrilha'].dropna().unique()) if 'PerfilNaTrilha' in df_ambientes.columns else []
        default_perfis = [p for p in ['Obrigatório', 'Participa'] if p in perfis_unicos]
        trilhas_unicas = sorted(df_ambientes['NomeTrilha'].dropna().unique()) if 'NomeTrilha' in df_ambientes.columns else []
        modulos_unicos = sorted(df_ambientes['NomeModulo'].dropna().unique()) if 'NomeModulo' in df_ambientes.columns else []
        grupos_unicos = sorted(df_ambientes['TodosGruposUsuario'].dropna().unique()) if 'TodosGruposUsuario' in df_ambientes.columns else []
        colf1, colf2, colf3, colf4, colf5 = st.columns(5)
        ambiente_selecionado = colf1.multiselect("Filtrar por ambiente:", ambientes_unicos, key="ambiente_dashboard")
        perfil_selecionado = colf2.multiselect("Filtrar por perfil na trilha:", perfis_unicos, default=default_perfis, key="perfil_dashboard")
        trilha_selecionada = colf3.multiselect("Filtrar por trilha:", trilhas_unicas, key="trilha_dashboard")
        modulo_selecionado = colf4.multiselect("Filtrar por módulo:", modulos_unicos, key="modulo_dashboard")
        grupo_selecionado = colf5.multiselect("Filtrar por grupo:", grupos_unicos, key="grupo_dashboard")
        # Período
        # Unir datas de acesso e de início de módulo para pegar o range total
        datas_acesso = pd.to_datetime(df_acessos['DataAcesso'], dayfirst=True, errors='coerce').dropna()
        datas_inicio_modulo = pd.to_datetime(df_ambientes['DataInicioModulo'], dayfirst=True, errors='coerce').dropna() if 'DataInicioModulo' in df_ambientes.columns else pd.Series([])
        data_inicio_total = min(datas_acesso.min(), datas_inicio_modulo.min()) if not datas_inicio_modulo.empty else datas_acesso.min()
        data_fim_total = max(datas_acesso.max(), datas_inicio_modulo.max()) if not datas_inicio_modulo.empty else datas_acesso.max()
        st.markdown("### Período")
        opcoes_periodo = {
            'Período completo': (data_inicio_total, data_fim_total),
            'Últimos 7 dias': (data_fim_total - pd.Timedelta(days=6), data_fim_total),
            'Últimos 30 dias': (data_fim_total - pd.Timedelta(days=29), data_fim_total),
            'Este mês': (data_fim_total.replace(day=1), data_fim_total),
            'Mês passado': ((data_fim_total.replace(day=1) - pd.Timedelta(days=1)).replace(day=1), data_fim_total.replace(day=1) - pd.Timedelta(days=1)),
            'Personalizado': None
        }
        escolha_periodo = st.selectbox("Selecione um período rápido ou escolha personalizado:", list(opcoes_periodo.keys()), index=0)
        if escolha_periodo != 'Personalizado':
            periodo = opcoes_periodo[escolha_periodo]
        else:
            periodo = st.date_input(
                "Selecione o período:",
                value=(data_inicio_total, data_fim_total),
                min_value=data_inicio_total,
                max_value=data_fim_total,
                format="DD/MM/YYYY"
            )
        filtros = {
            "ambiente": ambiente_selecionado,
            "perfil": perfil_selecionado,
            "trilha": trilha_selecionada,
            "modulo": modulo_selecionado,
            "grupo": grupo_selecionado,
            "periodo": periodo
        }
        return filtros
    else:
        st.error("Sua planilha precisa ter as abas 'UsuariosAmbientes' e 'Acessos'.")
        return None

if arquivo:
    filtros = get_filtros(arquivo)
    if filtros is not None:
        col1, col2 = st.columns(2)
        with col1:
            grafico1.app(arquivo, filtros)
        with col2:
            grafico2.app(arquivo, filtros)
else:
    st.info("Por favor, faça upload da planilha Excel original.")