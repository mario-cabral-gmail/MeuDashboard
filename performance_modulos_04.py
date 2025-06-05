import streamlit as st
import pandas as pd
import altair as alt
import locale
import plotly.graph_objects as go


def app(arquivo, filtros):
    st.markdown('''
    <style>
    .tooltip {
      position: relative;
      display: inline-block;
    }
    .tooltip .tooltiptext {
      visibility: hidden;
      min-width: 220px;
      max-width: 320px;
      background: #fff;
      color: #222;
      text-align: left;
      border-radius: 8px;
      padding: 10px 14px;
      position: absolute;
      z-index: 10;
      bottom: 130%;
      left: 50%;
      margin-left: -110px;
      opacity: 0;
      box-shadow: 0 2px 12px rgba(60,60,60,0.10), 0 1.5px 4px rgba(60,60,60,0.08);
      border: 1px solid #eee;
      font-size: 14px;
      transition: opacity 0.1s;
      pointer-events: none;
    }
    .tooltip:hover .tooltiptext {
      visibility: visible;
      opacity: 1;
      pointer-events: auto;
    }
    </style>
    <h3 style="display:inline;">
        Desempenho nos Módulos
        <span class="tooltip">
            <b style="color:#888; font-size:1.1em; cursor:help;">&#9432;</b>
            <span class="tooltiptext">
                Mostra a quantidade de participações e o status (aprovado, reprovado, em andamento, expirado etc.).<br>
                🕒 O filtro de período considera registros com início ou conclusão do módulo dentro do intervalo selecionado.
            </span>
        </span>
    </h3>
    ''', unsafe_allow_html=True)

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
            # Ajustar status para nova categoria 'Módulos Expirados'
            part['StatusAjustado'] = part['StatusModulo']
            part.loc[part['StatusModulo'] == 'Expirado (Não Realizado)', 'StatusAjustado'] = 'Módulos Expirados'
            # Criar o dataframe do gráfico a partir do 'part' corrigido
            df_graf = part.groupby(['DataParticipacao', 'StatusAjustado']).size().reset_index(name='Quantidade')
            datas_eixo = pd.DataFrame({'DataParticipacao': pd.date_range(start=data_inicio, end=data_fim, freq='D')})
            status_dom = ['Aprovado', 'Em Andamento', 'Reprovado', 'Módulos Expirados']
            status_cores = ['#2ecc71', '#e67e22', '#e74c3c', '#16a085']
            idx = pd.MultiIndex.from_product([datas_eixo['DataParticipacao'], status_dom], names=['DataParticipacao', 'StatusAjustado'])
            df_graf = df_graf.set_index(['DataParticipacao', 'StatusAjustado']).reindex(idx, fill_value=0).reset_index()
            df_graf['DataLabel'] = pd.to_datetime(df_graf['DataParticipacao']).dt.strftime('%d/%m/%Y')
            df_graf['DataX'] = pd.to_datetime(df_graf['DataParticipacao'])
            # Indicadores dinâmicos para os status presentes
            status_nomes = {
                'Aprovado': 'Aprovado',
                'Em Andamento': 'Andam.',
                'Reprovado': 'Reprovado',
                'Módulos Expirados': 'Expirado',
                'Expirado (Não Realizado)': 'Expirado',
                'Aprovado Fora do Prazo': 'Aprov. Fora Prazo',
                'Reprovado Fora do Prazo': 'Reprov. Fora Prazo',
                'Aguardando Correção': 'Aguard. Correção',
                'Não Iniciado': 'Não Iniciado',
                'Não Liberado': 'Não Liberado',
                'Dispensado': 'Dispensado'
            }
            # Gerar labels, valores e cores apenas para os status presentes
            status_presentes = part['StatusAjustado'].value_counts().index.tolist()
            status_labels = status_presentes
            # Indicadores dinâmicos para os status presentes + Participações, todos em cima
            total = part.shape[0]
            colunas = st.columns(len(status_labels) + 1)
            with colunas[0]:
                st.markdown(f"""
                <div style='text-align:center;'>
                    <span style='font-size:2.2em; font-weight:bold'>{total}</span><br>
                    <span style='font-size:1.1em; color:#888;'>Participações</span>
                </div>
                """, unsafe_allow_html=True)
                with st.expander('Ver'):
                    st.dataframe(part[['UsuarioID', 'NomeModulo', 'StatusAjustado', 'DataInicioModulo', 'DataConclusaoModulo']])
            for i, status in enumerate(status_labels):
                nome = status_nomes.get(status, status)
                valor = part[part['StatusAjustado'] == status].shape[0]
                perc = (valor / total * 100) if total > 0 else 0
                perc_str = f"{perc:.0f}%" if perc == int(perc) else f"{perc:.1f}%"
                with colunas[i+1]:
                    st.markdown(f"""
                    <div style='text-align:center;'>
                        <span style='font-size:2.2em; font-weight:bold'>{valor}</span><br>
                        <span style='font-size:1.1em; color:#888;'>{perc_str}</span><br>
                        <span style='font-size:1.1em'>{nome}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander('Ver'):
                        st.dataframe(part[part['StatusAjustado'] == status][['UsuarioID', 'NomeModulo', 'StatusAjustado', 'DataInicioModulo', 'DataConclusaoModulo']])
            # --- NOVO GRÁFICO: Pizza de distribuição dos status ---
            # Definir todas as cores possíveis para os status
            cores_status = {
                'Aprovado': '#2ecc71',
                'Reprovado': '#e74c3c',
                'Aprovado Fora do Prazo': '#3498db',
                'Reprovado Fora do Prazo': '#9b59b6',
                'Expirado (Não Realizado)': '#16a085',
                'Aguardando Correção': '#f1c40f',
                'Em Andamento': '#e67e22',
                'Não Iniciado': '#95a5a6',
                'Não Liberado': '#bdbdbd',
                'Dispensado': '#607d8b',
                'Módulos Expirados': '#16a085'  # Para compatibilidade com ajuste anterior
            }
            status_nomes = {
                'Aprovado': 'Aprov.',
                'Reprovado': 'Reprov.',
                'Aprovado Fora do Prazo': 'Aprov. Fora Prazo',
                'Reprovado Fora do Prazo': 'Reprov. Fora Prazo',
                'Expirado (Não Realizado)': 'Expirado',
                'Aguardando Correção': 'Aguard. Correção',
                'Em Andamento': 'Andam.',
                'Não Iniciado': 'Não Iniciado',
                'Não Liberado': 'Não Liberado',
                'Dispensado': 'Dispensado',
                'Módulos Expirados': 'Expir.'
            }
            # Gerar labels, valores e cores apenas para os status presentes
            status_presentes = part['StatusAjustado'].value_counts().index.tolist()
            status_labels = status_presentes
            status_counts = [part[part['StatusAjustado'] == s].shape[0] for s in status_labels]
            status_cores = [cores_status.get(s, '#888888') for s in status_labels]
            fig = go.Figure(data=[
                go.Pie(
                    labels=status_labels,
                    values=status_counts,
                    marker=dict(colors=status_cores),
                    hole=0.5
                )
            ])
            fig.update_traces(textinfo='percent+label', pull=[0.05] + [0]*(len(status_labels)-1))
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

if __name__ == "__main__":
    st.info("Este arquivo deve ser importado e chamado via dashboard.py para funcionar corretamente.") 