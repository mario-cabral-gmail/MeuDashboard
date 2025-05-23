import streamlit as st
import pandas as pd
import altair as alt
import locale

def app(arquivo, filtros):
    st.title("📊 Dashboard de Acessos")
    st.markdown("Visualize os acessos por dia, ambiente, perfil, trilha, módulo e grupo de forma interativa e moderna.")

    # Configura o locale para datas em português do Brasil
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        pass

    if arquivo:
        abas = pd.read_excel(arquivo, sheet_name=None)
        st.write("Abas encontradas na planilha:", list(abas.keys()))

        if 'Acessos' in abas and 'UsuariosAmbientes' in abas:
            df_acessos = abas['Acessos']
            df_ambientes = abas['UsuariosAmbientes']

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
                df['DataAcesso'] = pd.to_datetime(df['DataAcesso'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DataAcesso'])
                df['DataAcesso'] = df['DataAcesso'].dt.date

                data_inicio_total = df['DataAcesso'].min()
                data_fim_total = df['DataAcesso'].max()

                if 'DataInicioModulo' in df_ambientes.columns:
                    df_ambientes['DataInicioModulo'] = pd.to_datetime(df_ambientes['DataInicioModulo'], dayfirst=True, errors='coerce').dt.date
                if 'DataConclusaoModulo' in df_ambientes.columns:
                    df_ambientes['DataConclusaoModulo'] = pd.to_datetime(df_ambientes['DataConclusaoModulo'], dayfirst=True, errors='coerce').dt.date

                participacoes_inicio = df_ambientes[['UsuarioID', 'DataInicioModulo', 'NomeAmbiente', 'PerfilNaTrilha', 'NomeTrilha', 'NomeModulo', 'TodosGruposUsuario']].dropna(subset=['DataInicioModulo'])

                # Aplicar filtros recebidos
                if filtros.get('ambiente'):
                    df = df[df['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil'):
                    df = df[df['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha'):
                    df = df[df['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo'):
                    df = df[df['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo'):
                    df = df[df['TodosGruposUsuario'].isin(filtros['grupo'])]

                if filtros.get('ambiente'):
                    participacoes_inicio = participacoes_inicio[participacoes_inicio['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil'):
                    participacoes_inicio = participacoes_inicio[participacoes_inicio['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha'):
                    participacoes_inicio = participacoes_inicio[participacoes_inicio['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo'):
                    participacoes_inicio = participacoes_inicio[participacoes_inicio['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo'):
                    participacoes_inicio = participacoes_inicio[participacoes_inicio['TodosGruposUsuario'].isin(filtros['grupo'])]

                participacoes_inicio = participacoes_inicio.rename(columns={'DataInicioModulo': 'DataAcesso'})
                participacoes_inicio = participacoes_inicio.groupby('DataAcesso')['UsuarioID'].nunique().reset_index()
                participacoes_inicio = participacoes_inicio.rename(columns={'UsuarioID': 'Usuarios_participantes'})

                consolidado = df.groupby('DataAcesso')['UsuarioID'].nunique().reset_index()
                consolidado = consolidado.rename(columns={'UsuarioID': 'Usuarios_com_acesso'})
                consolidado = consolidado.sort_values('DataAcesso')

                datas_continuas = pd.DataFrame({'DataAcesso': pd.date_range(start=data_inicio_total, end=data_fim_total)})
                datas_continuas['DataAcesso'] = datas_continuas['DataAcesso'].dt.date
                consolidado = datas_continuas.merge(consolidado, on='DataAcesso', how='left')

                consolidado = consolidado.merge(participacoes_inicio, on='DataAcesso', how='left')
                consolidado[['Usuarios_com_acesso', 'Usuarios_participantes']] = \
                    consolidado[['Usuarios_com_acesso', 'Usuarios_participantes']].fillna(0).astype(int)

                # Usar o período recebido nos filtros
                periodo = filtros.get('periodo')
                if isinstance(periodo, tuple) and len(periodo) == 2:
                    data_ini, data_fi = periodo
                    # Garantir que ambos sejam datetime.date
                    data_ini = pd.to_datetime(data_ini).date()
                    data_fi = pd.to_datetime(data_fi).date()
                    consolidado['DataAcesso'] = pd.to_datetime(consolidado['DataAcesso']).dt.date
                    mask = (consolidado['DataAcesso'] >= data_ini) & (consolidado['DataAcesso'] <= data_fi)
                    consolidado_filtrado = consolidado.loc[mask]
                else:
                    consolidado_filtrado = consolidado

                total_usuarios = df['UsuarioID'].nunique()
                total_ambientes = df['NomeAmbiente'].nunique() if 'NomeAmbiente' in df.columns else 0
                total_perfis = df['PerfilNaTrilha'].nunique() if 'PerfilNaTrilha' in df.columns else 0
                participacoes_inicio_raw = df_ambientes.dropna(subset=['DataInicioModulo']).copy()
                participacoes_inicio_raw = participacoes_inicio_raw.rename(columns={'DataInicioModulo': 'DataAcesso'})
                if filtros.get('ambiente'):
                    participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['NomeAmbiente'].isin(filtros['ambiente'])]
                if filtros.get('perfil'):
                    participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['PerfilNaTrilha'].isin(filtros['perfil'])]
                if filtros.get('trilha'):
                    participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['NomeTrilha'].isin(filtros['trilha'])]
                if filtros.get('modulo'):
                    participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['NomeModulo'].isin(filtros['modulo'])]
                if filtros.get('grupo'):
                    participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['TodosGruposUsuario'].isin(filtros['grupo'])]
                total_usuarios_com_participacao = participacoes_inicio_raw[
                    (participacoes_inicio_raw['DataAcesso'] >= consolidado_filtrado['DataAcesso'].min()) &
                    (participacoes_inicio_raw['DataAcesso'] <= consolidado_filtrado['DataAcesso'].max())
                ]['UsuarioID'].nunique()
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
                df_acessos_filtrado = df_acessos_filtrado[
                    (df_acessos_filtrado['DataAcesso'] >= consolidado_filtrado['DataAcesso'].min()) &
                    (df_acessos_filtrado['DataAcesso'] <= consolidado_filtrado['DataAcesso'].max())
                ]
                total_acessos = df_acessos_filtrado.shape[0]
                media_diaria_acessos = consolidado_filtrado['Usuarios_com_acesso'].mean() if not consolidado_filtrado.empty else 0
                media_diaria_participantes = consolidado_filtrado['Usuarios_participantes'].mean() if not consolidado_filtrado.empty else 0
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
                participacoes_filtrado['DataAcesso'] = pd.to_datetime(participacoes_filtrado['DataAcesso'], dayfirst=True, errors='coerce').dt.date
                participacoes_filtrado = participacoes_filtrado[
                    (participacoes_filtrado['DataAcesso'] >= consolidado_filtrado['DataAcesso'].min()) &
                    (participacoes_filtrado['DataAcesso'] <= consolidado_filtrado['DataAcesso'].max())
                ]
                total_participacoes = participacoes_filtrado.shape[0]

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Total de Usuários", total_usuarios)
                with col1.expander("Ver detalhes usuários"):
                    st.dataframe(df[['UsuarioID']].drop_duplicates())

                col2.metric("Total de Ambientes", total_ambientes)
                with col2.expander("Ver detalhes ambientes"):
                    st.dataframe(df[['NomeAmbiente']].drop_duplicates())

                col3.metric("Total de Perfis", total_perfis)
                with col3.expander("Ver detalhes perfis"):
                    st.dataframe(df[['PerfilNaTrilha']].drop_duplicates())

                col4.metric("Total de Usuários com Participação", total_usuarios_com_participacao)
                with col4.expander("Ver detalhes participação"):
                    st.dataframe(participacoes_inicio_raw[['UsuarioID', 'DataAcesso']].drop_duplicates())

                col5.metric("Total de Participações", total_participacoes)
                with col5.expander("Ver detalhes participações"):
                    st.dataframe(participacoes_filtrado)

                col6, col7, col8, col9 = st.columns(4)
                col6.metric("Total de Acessos", total_acessos)
                with col6.expander("Ver detalhes acessos"):
                    st.dataframe(df_acessos_filtrado)
                col7.metric("Média diária de acessos", f"{media_diaria_acessos:.1f}")
                col8.metric("Média diária de participações", f"{media_diaria_participantes:.1f}")
                col9.metric("% de participação", f"{percentual_participacao:.1f}%")

                consolidado_long = pd.melt(
                    consolidado_filtrado,
                    id_vars=['DataAcesso'],
                    value_vars=['Usuarios_com_acesso', 'Usuarios_participantes'],
                    var_name='Tipo',
                    value_name='Quantidade'
                )

                consolidado_long['Tipo'] = consolidado_long['Tipo'].map({
                    'Usuarios_com_acesso': 'Usuários com acesso',
                    'Usuarios_participantes': 'Usuários participantes'
                })

                st.markdown("### Evolução dos acessos e participações")

                hover = alt.selection_single(
                    fields=["DataAcesso"],
                    nearest=True,
                    on="mouseover",
                    empty="none",
                    clear="mouseout"
                )

                base = alt.Chart(consolidado_long).encode(
                    x=alt.X('DataAcesso:T', title='Data de Acesso', axis=alt.Axis(format='%d/%m/%Y')),
                    color=alt.Color(
                        'Tipo:N',
                        title='Indicador',
                        legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(
                            domain=['Usuários com acesso', 'Usuários participantes'],
                            range=['#1f77b4', '#43A047']
                        )
                    ),
                    strokeDash=alt.StrokeDash(
                        'Tipo:N',
                        legend=None,
                        scale=alt.Scale(
                            domain=['Usuários com acesso', 'Usuários participantes'],
                            range=[[6,6], []]
                        )
                    )
                )

                line = base.mark_line(strokeWidth=4).encode(
                    y=alt.Y('Quantidade:Q', title='Quantidade de usuários')
                )

                points = base.mark_circle(size=80).encode(
                    y='Quantidade:Q',
                    opacity=alt.value(0)
                ).add_selection(
                    hover
                )

                tooltips = base.mark_rule().encode(
                    opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
                    tooltip=[
                        alt.Tooltip('DataAcesso:T', title='Data', format='%d/%m/%Y'),
                        alt.Tooltip('Tipo:N', title='Indicador'),
                        alt.Tooltip('Quantidade:Q', title='Quantidade')
                    ]
                ).transform_filter(
                    hover
                )

                chart = (line + points + tooltips).properties(
                    width=900,
                    height=400
                )

                st.altair_chart(chart, use_container_width=True)

                st.markdown("### Dados detalhados")
                st.dataframe(consolidado_filtrado, use_container_width=True)

                st.markdown("### Explorar dados brutos por dia")

                datas_disponiveis = consolidado_filtrado['DataAcesso'].drop_duplicates().sort_values()
                data_selecionada = st.selectbox(
                    "Selecione uma data para ver os dados brutos:",
                    datas_disponiveis,
                    format_func=lambda d: d.strftime('%d/%m/%Y')
                )

                dados_brutos_dia = df[df['DataAcesso'] == data_selecionada]

                st.markdown(f"#### Dados brutos para {data_selecionada.strftime('%d/%m/%Y')}")
                st.dataframe(dados_brutos_dia, use_container_width=True)

                st.write("Amostra dos dados de acesso após filtros:")
                st.dataframe(df[['UsuarioID', 'DataAcesso']].drop_duplicates())

                st.write("Linhas em df após filtros:", df.shape[0])
                st.write("Período considerado:", consolidado_filtrado['DataAcesso'].min(), consolidado_filtrado['DataAcesso'].max())
        else:
            st.error("Sua planilha precisa ter as colunas 'DataAcesso' e 'UsuarioID' na aba de acessos. As colunas encontradas foram: " + str(df.columns.tolist()))
    else:
        st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'. Abas encontradas: " + str(list(abas.keys())))
        st.info("Por favor, faça upload da planilha Excel original.")