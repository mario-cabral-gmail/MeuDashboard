import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def app(arquivo, filtros):
    st.title("Engajamento de Módulos")
    if arquivo:
        abas = pd.read_excel(arquivo, sheet_name=None)
        if 'UsuariosAmbientes' in abas:
            df_ambientes = abas['UsuariosAmbientes']
            # Filtrar apenas usuários ativos se possível
            if 'Acessos' in abas and 'StatusUsuario' in abas['Acessos'].columns:
                df_acessos = abas['Acessos']
                df_acessos = df_acessos[df_acessos['StatusUsuario'].str.lower() == 'ativo']
                if 'UsuarioID' in df_ambientes.columns and 'UsuarioID' in df_acessos.columns:
                    usuarios_ativos = df_acessos['UsuarioID'].unique()
                    df_ambientes = df_ambientes[df_ambientes['UsuarioID'].isin(usuarios_ativos)]
            # Filtro de status do usuário
            if filtros.get('status_usuario') and 'Acessos' in abas and 'StatusUsuario' in abas['Acessos'].columns:
                df_acessos = abas['Acessos']
                usuarios_filtrados = df_acessos[df_acessos['StatusUsuario'].isin(filtros['status_usuario'])]['UsuarioID'].unique()
                df_ambientes = df_ambientes[df_ambientes['UsuarioID'].isin(usuarios_filtrados)]
            # Aplicar filtros recebidos
            df_filtros = df_ambientes.copy()
            if filtros.get('ambiente'):
                df_filtros = df_filtros[df_filtros['NomeAmbiente'].isin(filtros['ambiente'])]
            if filtros.get('perfil'):
                df_filtros = df_filtros[df_filtros['PerfilNaTrilha'].isin(filtros['perfil'])]
            if filtros.get('trilha'):
                df_filtros = df_filtros[df_filtros['NomeTrilha'].isin(filtros['trilha'])]
            if filtros.get('modulo'):
                df_filtros = df_filtros[df_filtros['NomeModulo'].isin(filtros['modulo'])]
            if filtros.get('grupo'):
                df_filtros = df_filtros[df_filtros['TodosGruposUsuario'].isin(filtros['grupo'])]
            # Conversão das datas dos módulos (SEM hora)
            df_filtros['DataInicioModulo'] = pd.to_datetime(df_filtros['DataInicioModulo'], format='%d/%m/%Y', errors='coerce')
            df_filtros['DataConclusaoModulo'] = pd.to_datetime(df_filtros['DataConclusaoModulo'], format='%d/%m/%Y', errors='coerce')
            # Filtro de período
            if filtros.get('periodo') and (isinstance(filtros['periodo'], list) or isinstance(filtros['periodo'], tuple)) and len(filtros['periodo']) == 2:
                data_inicio_filtro = pd.to_datetime(filtros['periodo'][0], format='%d/%m/%Y')
                data_fim_filtro = pd.to_datetime(filtros['periodo'][1], format='%d/%m/%Y')
                mask_inicio = (df_filtros['DataInicioModulo'].notna()) & (df_filtros['DataInicioModulo'] >= data_inicio_filtro) & (df_filtros['DataInicioModulo'] <= data_fim_filtro)
                mask_conclusao = (df_filtros['DataConclusaoModulo'].notna()) & (df_filtros['DataConclusaoModulo'] >= data_inicio_filtro) & (df_filtros['DataConclusaoModulo'] <= data_fim_filtro)
                df_filtros = df_filtros[mask_inicio | mask_conclusao]
            # Considerar apenas módulos disponíveis para os usuários filtrados
            modulos_disponiveis = df_filtros[['UsuarioID', 'NomeModulo', 'StatusModulo']].drop_duplicates()
            # Definir status de finalizado e pendente
            status_finalizado = ['Aprovado', 'Finalizado', 'Expirado (Não Realizado)', 'Reprovado']
            modulos_disponiveis['Finalizado'] = modulos_disponiveis['StatusModulo'].isin(status_finalizado)
            total_modulos = modulos_disponiveis.shape[0]
            total_finalizados = modulos_disponiveis['Finalizado'].sum()
            total_pendentes = total_modulos - total_finalizados
            perc_finalizados = (total_finalizados / total_modulos * 100) if total_modulos > 0 else 0
            perc_pendentes = 100 - perc_finalizados if total_modulos > 0 else 0
            # Gráfico de pizza/donut
            fig = go.Figure(data=[
                go.Pie(
                    labels=['Finalizados', 'Pendentes'],
                    values=[total_finalizados, total_pendentes],
                    hole=0.5,
                    marker=dict(colors=['#4285F4', '#90CAF9'])
                )
            ])
            fig.update_traces(textinfo='percent+label', pull=[0.05, 0])
            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                width=550,
                height=350
            )
            st.plotly_chart(fig, use_container_width=False)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<b>Módulos Finalizados</b><br><span style='font-size:2em'>{perc_finalizados:.2f}%</span> ({total_finalizados})", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<b>Módulos Pendentes</b><br><span style='font-size:2em'>{perc_pendentes:.2f}%</span> ({total_pendentes})", unsafe_allow_html=True)
            with st.expander("Detalhar"):
                cols = list(modulos_disponiveis.columns)
                if 'PerfilNaTrilha' in df_filtros.columns and 'PerfilNaTrilha' not in cols:
                    cols.append('PerfilNaTrilha')
                # Merge para garantir que a coluna esteja presente
                if 'PerfilNaTrilha' not in modulos_disponiveis.columns and 'UsuarioID' in modulos_disponiveis.columns and 'UsuarioID' in df_filtros.columns:
                    modulos_disponiveis = modulos_disponiveis.merge(
                        df_filtros[['UsuarioID', 'PerfilNaTrilha']].drop_duplicates(),
                        on='UsuarioID', how='left')
                st.dataframe(modulos_disponiveis[cols])
        else:
            st.error("Sua planilha precisa ter a aba 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == '__main__':
    app() 