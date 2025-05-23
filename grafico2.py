import streamlit as st
import pandas as pd
import altair as alt
import locale
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Dashboard de Acessos", layout="wide", page_icon="📊")


# Título e descrição
st.title("📊 Dashboard de Acessos")
st.markdown("Visualize os acessos por dia, ambiente, perfil, trilha, módulo e grupo de forma interativa e moderna.")

def app():
    st.title("Engajamento")
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        pass
    arquivo = st.file_uploader("Faça upload da planilha Excel", type=["xlsx"])
    if arquivo:
        abas = pd.read_excel(arquivo, sheet_name=None)
        if 'Acessos' in abas and 'UsuariosAmbientes' in abas:
            df_acessos = abas['Acessos']
            df_ambientes = abas['UsuariosAmbientes']
            if 'DataAcesso' in df_acessos.columns:
                df_acessos['DataAcesso'] = pd.to_datetime(df_acessos['DataAcesso'], dayfirst=True, errors='coerce').dt.date
            if 'DataCadastro' in df_ambientes.columns:
                df_ambientes['DataCadastro'] = pd.to_datetime(df_ambientes['DataCadastro'], dayfirst=True, errors='coerce').dt.date
            st.markdown("### Filtros")
            colf1, colf2, colf3, colf4, colf5 = st.columns(5)
            ambiente_selecionado = perfil_selecionado = trilha_selecionada = modulo_selecionado = grupo_selecionado = None
            if 'NomeAmbiente' in df_ambientes.columns:
                ambientes_unicos = sorted(df_ambientes['NomeAmbiente'].dropna().unique())
                ambiente_selecionado = colf1.multiselect("Filtrar por ambiente:", ambientes_unicos)
            if 'PerfilNaTrilha' in df_ambientes.columns:
                perfis_unicos = sorted(df_ambientes['PerfilNaTrilha'].dropna().unique())
                default_perfis = [p for p in ['Obrigatório', 'Participa'] if p in perfis_unicos]
                perfil_selecionado = colf2.multiselect("Filtrar por perfil na trilha:", perfis_unicos, default=default_perfis)
            if 'NomeTrilha' in df_ambientes.columns:
                trilhas_unicas = sorted(df_ambientes['NomeTrilha'].dropna().unique())
                trilha_selecionada = colf3.multiselect("Filtrar por trilha:", trilhas_unicas)
            if 'NomeModulo' in df_ambientes.columns:
                modulos_unicos = sorted(df_ambientes['NomeModulo'].dropna().unique())
                modulo_selecionado = colf4.multiselect("Filtrar por módulo:", modulos_unicos)
            if 'TodosGruposUsuario' in df_ambientes.columns:
                grupos_unicos = sorted(df_ambientes['TodosGruposUsuario'].dropna().unique())
                grupo_selecionado = colf5.multiselect("Filtrar por grupo:", grupos_unicos)
            df_amb_filtros = df_ambientes.copy()
            if ambiente_selecionado:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeAmbiente'].isin(ambiente_selecionado)]
            if perfil_selecionado:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['PerfilNaTrilha'].isin(perfil_selecionado)]
            if trilha_selecionada:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeTrilha'].isin(trilha_selecionada)]
            if modulo_selecionado:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeModulo'].isin(modulo_selecionado)]
            if grupo_selecionado:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['TodosGruposUsuario'].isin(grupo_selecionado)]
            data_inicio_total = df_amb_filtros['DataCadastro'].min() if 'DataCadastro' in df_amb_filtros.columns else None
            data_fim_total = df_acessos['DataAcesso'].max() if 'DataAcesso' in df_acessos.columns else None
            st.markdown("### Período")
            if data_inicio_total and data_fim_total:
                periodo = st.date_input(
                    "Selecione o período:",
                    value=(data_inicio_total, data_fim_total),
                    min_value=data_inicio_total,
                    max_value=data_fim_total,
                    format="DD/MM/YYYY"
                )
            else:
                periodo = None
            if periodo and isinstance(periodo, tuple) and len(periodo) == 2:
                data_ini, data_fi = periodo
                usuarios_cadastrados = df_amb_filtros[(df_amb_filtros['DataCadastro'] >= data_ini) & (df_amb_filtros['DataCadastro'] <= data_fi)]
            else:
                usuarios_cadastrados = df_amb_filtros
            total_usuarios = usuarios_cadastrados['UsuarioID'].nunique() if 'UsuarioID' in usuarios_cadastrados.columns else 0
            if total_usuarios > 0:
                usuarios_ids = usuarios_cadastrados['UsuarioID'].unique()
                df_acessos_filtros = df_acessos[df_acessos['UsuarioID'].isin(usuarios_ids)]
                if periodo and isinstance(periodo, tuple) and len(periodo) == 2:
                    df_acessos_filtros = df_acessos_filtros[(df_acessos_filtros['DataAcesso'] >= data_ini) & (df_acessos_filtros['DataAcesso'] <= data_fi)]
                usuarios_com_acesso = df_acessos_filtros['UsuarioID'].nunique()
            else:
                usuarios_com_acesso = 0
            percentual = (usuarios_com_acesso / total_usuarios * 100) if total_usuarios > 0 else 0
            if percentual >= 70:
                classificacao = "Bom"
            elif percentual >= 40:
                classificacao = "Regular"
            else:
                classificacao = "Baixo"
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = percentual,
                number = {'suffix': '%'},
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"<b>{classificacao}</b>", 'font': {'size': 24}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                    'bar': {'color': "#00796B", 'thickness': 0.25},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 40], 'color': '#FF6F6F'},
                        {'range': [40, 70], 'color': '#FFD180'},
                        {'range': [70, 100], 'color': '#B2FFB2'}
                    ],
                }
            ))
            fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=40),
                height=400
            )
            st.markdown("#### Engajamento")
            colg1, colg2, colg3 = st.columns([1,2,1])
            with colg1:
                st.metric("Usuários", total_usuarios)
                st.metric("Usuários c/ acesso", usuarios_com_acesso)
            with colg2:
                st.plotly_chart(fig, use_container_width=True)
            with colg3:
                st.write("")
        else:
            st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")