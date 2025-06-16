import streamlit as st
import pandas as pd
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
      font-size: 14px !important;
      font-weight: 400 !important;
      line-height: 1.4;
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
        Ambientes com mais participações
        <span class="tooltip">
            <b style="color:#888; font-size:1.1em; cursor:help;">&#9432;</b>
            <span class="tooltiptext">
                Mostra os 3 ambientes com maior número de participações e aprovações.<br>
                🕒 Somente participações com início ou conclusão do módulo dentro do período são consideradas.
            </span>
        </span>
    </h3>
    ''', unsafe_allow_html=True)
    if arquivo:
        # Suportar tanto arquivo Excel quanto dicionário com DataFrames
        if isinstance(arquivo, dict):
            abas = arquivo
        else:
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
            # Aplicar filtros
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
            # Filtro de período (igual ao gráfico 3)
            periodo = filtros.get('periodo')
            if periodo and isinstance(periodo, tuple) and len(periodo) == 2:
                data_ini, data_fi = pd.to_datetime(periodo[0], format='%d/%m/%Y'), pd.to_datetime(periodo[1], format='%d/%m/%Y')
                df_ambientes['DataInicioModulo'] = pd.to_datetime(df_ambientes['DataInicioModulo'], dayfirst=True, errors='coerce')
                df_ambientes['DataConclusaoModulo'] = pd.to_datetime(df_ambientes['DataConclusaoModulo'], dayfirst=True, errors='coerce')
                if filtros.get('incluir_sem_data'):
                    com_data = df_ambientes[df_ambientes['DataInicioModulo'].notna() | df_ambientes['DataConclusaoModulo'].notna()]
                    sem_data = df_ambientes[df_ambientes['DataInicioModulo'].isna() & df_ambientes['DataConclusaoModulo'].isna()]
                    mask_inicio = (com_data['DataInicioModulo'].notna()) & (com_data['DataInicioModulo'] >= data_ini) & (com_data['DataInicioModulo'] <= data_fi)
                    mask_conclusao = (com_data['DataConclusaoModulo'].notna()) & (com_data['DataConclusaoModulo'] >= data_ini) & (com_data['DataConclusaoModulo'] <= data_fi)
                    com_data_filtrado = com_data[mask_inicio | mask_conclusao]
                    df_ambientes = pd.concat([com_data_filtrado, sem_data], ignore_index=True)
                else:
                    mask_inicio = (df_ambientes['DataInicioModulo'] >= data_ini) & (df_ambientes['DataInicioModulo'] <= data_fi)
                    mask_conclusao = (df_ambientes['DataConclusaoModulo'] >= data_ini) & (df_ambientes['DataConclusaoModulo'] <= data_fi)
                    mask = mask_inicio | mask_conclusao
                    df_ambientes = df_ambientes[mask]
            # Considerar como participação quem tem DataInicioModulo ou DataConclusaoModulo preenchida
            if filtros.get('incluir_sem_data'):
                part = df_ambientes.drop_duplicates(subset=['UsuarioID', 'NomeAmbiente', 'NomeModulo'])
            else:
                part = df_ambientes.dropna(subset=['DataInicioModulo', 'DataConclusaoModulo'], how='all').drop_duplicates(subset=['UsuarioID', 'NomeAmbiente', 'NomeModulo'])
            part['DataInicioModulo'] = pd.to_datetime(part['DataInicioModulo'], dayfirst=True, errors='coerce')
            part['DataConclusaoModulo'] = pd.to_datetime(part['DataConclusaoModulo'], dayfirst=True, errors='coerce')
            participacoes = part.groupby('NomeAmbiente').size()
            aprov = part[part['StatusModulo'] == 'Aprovado']
            aprovacoes = aprov.groupby('NomeAmbiente').size()
            # Unir em DataFrame
            df_plot = pd.DataFrame({
                'Participações': participacoes,
                'Aprovações': aprovacoes
            }).fillna(0).astype(int)
            df_plot = df_plot.sort_values('Participações', ascending=False).head(3)
            df_plot = df_plot.iloc[::-1]  # Inverter para o maior no topo
            if df_plot.empty:
                st.info("Nenhum dado encontrado após aplicação dos filtros.")
                return
            ambientes = df_plot.index.tolist()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=ambientes,
                x=df_plot['Participações'],
                name='Participações',
                orientation='h',
                marker_color='#4285F4',
                text=df_plot['Participações'],
                textposition='auto'
            ))
            fig.add_trace(go.Bar(
                y=ambientes,
                x=df_plot['Aprovações'],
                name='Aprovações',
                orientation='h',
                marker_color='#90EE90',
                text=df_plot['Aprovações'],
                textposition='auto'
            ))
            fig.update_layout(
                barmode='group',
                xaxis_title=None,
                yaxis_title=None,
                height=350 + 25*len(ambientes),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            if fig is not None and hasattr(fig, 'to_plotly_json'):
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Erro ao gerar o gráfico: objeto inválido.")
            with st.expander("Ver dados brutos"):
                st.dataframe(df_plot)
        else:
            st.error("Sua planilha precisa ter a aba 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.") 