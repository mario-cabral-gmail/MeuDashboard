import streamlit as st
import pandas as pd
import altair as alt
import locale
import plotly.graph_objects as go

def app(arquivo, filtros):
    st.title("Engajamento")
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        pass
    if arquivo:
        abas = pd.read_excel(arquivo, sheet_name=None)
        if 'Acessos' in abas and 'UsuariosAmbientes' in abas:
            df_acessos = abas['Acessos']
            df_ambientes = abas['UsuariosAmbientes']
            if 'DataAcesso' in df_acessos.columns:
                df_acessos['DataAcesso'] = pd.to_datetime(df_acessos['DataAcesso'], dayfirst=True, errors='coerce').dt.date
            if 'DataCadastro' in df_ambientes.columns:
                df_ambientes['DataCadastro'] = pd.to_datetime(df_ambientes['DataCadastro'], dayfirst=True, errors='coerce').dt.date
            # Aplicar filtros recebidos
            df_amb_filtros = df_ambientes.copy()
            if filtros.get('ambiente'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeAmbiente'].isin(filtros['ambiente'])]
            if filtros.get('perfil'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['PerfilNaTrilha'].isin(filtros['perfil'])]
            if filtros.get('trilha'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeTrilha'].isin(filtros['trilha'])]
            if filtros.get('modulo'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeModulo'].isin(filtros['modulo'])]
            if filtros.get('grupo'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['TodosGruposUsuario'].isin(filtros['grupo'])]
            data_inicio_total = df_amb_filtros['DataCadastro'].min() if 'DataCadastro' in df_amb_filtros.columns else None
            data_fim_total = df_acessos['DataAcesso'].max() if 'DataAcesso' in df_acessos.columns else None
            # Usar o período recebido nos filtros
            periodo = filtros.get('periodo')
            if periodo and isinstance(periodo, tuple) and len(periodo) == 2:
                data_ini, data_fi = periodo
                data_ini = pd.to_datetime(data_ini).date()
                data_fi = pd.to_datetime(data_fi).date()
                df_amb_filtros['DataCadastro'] = pd.to_datetime(df_amb_filtros['DataCadastro']).dt.date
                usuarios_cadastrados = df_amb_filtros[df_amb_filtros['DataCadastro'] <= data_fi]
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
                with st.expander("Ver detalhes usuários"):
                    st.dataframe(usuarios_cadastrados)
                st.metric("Usuários c/ acesso", usuarios_com_acesso)
                with st.expander("Ver detalhes usuários c/ acesso"):
                    st.dataframe(df_acessos_filtros)
            with colg2:
                st.plotly_chart(fig, use_container_width=True)
            with colg3:
                st.write("")
        else:
            st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == "__main__":
    st.info("Este arquivo deve ser importado e chamado via dashboard.py para funcionar corretamente.")