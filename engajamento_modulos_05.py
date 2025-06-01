import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def app(arquivo, filtros):
    st.title("Finalização dos Módulos")
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
                if filtros.get('incluir_sem_data'):
                    com_data = df_filtros[df_filtros['DataInicioModulo'].notna() | df_filtros['DataConclusaoModulo'].notna()]
                    sem_data = df_filtros[df_filtros['DataInicioModulo'].isna() & df_filtros['DataConclusaoModulo'].isna()]
                    mask_inicio = (com_data['DataInicioModulo'].notna()) & (com_data['DataInicioModulo'] >= data_inicio_filtro) & (com_data['DataInicioModulo'] <= data_fim_filtro)
                    mask_conclusao = (com_data['DataConclusaoModulo'].notna()) & (com_data['DataConclusaoModulo'] >= data_inicio_filtro) & (com_data['DataConclusaoModulo'] <= data_fim_filtro)
                    com_data_filtrado = com_data[mask_inicio | mask_conclusao]
                    df_filtros = pd.concat([com_data_filtrado, sem_data], ignore_index=True)
                else:
                    mask_inicio = (df_filtros['DataInicioModulo'].notna()) & (df_filtros['DataInicioModulo'] >= data_inicio_filtro) & (df_filtros['DataInicioModulo'] <= data_fim_filtro)
                    mask_conclusao = (df_filtros['DataConclusaoModulo'].notna()) & (df_filtros['DataConclusaoModulo'] >= data_inicio_filtro) & (df_filtros['DataConclusaoModulo'] <= data_fim_filtro)
                    df_filtros = df_filtros[mask_inicio | mask_conclusao]
            # Considerar apenas módulos disponíveis para os usuários filtrados
            modulos_disponiveis = df_filtros[['UsuarioID', 'NomeModulo', 'StatusModulo']].drop_duplicates()
            # Definir status de finalizado, expirado e pendente
            status_finalizado = ['Aprovado', 'Finalizado', 'Reprovado']
            status_expirado = ['Expirado (Não Realizado)']
            modulos_disponiveis['Finalizado'] = modulos_disponiveis['StatusModulo'].isin(status_finalizado)
            modulos_disponiveis['Expirado'] = modulos_disponiveis['StatusModulo'].isin(status_expirado)
            total_modulos = modulos_disponiveis.shape[0]
            total_finalizados = modulos_disponiveis['Finalizado'].sum()
            total_expirados = modulos_disponiveis['Expirado'].sum()
            total_pendentes = total_modulos - total_finalizados - total_expirados
            perc_finalizados = (total_finalizados / total_modulos * 100) if total_modulos > 0 else 0
            perc_expirados = (total_expirados / total_modulos * 100) if total_modulos > 0 else 0
            perc_pendentes = 100 - perc_finalizados - perc_expirados if total_modulos > 0 else 0
            perc_finalizados_str = f"{perc_finalizados:.0f}%" if perc_finalizados == int(perc_finalizados) else f"{perc_finalizados:.1f}%"
            perc_pendentes_str = f"{perc_pendentes:.0f}%" if perc_pendentes == int(perc_pendentes) else f"{perc_pendentes:.1f}%"
            perc_expirados_str = f"{perc_expirados:.0f}%" if perc_expirados == int(perc_expirados) else f"{perc_expirados:.1f}%"
            # Indicadores dinâmicos para os status presentes + Participações, todos em cima
            colunas = st.columns(3)
            with colunas[0]:
                st.markdown(f"""
                <div style='text-align:center;'>
                    <span style='font-size:2.2em; font-weight:bold'>{total_finalizados}</span><br>
                    <span style='font-size:1.1em; color:#888;'>{perc_finalizados_str}</span><br>
                    <span style='font-size:1.1em'>Finalizados</span>
                </div>
                """, unsafe_allow_html=True)
            with colunas[1]:
                st.markdown(f"""
                <div style='text-align:center;'>
                    <span style='font-size:2.2em; font-weight:bold'>{total_pendentes}</span><br>
                    <span style='font-size:1.1em; color:#888;'>{perc_pendentes_str}</span><br>
                    <span style='font-size:1.1em'>Pendentes</span>
                </div>
                """, unsafe_allow_html=True)
            with colunas[2]:
                st.markdown(f"""
                <div style='text-align:center;'>
                    <span style='font-size:2.2em; font-weight:bold'>{total_expirados}</span><br>
                    <span style='font-size:1.1em; color:#888;'>{perc_expirados_str}</span><br>
                    <span style='font-size:1.1em'>Expirados</span>
                </div>
                """, unsafe_allow_html=True)
            # Botão de detalhar logo abaixo dos indicadores
            with st.expander('Ver'):
                cols = list(modulos_disponiveis.columns)
                if 'PerfilNaTrilha' in df_filtros.columns and 'PerfilNaTrilha' not in cols:
                    cols.append('PerfilNaTrilha')
                if 'PerfilNaTrilha' not in modulos_disponiveis.columns and 'UsuarioID' in modulos_disponiveis.columns and 'UsuarioID' in df_filtros.columns:
                    modulos_disponiveis = modulos_disponiveis.merge(
                        df_filtros[['UsuarioID', 'PerfilNaTrilha']].drop_duplicates(),
                        on='UsuarioID', how='left')
                st.dataframe(modulos_disponiveis[cols])
            # Gráfico de pizza/donut com três categorias
            fig = go.Figure(data=[
                go.Pie(
                    labels=['Finalizados', 'Pendentes', 'Expirados'],
                    values=[total_finalizados, total_pendentes, total_expirados],
                    hole=0.5,
                    marker=dict(colors=['#4285F4', '#90CAF9', '#16a085'])
                )
            ])
            fig.update_traces(textinfo='percent+label', pull=[0.05, 0, 0])
            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                width=550,
                height=350
            )
            if fig is not None and hasattr(fig, 'to_plotly_json'):
                st.plotly_chart(fig, use_container_width=False)
            else:
                st.error("Erro ao gerar o gráfico: objeto inválido.")
        else:
            st.error("Sua planilha precisa ter a aba 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == '__main__':
    app() 