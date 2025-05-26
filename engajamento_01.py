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
            # Filtrar apenas usuários ativos
            if 'StatusUsuario' in df_acessos.columns:
                df_acessos = df_acessos[df_acessos['StatusUsuario'].str.lower() == 'ativo']
            df_ambientes = abas['UsuariosAmbientes']
            # Filtrar df_ambientes para considerar apenas UsuarioID ativos
            if 'UsuarioID' in df_ambientes.columns and 'UsuarioID' in df_acessos.columns:
                usuarios_ativos = df_acessos['UsuarioID'].unique()
                df_ambientes = df_ambientes[df_ambientes['UsuarioID'].isin(usuarios_ativos)]
            if 'DataAcesso' in df_acessos.columns:
                df_acessos['DataAcesso'] = pd.to_datetime(df_acessos['DataAcesso'], dayfirst=True, errors='coerce').dt.date
                df_acessos['data_completa'] = pd.to_datetime(df_acessos['DataAcesso']).dt.date
            if 'DataCadastro' in df_ambientes.columns:
                df_ambientes['DataCadastro'] = pd.to_datetime(df_ambientes['DataCadastro'], format='%d/%m/%Y', errors='coerce').dt.date
                df_ambientes['data_completa'] = pd.to_datetime(df_ambientes['DataCadastro']).dt.date
            # Filtro de status do usuário
            if filtros.get('status_usuario') and 'StatusUsuario' in df_acessos.columns:
                df_acessos = df_acessos[df_acessos['StatusUsuario'].isin(filtros['status_usuario'])]
                if 'UsuarioID' in df_ambientes.columns:
                    usuarios_filtrados = df_acessos['UsuarioID'].unique()
                    df_ambientes = df_ambientes[df_ambientes['UsuarioID'].isin(usuarios_filtrados)]
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
                df_amb_filtros['DataCadastro'] = pd.to_datetime(df_amb_filtros['DataCadastro'], format='%d/%m/%Y', errors='coerce')
                usuarios_cadastrados = df_amb_filtros[df_amb_filtros['DataCadastro'].dt.date <= data_fi]
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
                height=300
            )
            # st.markdown("#### Engajamento")  # Removido para padronização
            colg1, colg2 = st.columns([1,1])
            with colg1:
                cols = list(usuarios_cadastrados.columns)
                if 'PerfilNaTrilha' in usuarios_cadastrados.columns and 'PerfilNaTrilha' not in cols:
                    cols.append('PerfilNaTrilha')
                st.metric("Usuários Cadastrados (Ativos)", total_usuarios)
            with colg2:
                # Garantir que PerfilNaTrilha está presente em df_acessos_filtros
                if 'PerfilNaTrilha' not in df_acessos_filtros.columns and 'UsuarioID' in df_acessos_filtros.columns and 'UsuarioID' in df_ambientes.columns:
                    df_acessos_filtros = df_acessos_filtros.merge(
                        df_ambientes[['UsuarioID', 'PerfilNaTrilha']].drop_duplicates(),
                        on='UsuarioID',
                        how='left'
                    )
                cols = list(df_acessos_filtros.columns)
                if 'PerfilNaTrilha' in df_acessos_filtros.columns and 'PerfilNaTrilha' not in cols:
                    cols.append('PerfilNaTrilha')
                st.metric("Usuários c/ acesso", usuarios_com_acesso)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == "__main__":
    st.info("Este arquivo deve ser importado e chamado via dashboard.py para funcionar corretamente.")