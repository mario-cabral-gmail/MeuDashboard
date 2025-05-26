import streamlit as st
import pandas as pd
import altair as alt
import locale
import plotly.graph_objects as go


def app(arquivo, filtros):
    st.title("Performance nos Módulos")

    # Configura o locale para datas em português do Brasil
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        pass

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
            # Filtrar conforme os filtros recebidos
            if filtros.get('ambiente'):
                df_ambientes = df_ambientes[df_ambientes['NomeAmbiente'].isin(filtros['ambiente'])]
            if filtros.get('perfil'):
                df_ambientes = df_ambientes[df_ambientes['PerfilNaTrilha'].isin(filtros['perfil'])]
            if filtros.get('trilha'):
                df_ambientes = df_ambientes[df_ambientes['NomeTrilha'].isin(filtros['trilha'])]
            if filtros.get('modulo'):
                df_ambientes = df_ambientes[df_ambientes['NomeModulo'].isin(filtros['modulo'])]
            if filtros.get('grupo'):
                df_ambientes = df_ambientes[df_ambientes['TodosGruposUsuario'].isin(filtros['grupo'])]
            # Filtro de status do usuário
            if filtros.get('status_usuario') and 'Acessos' in abas and 'StatusUsuario' in abas['Acessos'].columns:
                df_acessos = abas['Acessos']
                usuarios_filtrados = df_acessos[df_acessos['StatusUsuario'].isin(filtros['status_usuario'])]['UsuarioID'].unique()
                df_ambientes = df_ambientes[df_ambientes['UsuarioID'].isin(usuarios_filtrados)]
            # Considerar como participação quem tem pelo menos uma das datas (DataInicioModulo ou DataConclusaoModulo) preenchida
            if filtros.get('incluir_sem_data'):
                # Todos os pares únicos
                part = df_ambientes.drop_duplicates(subset=['UsuarioID', 'NomeModulo'])
                # Preencher StatusModulo como 'Expirado (Não Realizado)' onde ambas as datas são vazias
                mask_sem_data = part['DataInicioModulo'].isna() & part['DataConclusaoModulo'].isna()
                part.loc[mask_sem_data, 'StatusModulo'] = part.loc[mask_sem_data, 'StatusModulo'].fillna('Expirado (Não Realizado)')
            else:
                part = df_ambientes.dropna(subset=['DataInicioModulo', 'DataConclusaoModulo'], how='all').drop_duplicates(subset=['UsuarioID', 'NomeModulo'])
            # Conversão explícita das datas com formato correto
            part['DataParticipacao'] = pd.to_datetime(part['DataConclusaoModulo'].combine_first(part['DataInicioModulo']))
            part['DataParticipacao'] = part['DataParticipacao'].dt.date if part['DataParticipacao'].notna().any() else part['DataParticipacao']
            # Garantir que DataParticipacao está como date antes de qualquer filtro de período
            if 'DataParticipacao' in part.columns:
                part['DataParticipacao'] = pd.to_datetime(part['DataParticipacao'], errors='coerce').dt.date
            # Filtro de período
            if filtros.get('periodo') and (isinstance(filtros['periodo'], list) or isinstance(filtros['periodo'], tuple)) and len(filtros['periodo']) == 2:
                data_inicio_filtro = pd.to_datetime(filtros['periodo'][0], format='%d/%m/%Y')
                data_fim_filtro = pd.to_datetime(filtros['periodo'][1], format='%d/%m/%Y')
                if filtros.get('incluir_sem_data'):
                    # Separa registros com e sem data
                    com_data = part[part['DataParticipacao'].notna()]
                    sem_data = part[part['DataParticipacao'].isna()]
                    mask_inicio = (com_data['DataInicioModulo'].notna()) & (com_data['DataInicioModulo'] >= data_inicio_filtro) & (com_data['DataInicioModulo'] <= data_fim_filtro)
                    mask_conclusao = (com_data['DataConclusaoModulo'].notna()) & (com_data['DataConclusaoModulo'] >= data_inicio_filtro) & (com_data['DataConclusaoModulo'] <= data_fim_filtro)
                    com_data_filtrado = com_data[mask_inicio | mask_conclusao]
                    part = pd.concat([com_data_filtrado, sem_data], ignore_index=True)
                else:
                    mask_inicio = (part['DataInicioModulo'].notna()) & (part['DataInicioModulo'] >= data_inicio_filtro) & (part['DataInicioModulo'] <= data_fim_filtro)
                    mask_conclusao = (part['DataConclusaoModulo'].notna()) & (part['DataConclusaoModulo'] >= data_inicio_filtro) & (part['DataConclusaoModulo'] <= data_fim_filtro)
                    part = part[mask_inicio | mask_conclusao]
            total_participacoes_reais = part.shape[0]
            # Identificar todos os pares UsuarioID+NomeModulo esperados após filtros
            todos_pares = df_ambientes.drop_duplicates(subset=['UsuarioID', 'NomeModulo'])[['UsuarioID', 'NomeModulo']]
            # Encontrar pares sem participação (sem datas preenchidas)
            sem_part = df_ambientes[df_ambientes['DataInicioModulo'].isna() & df_ambientes['DataConclusaoModulo'].isna()].drop_duplicates(subset=['UsuarioID', 'NomeModulo'])
            # Se houver período, considerar apenas pares cujo módulo deveria ter sido realizado até data_fim_filtro
            if data_fim_filtro is not None:
                expirados = sem_part.copy()
                expirados['DataParticipacao'] = data_fim_filtro
                expirados['StatusModulo'] = 'Expirado (Não Realizado)'
                # Dataframe para o gráfico: participações reais + expirados
                part_graf = pd.concat([part, expirados[['UsuarioID', 'NomeModulo', 'StatusModulo', 'DataParticipacao']]], ignore_index=True)
            else:
                part_graf = part.copy()
            # Antes de filtrar part_graf pelo período, garantir que DataParticipacao está como date
            if 'DataParticipacao' in part_graf.columns:
                part_graf['DataParticipacao'] = pd.to_datetime(part_graf['DataParticipacao'], errors='coerce').dt.date
            # Filtro de período
            if filtros.get('periodo') and (isinstance(filtros['periodo'], list) or isinstance(filtros['periodo'], tuple)) and len(filtros['periodo']) == 2:
                data_inicio_filtro = pd.to_datetime(filtros['periodo'][0], format='%d/%m/%Y')
                data_fim_filtro = pd.to_datetime(filtros['periodo'][1], format='%d/%m/%Y')
                # Antes do filtro de período em part_graf, garantir tipos corretos
                if 'DataParticipacao' in part_graf.columns:
                    part_graf['DataParticipacao'] = pd.to_datetime(part_graf['DataParticipacao'], errors='coerce')
                if 'data_inicio' in locals() and hasattr(data_inicio, 'date'):
                    data_inicio = data_inicio.date()
                if 'data_fim' in locals() and hasattr(data_fim, 'date'):
                    data_fim = data_fim.date()
                part_graf = part_graf[(
                    (pd.to_datetime(part_graf['DataInicioModulo'], errors='coerce') >= data_inicio_filtro) | (pd.to_datetime(part_graf['DataConclusaoModulo'], errors='coerce') >= data_inicio_filtro)
                ) & (
                    (pd.to_datetime(part_graf['DataInicioModulo'], errors='coerce') <= data_fim_filtro) | (pd.to_datetime(part_graf['DataConclusaoModulo'], errors='coerce') <= data_fim_filtro)
                )]
            # Gerar datas contínuas do período filtrado (igual ao gráfico 2)
            if filtros.get('periodo') and (isinstance(filtros['periodo'], list) or isinstance(filtros['periodo'], tuple)) and len(filtros['periodo']) == 2:
                data_inicio = pd.to_datetime(filtros['periodo'][0], format='%d/%m/%Y')
                data_fim = pd.to_datetime(filtros['periodo'][1], format='%d/%m/%Y')
            elif not part_graf.empty:
                data_inicio = part_graf['DataParticipacao'].min()
                data_fim = part_graf['DataParticipacao'].max()
            else:
                data_inicio = data_fim = pd.to_datetime('today')
            # Filtrar part_graf pelo período antes de agrupar
            part_graf = part_graf[(part_graf['DataParticipacao'] >= data_inicio) & (part_graf['DataParticipacao'] <= data_fim)]
            # Criar o dataframe do gráfico a partir do 'part' corrigido
            df_graf = part.groupby(['DataParticipacao', 'StatusModulo']).size().reset_index(name='Quantidade')
            datas_eixo = pd.DataFrame({'DataParticipacao': pd.date_range(start=data_inicio, end=data_fim, freq='D')})
            status_dom = ['Aprovado', 'Em Andamento', 'Reprovado', 'Expirado (Não Realizado)']
            status_cores = ['#2ecc71', '#e67e22', '#e74c3c', '#16a085']
            idx = pd.MultiIndex.from_product([datas_eixo['DataParticipacao'], status_dom], names=['DataParticipacao', 'StatusModulo'])
            df_graf = df_graf.set_index(['DataParticipacao', 'StatusModulo']).reindex(idx, fill_value=0).reset_index()
            df_graf['DataLabel'] = pd.to_datetime(df_graf['DataParticipacao']).dt.strftime('%d/%m/%Y')
            df_graf['DataX'] = pd.to_datetime(df_graf['DataParticipacao'])
            # Indicadores
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric('Particip.', part.shape[0])
            with col1.expander('Ver'):
                st.dataframe(part[['UsuarioID', 'NomeModulo', 'StatusModulo', 'DataInicioModulo', 'DataConclusaoModulo']])
            col2.metric('Aprov.', part[part['StatusModulo'] == 'Aprovado'].shape[0])
            with col2.expander('Ver'):
                st.dataframe(part[part['StatusModulo'] == 'Aprovado'][['UsuarioID', 'NomeModulo', 'StatusModulo']])
            col3.metric('Andam.', part[part['StatusModulo'] == 'Em Andamento'].shape[0])
            with col3.expander('Ver'):
                st.dataframe(part[part['StatusModulo'] == 'Em Andamento'][['UsuarioID', 'NomeModulo', 'StatusModulo']])
            col4.metric('Reprov.', part[part['StatusModulo'] == 'Reprovado'].shape[0])
            with col4.expander('Ver'):
                st.dataframe(part[part['StatusModulo'] == 'Reprovado'][['UsuarioID', 'NomeModulo', 'StatusModulo']])
            col5.metric('Expir.', part[part['StatusModulo'] == 'Expirado (Não Realizado)'].shape[0])
            with col5.expander('Ver'):
                st.dataframe(part[part['StatusModulo'] == 'Expirado (Não Realizado)'][['UsuarioID', 'NomeModulo', 'StatusModulo', 'DataInicioModulo', 'DataConclusaoModulo']])
            # --- NOVO GRÁFICO: Pizza de distribuição dos status ---
            status_labels = ['Aprovado', 'Em Andamento', 'Reprovado', 'Expirado (Não Realizado)']
            status_cores = ['#2ecc71', '#e67e22', '#e74c3c', '#16a085']
            status_counts = [
                part[part['StatusModulo'] == 'Aprovado'].shape[0],
                part[part['StatusModulo'] == 'Em Andamento'].shape[0],
                part[part['StatusModulo'] == 'Reprovado'].shape[0],
                part[part['StatusModulo'] == 'Expirado (Não Realizado)'].shape[0]
            ]
            fig = go.Figure(data=[
                go.Pie(
                    labels=status_labels,
                    values=status_counts,
                    marker=dict(colors=status_cores),
                    hole=0.5
                )
            ])
            fig.update_traces(textinfo='percent+label', pull=[0.05, 0, 0, 0])
            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                width=550,
                height=350
            )
            st.plotly_chart(fig, use_container_width=False)
        else:
            st.error("Sua planilha precisa ter a aba 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == "__main__":
    st.info("Este arquivo deve ser importado e chamado via dashboard.py para funcionar corretamente.") 