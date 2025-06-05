import streamlit as st
import pandas as pd
import altair as alt
import locale

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
        Acessos
        <span class="tooltip">
            <b style="color:#888; font-size:1.1em; cursor:help;">&#9432;</b>
            <span class="tooltiptext">
                Mostra o número total de acessos e a evolução ao longo do tempo.<br>
                🕒 Apenas acessos com data dentro do período selecionado entram no gráfico.
            </span>
        </span>
    </h3>
    ''', unsafe_allow_html=True)
    # st.title("📊 Dashboard de Acessos")
    # st.markdown("Visualize os acessos por dia, ambiente, perfil, trilha, módulo e grupo de forma interativa e moderna.")

    # Configura o locale para datas em português do Brasil
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

            campos_merge = [
                'UsuarioID', 'NomeAmbiente', 'PerfilNaTrilha', 'NomeTrilha',
                'NomeModulo', 'TodosGruposUsuario'
            ]
            campos_merge = [c for c in campos_merge if c in df_ambientes.columns]
            df = pd.merge(
                df_acessos,
                df_ambientes[campos_merge],
                on='UsuarioID',
                how='left'
            )

            if 'DataAcesso' in df.columns and 'UsuarioID' in df.columns:
                df['DataAcesso'] = pd.to_datetime(df['DataAcesso'], dayfirst=True, errors='coerce').dt.normalize()
                df = df.dropna(subset=['DataAcesso'])

                data_inicio_total = df['DataAcesso'].min()
                data_fim_total = df['DataAcesso'].max()

                if 'DataInicioModulo' in df_ambientes.columns:
                    df_ambientes['DataInicioModulo'] = pd.to_datetime(df_ambientes['DataInicioModulo'], format='%d/%m/%Y', errors='coerce').dt.normalize()
                if 'DataConclusaoModulo' in df_ambientes.columns:
                    df_ambientes['DataConclusaoModulo'] = pd.to_datetime(df_ambientes['DataConclusaoModulo'], format='%d/%m/%Y', errors='coerce').dt.normalize()

                # Inicializar participacoes_inicio para evitar erro de variável não definida
                participacoes_inicio = pd.DataFrame()
                # Padronizar datas para datetime64[ns] e extrair apenas a data
                df['DataAcesso'] = pd.to_datetime(df['DataAcesso'], dayfirst=True, errors='coerce').dt.normalize()
                if 'DataAcesso' in participacoes_inicio.columns:
                    participacoes_inicio['DataAcesso'] = pd.to_datetime(participacoes_inicio['DataAcesso'], dayfirst=True, errors='coerce').dt.normalize()
                    usuarios_participantes = participacoes_inicio.groupby('DataAcesso')['UsuarioID'].nunique().reset_index(name='Usuarios_participantes')
                else:
                    usuarios_participantes = pd.DataFrame(columns=['DataAcesso', 'Usuarios_participantes'])
                # Gerar datas contínuas do período filtrado
                data_inicio_eixo = df['DataAcesso'].min()
                data_fim_eixo = df['DataAcesso'].max()
                datas_eixo = pd.DataFrame({'DataAcesso': pd.date_range(start=data_inicio_eixo, end=data_fim_eixo, freq='D')})
                # Aplicar filtros ao DataFrame de participantes antes de calcular participantes por dia
                df_ambientes_filtrado = df_ambientes.copy()
                if filtros.get('ambiente') and 'NomeAmbiente' in df_ambientes_filtrado.columns:
                    df_ambientes_filtrado = df_ambientes_filtrado[df_ambientes_filtrado['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil') and 'PerfilNaTrilha' in df_ambientes_filtrado.columns:
                    df_ambientes_filtrado = df_ambientes_filtrado[df_ambientes_filtrado['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha') and 'NomeTrilha' in df_ambientes_filtrado.columns:
                    df_ambientes_filtrado = df_ambientes_filtrado[df_ambientes_filtrado['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo') and 'NomeModulo' in df_ambientes_filtrado.columns:
                    df_ambientes_filtrado = df_ambientes_filtrado[df_ambientes_filtrado['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo') and 'TodosGruposUsuario' in df_ambientes_filtrado.columns:
                    df_ambientes_filtrado = df_ambientes_filtrado[df_ambientes_filtrado['TodosGruposUsuario'].isin(filtros['grupo'])]
                # Usuários participantes: quem iniciou OU concluiu módulo no dia (após filtro)
                participantes_inicio = pd.DataFrame()
                participantes_fim = pd.DataFrame()
                if 'DataInicioModulo' in df_ambientes_filtrado.columns:
                    participantes_inicio = df_ambientes_filtrado[['UsuarioID', 'DataInicioModulo']].dropna()
                    participantes_inicio['DataParticipacao'] = pd.to_datetime(participantes_inicio['DataInicioModulo'], dayfirst=True, errors='coerce').dt.normalize()
                if 'DataConclusaoModulo' in df_ambientes_filtrado.columns:
                    participantes_fim = df_ambientes_filtrado[['UsuarioID', 'DataConclusaoModulo']].dropna()
                    participantes_fim['DataParticipacao'] = pd.to_datetime(participantes_fim['DataConclusaoModulo'], dayfirst=True, errors='coerce').dt.normalize()
                # Concatenar e deduplicar participantes por dia e usuário
                participantes = pd.concat([
                    participantes_inicio[['UsuarioID', 'DataParticipacao']],
                    participantes_fim[['UsuarioID', 'DataParticipacao']]
                ])
                participantes = participantes.drop_duplicates(subset=['UsuarioID', 'DataParticipacao'])
                usuarios_participantes = participantes.groupby('DataParticipacao')['UsuarioID'].nunique().reset_index(name='Usuarios_participantes')
                usuarios_participantes = datas_eixo.merge(usuarios_participantes, left_on='DataAcesso', right_on='DataParticipacao', how='left').fillna(0)
                usuarios_participantes['Usuarios_participantes'] = usuarios_participantes['Usuarios_participantes'].astype(int)
                usuarios_participantes['data_completa'] = usuarios_participantes['DataAcesso']

                # Aplicar filtros ao DataFrame principal antes de qualquer agrupamento
                df_filtrado = df.copy()
                if filtros.get('ambiente') and 'NomeAmbiente' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil') and 'PerfilNaTrilha' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha') and 'NomeTrilha' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo') and 'NomeModulo' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo') and 'TodosGruposUsuario' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['TodosGruposUsuario'].isin(filtros['grupo'])]
                # Agrupar acessos por data normalmente, agora usando df_filtrado
                usuarios_acesso = df_filtrado.groupby('DataAcesso')['UsuarioID'].nunique().reset_index(name='Usuarios_com_acesso')
                usuarios_acesso = datas_eixo.merge(usuarios_acesso, on='DataAcesso', how='left')
                usuarios_acesso['Usuarios_com_acesso'] = usuarios_acesso['Usuarios_com_acesso'].fillna(0).astype(int)
                usuarios_acesso['data_completa'] = usuarios_acesso['DataAcesso']

                consolidado = df.groupby('DataAcesso')['UsuarioID'].nunique().reset_index()
                consolidado = consolidado.rename(columns={'UsuarioID': 'Usuarios_com_acesso'})
                consolidado = consolidado.sort_values('DataAcesso')

                datas_continuas = pd.DataFrame({'DataAcesso': pd.date_range(start=data_inicio_total, end=data_fim_total)})
                consolidado = datas_continuas.merge(consolidado, on='DataAcesso', how='left')

                consolidado = consolidado.merge(usuarios_participantes, on='DataAcesso', how='left')
                consolidado[['Usuarios_com_acesso', 'Usuarios_participantes']] = \
                    consolidado[['Usuarios_com_acesso', 'Usuarios_participantes']].fillna(0).astype(int)

                # Usar o período recebido nos filtros
                periodo = filtros.get('periodo')
                if isinstance(periodo, tuple) and len(periodo) == 2:
                    data_ini, data_fi = periodo
                    data_ini = pd.to_datetime(data_ini)
                    data_fi = pd.to_datetime(data_fi)
                    # Garantir que ambos sejam date para comparação
                    consolidado['DataAcesso'] = pd.to_datetime(consolidado['DataAcesso'])
                    mask = (consolidado['DataAcesso'].dt.date >= data_ini.date()) & (consolidado['DataAcesso'].dt.date <= data_fi.date())
                    consolidado_filtrado = consolidado.loc[mask]
                else:
                    consolidado_filtrado = consolidado

                # Calcular total_usuarios a partir da aba UsuariosAmbientes, sem filtrar por DataCadastro
                df_usuarios = df_ambientes.copy()
                if 'DataCadastro' in df_usuarios.columns:
                    df_usuarios['DataCadastro'] = pd.to_datetime(df_usuarios['DataCadastro'], dayfirst=True, errors='coerce').dt.date
                if filtros.get('ambiente'):
                    df_usuarios = df_usuarios[df_usuarios['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil'):
                    df_usuarios = df_usuarios[df_usuarios['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha'):
                    df_usuarios = df_usuarios[df_usuarios['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo'):
                    df_usuarios = df_usuarios[df_usuarios['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo'):
                    df_usuarios = df_usuarios[df_usuarios['TodosGruposUsuario'].isin(filtros['grupo'])]
                # Removido filtro por DataCadastro <= data_fi
                total_usuarios = df_usuarios['UsuarioID'].nunique() if 'UsuarioID' in df_usuarios.columns else 0
                total_ambientes = df['NomeAmbiente'].nunique() if 'NomeAmbiente' in df.columns else 0
                total_perfis = df['PerfilNaTrilha'].nunique() if 'PerfilNaTrilha' in df.columns else 0
                participacoes_inicio_raw = df_ambientes[['UsuarioID', 'DataInicioModulo', 'NomeAmbiente', 'PerfilNaTrilha', 'NomeTrilha', 'NomeModulo', 'TodosGruposUsuario']].dropna(subset=['DataInicioModulo'])
                participacoes_inicio_raw['data_completa'] = pd.to_datetime(participacoes_inicio_raw['DataInicioModulo']).dt.date
                participacoes_inicio_raw['semana'] = pd.to_datetime(participacoes_inicio_raw['DataInicioModulo']).dt.to_period('W').apply(lambda r: r.start_time.date() if pd.notnull(r) else pd.NaT)
                participacoes_inicio_raw['mes'] = pd.to_datetime(participacoes_inicio_raw['DataInicioModulo']).dt.to_period('M').apply(lambda r: r.start_time.date() if pd.notnull(r) else pd.NaT)

                # Definir col_data ANTES de qualquer uso
                col_data = 'data_completa'

                # Só depois use col_data
                participacoes_inicio = participacoes_inicio_raw.drop_duplicates(subset=['UsuarioID', col_data])
                usuarios_participantes = participacoes_inicio.groupby(col_data)['UsuarioID'].nunique().reset_index(name='Usuarios_participantes')
                df_acessos_filtrado = df_acessos.copy()
                if filtros.get('ambiente') and 'NomeAmbiente' in df_ambientes.columns:
                    usuarios_ambiente = df_ambientes[df_ambientes['NomeAmbiente'].isin(filtros['ambiente'])]['UsuarioID'].unique()
                    df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_ambiente)]
                if filtros.get('perfil') and 'PerfilNaTrilha' in df_ambientes.columns:
                    usuarios_perfil = df_ambientes[df_ambientes['PerfilNaTrilha'].isin(filtros['perfil'])]['UsuarioID'].unique()
                    df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_perfil)]
                if filtros.get('trilha') and 'NomeTrilha' in df_ambientes.columns:
                    usuarios_trilha = df_ambientes[df_ambientes['NomeTrilha'].isin(filtros['trilha'])]['UsuarioID'].unique()
                    df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_trilha)]
                if filtros.get('modulo') and 'NomeModulo' in df_ambientes.columns:
                    usuarios_modulo = df_ambientes[df_ambientes['NomeModulo'].isin(filtros['modulo'])]['UsuarioID'].unique()
                    df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_modulo)]
                if filtros.get('grupo') and 'TodosGruposUsuario' in df_ambientes.columns:
                    usuarios_grupo = df_ambientes[df_ambientes['TodosGruposUsuario'].isin(filtros['grupo'])]['UsuarioID'].unique()
                    df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_grupo)]
                df_acessos_filtrado['DataAcesso'] = pd.to_datetime(df_acessos_filtrado['DataAcesso'], dayfirst=True, errors='coerce').dt.date
                # Garantir que ambos os lados da comparação são date
                data_min = pd.to_datetime(consolidado_filtrado['DataAcesso'].min())
                data_max = pd.to_datetime(consolidado_filtrado['DataAcesso'].max())
                df_acessos_filtrado = df_acessos_filtrado[
                    (pd.to_datetime(df_acessos_filtrado['DataAcesso']) >= data_min) &
                    (pd.to_datetime(df_acessos_filtrado['DataAcesso']) <= data_max)
                ]
                total_acessos = df_acessos_filtrado.shape[0]
                # Aplicar filtros ao DataFrame de participações antes de calcular o total de usuários com participação
                participacoes_inicio_filtrado = participacoes_inicio_raw.copy()
                if filtros.get('ambiente') and 'NomeAmbiente' in participacoes_inicio_filtrado.columns:
                    participacoes_inicio_filtrado = participacoes_inicio_filtrado[participacoes_inicio_filtrado['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil') and 'PerfilNaTrilha' in participacoes_inicio_filtrado.columns:
                    participacoes_inicio_filtrado = participacoes_inicio_filtrado[participacoes_inicio_filtrado['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha') and 'NomeTrilha' in participacoes_inicio_filtrado.columns:
                    participacoes_inicio_filtrado = participacoes_inicio_filtrado[participacoes_inicio_filtrado['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo') and 'NomeModulo' in participacoes_inicio_filtrado.columns:
                    participacoes_inicio_filtrado = participacoes_inicio_filtrado[participacoes_inicio_filtrado['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo') and 'TodosGruposUsuario' in participacoes_inicio_filtrado.columns:
                    participacoes_inicio_filtrado = participacoes_inicio_filtrado[participacoes_inicio_filtrado['TodosGruposUsuario'].isin(filtros['grupo'])]
                # Calcular total_usuarios_com_participacao corretamente após deduplicação e filtros
                total_usuarios_com_participacao = participacoes_inicio_filtrado['UsuarioID'].nunique()
                percentual_participacao = (
                    total_usuarios_com_participacao / total_usuarios * 100
                ) if total_usuarios > 0 else 0

                participacoes_filtrado = df_ambientes.dropna(subset=['DataInicioModulo']).copy()
                participacoes_filtrado = participacoes_filtrado.rename(columns={'DataInicioModulo': 'DataAcesso'})
                if filtros.get('ambiente') and 'NomeAmbiente' in participacoes_filtrado.columns:
                    participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil') and 'PerfilNaTrilha' in participacoes_filtrado.columns:
                    participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha') and 'NomeTrilha' in participacoes_filtrado.columns:
                    participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo') and 'NomeModulo' in participacoes_filtrado.columns:
                    participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo') and 'TodosGruposUsuario' in participacoes_filtrado.columns:
                    participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['TodosGruposUsuario'].isin(filtros['grupo'])]
                participacoes_filtrado['DataAcesso'] = pd.to_datetime(participacoes_filtrado['DataAcesso'])
                if isinstance(periodo, tuple) and len(periodo) == 2:
                    data_ini, data_fi = periodo
                    data_ini = pd.to_datetime(data_ini)
                    data_fi = pd.to_datetime(data_fi)
                    participacoes_filtrado = participacoes_filtrado[
                        (participacoes_filtrado['DataAcesso'] >= data_ini) &
                        (participacoes_filtrado['DataAcesso'] <= data_fi)
                    ]
                total_participacoes = participacoes_filtrado.shape[0]

                # --- AJUSTE FINAL: Indicadores respeitando todos os filtros e o período ---
                # 1. Aplique todos os filtros no DataFrame de acessos
                df_acessos_indicador = df_acessos.copy()
                if filtros.get('ambiente') and 'NomeAmbiente' in df_ambientes.columns:
                    usuarios_ambiente = df_ambientes[df_ambientes['NomeAmbiente'].isin(filtros['ambiente'])]['UsuarioID'].unique()
                    df_acessos_indicador = df_acessos_indicador[df_acessos_indicador['UsuarioID'].isin(usuarios_ambiente)]
                if filtros.get('perfil') and 'PerfilNaTrilha' in df_ambientes.columns:
                    usuarios_perfil = df_ambientes[df_ambientes['PerfilNaTrilha'].isin(filtros['perfil'])]['UsuarioID'].unique()
                    df_acessos_indicador = df_acessos_indicador[df_acessos_indicador['UsuarioID'].isin(usuarios_perfil)]
                if filtros.get('trilha') and 'NomeTrilha' in df_ambientes.columns:
                    usuarios_trilha = df_ambientes[df_ambientes['NomeTrilha'].isin(filtros['trilha'])]['UsuarioID'].unique()
                    df_acessos_indicador = df_acessos_indicador[df_acessos_indicador['UsuarioID'].isin(usuarios_trilha)]
                if filtros.get('modulo') and 'NomeModulo' in df_ambientes.columns:
                    usuarios_modulo = df_ambientes[df_ambientes['NomeModulo'].isin(filtros['modulo'])]['UsuarioID'].unique()
                    df_acessos_indicador = df_acessos_indicador[df_acessos_indicador['UsuarioID'].isin(usuarios_modulo)]
                if filtros.get('grupo') and 'TodosGruposUsuario' in df_ambientes.columns:
                    usuarios_grupo = df_ambientes[df_ambientes['TodosGruposUsuario'].isin(filtros['grupo'])]['UsuarioID'].unique()
                    df_acessos_indicador = df_acessos_indicador[df_acessos_indicador['UsuarioID'].isin(usuarios_grupo)]
                # 2. Filtro de período
                if isinstance(periodo, tuple) and len(periodo) == 2:
                    data_ini, data_fi = periodo
                    data_ini = pd.to_datetime(data_ini)
                    data_fi = pd.to_datetime(data_fi)
                    df_acessos_indicador['DataAcesso'] = pd.to_datetime(df_acessos_indicador['DataAcesso'], dayfirst=True, errors='coerce')
                    df_acessos_indicador = df_acessos_indicador[(df_acessos_indicador['DataAcesso'] >= data_ini) & (df_acessos_indicador['DataAcesso'] <= data_fi)]
                usuarios_com_acesso = df_acessos_indicador['UsuarioID'].nunique()

                col1, col2 = st.columns(2)
                col1.metric("Usuários com Acesso", usuarios_com_acesso)
                col2.metric("Total de Acessos", total_acessos)

                # Gráfico apenas de Usuários com Acesso
                ids_acesso_por_data = df_filtrado.groupby('DataAcesso')['UsuarioID'].apply(lambda x: ', '.join(map(str, x.drop_duplicates()))).reset_index(name='IDs_acesso')
                usuarios_acesso = usuarios_acesso.merge(ids_acesso_por_data, on='DataAcesso', how='left')
                usuarios_acesso['DataLabel'] = pd.to_datetime(usuarios_acesso['DataAcesso']).dt.strftime('%d/%m/%Y')
                usuarios_acesso['DataX'] = pd.to_datetime(usuarios_acesso['DataLabel'], dayfirst=True, errors='coerce')

                base = alt.Chart(usuarios_acesso).encode(
                    x=alt.X('DataX:T', title='Data', axis=alt.Axis(labelExpr="datum.value ? timeFormat(datum.value, '%d/%m/%Y') : ''")),
                    y=alt.Y('Usuarios_com_acesso:Q', title='Quantidade de usuários'),
                    tooltip=[
                        alt.Tooltip('DataLabel:N', title='Data'),
                        alt.Tooltip('Usuarios_com_acesso:Q', title='Usuários com Acesso'),
                        alt.Tooltip('IDs_acesso:N', title='IDs dos Usuários')
                    ]
                )

                line = base.mark_line(strokeWidth=4, color='#1f77b4')
                points = base.mark_circle(size=80, color='#1f77b4')

                chart = (line + points).properties(
                    width=800,
                    height=400,
                    title='Usuários com Acesso por Dia'
                )

                st.altair_chart(chart, use_container_width=True)

                # Merge para trazer PerfilNaTrilha prioritário para df
                if 'UsuarioID' in df_acessos.columns and 'UsuarioID' in df_ambientes.columns:
                    prioridade = {'Obrigatório': 1, 'Participa': 2, 'Gestor': 3}
                    df_perfis = df_ambientes[['UsuarioID', 'PerfilNaTrilha']].dropna().copy()
                    df_perfis['prioridade'] = df_perfis['PerfilNaTrilha'].map(prioridade).fillna(99)
                    df_perfis = df_perfis.sort_values('prioridade').drop_duplicates('UsuarioID', keep='first')
                    df_perfis = df_perfis[['UsuarioID', 'PerfilNaTrilha']]
                    df = df.drop(columns=['PerfilNaTrilha'], errors='ignore')
                    df = df.merge(df_perfis, on='UsuarioID', how='left')
                # Aplicar filtro de perfil diretamente em df
                if filtros.get('perfil') and 'PerfilNaTrilha' in df.columns:
                    df = df[df['PerfilNaTrilha'].isin(filtros['perfil'])]

        else:
            st.error("Sua planilha precisa ter as colunas 'DataAcesso' e 'UsuarioID' na aba de acessos. As colunas encontradas foram: " + str(df.columns.tolist()))
    else:
        st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'. Abas encontradas: " + str(list(abas.keys())))
        st.info("Por favor, faça upload da planilha Excel original.")