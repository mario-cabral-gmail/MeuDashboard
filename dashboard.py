import streamlit as st
import pandas as pd
import altair as alt
import locale

# Configuração da página
st.set_page_config(page_title="Dashboard de Acessos", layout="wide", page_icon="📊")


# Título e descrição
st.title("📊 Dashboard de Acessos")
st.markdown("Visualize os acessos por dia, ambiente, perfil, trilha, módulo e grupo de forma interativa e moderna.")

# Configura o locale para datas em português do Brasil
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass  # Em alguns sistemas pode não funcionar, mas não impede o funcionamento

arquivo = st.file_uploader("Faça upload da planilha Excel", type=["xlsx"])

if arquivo:
    abas = pd.read_excel(arquivo, sheet_name=None)
    st.write("Abas encontradas na planilha:", list(abas.keys()))

    if 'Acessos' in abas and 'UsuariosAmbientes' in abas:
        df_acessos = abas['Acessos']
        df_ambientes = abas['UsuariosAmbientes']

        # Merge para trazer todos os campos extras, incluindo grupo
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

        # Conversão de datas
        if 'DataAcesso' in df.columns and 'UsuarioID' in df.columns:
            df['DataAcesso'] = pd.to_datetime(df['DataAcesso'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['DataAcesso'])
            df['DataAcesso'] = df['DataAcesso'].dt.date

            # Range de datas total (antes dos filtros)
            data_inicio_total = df['DataAcesso'].min()
            data_fim_total = df['DataAcesso'].max()

            # Conversão das datas de participação
            if 'DataInicioModulo' in df_ambientes.columns:
                df_ambientes['DataInicioModulo'] = pd.to_datetime(df_ambientes['DataInicioModulo'], dayfirst=True, errors='coerce').dt.date
            if 'DataConclusaoModulo' in df_ambientes.columns:
                df_ambientes['DataConclusaoModulo'] = pd.to_datetime(df_ambientes['DataConclusaoModulo'], dayfirst=True, errors='coerce').dt.date

            # Participações por data de início do módulo (apenas DataInicioModulo)
            participacoes_inicio = df_ambientes[['UsuarioID', 'DataInicioModulo', 'NomeAmbiente', 'PerfilNaTrilha', 'NomeTrilha', 'NomeModulo', 'TodosGruposUsuario']].dropna(subset=['DataInicioModulo'])

            # Filtros dinâmicos
            st.markdown("### Filtros")
            colf1, colf2, colf3, colf4, colf5 = st.columns(5)

            # Ambiente
            if 'NomeAmbiente' in df.columns:
                ambientes_unicos = sorted(df['NomeAmbiente'].dropna().unique())
                ambiente_selecionado = colf1.multiselect("Filtrar por ambiente:", ambientes_unicos)
                if ambiente_selecionado:
                    df = df[df['NomeAmbiente'].isin(ambiente_selecionado)]

            # Perfil na trilha (com seleção padrão)
            if 'PerfilNaTrilha' in df.columns:
                perfis_unicos = sorted(df['PerfilNaTrilha'].dropna().unique())
                # Seleção padrão: 'Obrigatório' e 'Participa' se existirem
                default_perfis = [p for p in ['Obrigatório', 'Participa'] if p in perfis_unicos]
                perfil_selecionado = colf2.multiselect(
                    "Filtrar por perfil na trilha:",
                    perfis_unicos,
                    default=default_perfis
                )
                if perfil_selecionado:
                    df = df[df['PerfilNaTrilha'].isin(perfil_selecionado)]

            # Nome da trilha
            if 'NomeTrilha' in df.columns:
                trilhas_unicas = sorted(df['NomeTrilha'].dropna().unique())
                trilha_selecionada = colf3.multiselect("Filtrar por trilha:", trilhas_unicas)
                if trilha_selecionada:
                    df = df[df['NomeTrilha'].isin(trilha_selecionada)]

            # Nome do módulo
            if 'NomeModulo' in df.columns:
                modulos_unicos = sorted(df['NomeModulo'].dropna().unique())
                modulo_selecionado = colf4.multiselect("Filtrar por módulo:", modulos_unicos)
                if modulo_selecionado:
                    df = df[df['NomeModulo'].isin(modulo_selecionado)]

            # Grupo
            if 'TodosGruposUsuario' in df.columns:
                grupos_unicos = sorted(df['TodosGruposUsuario'].dropna().unique())
                grupo_selecionado = colf5.multiselect("Filtrar por grupo:", grupos_unicos)
                if grupo_selecionado:
                    df = df[df['TodosGruposUsuario'].isin(grupo_selecionado)]

            # Aplique os mesmos filtros em participacoes_inicio
            if 'NomeAmbiente' in participacoes_inicio.columns and ambiente_selecionado:
                participacoes_inicio = participacoes_inicio[participacoes_inicio['NomeAmbiente'].isin(ambiente_selecionado)]
            if 'PerfilNaTrilha' in participacoes_inicio.columns and perfil_selecionado:
                participacoes_inicio = participacoes_inicio[participacoes_inicio['PerfilNaTrilha'].isin(perfil_selecionado)]
            if 'NomeTrilha' in participacoes_inicio.columns and trilha_selecionada:
                participacoes_inicio = participacoes_inicio[participacoes_inicio['NomeTrilha'].isin(trilha_selecionada)]
            if 'NomeModulo' in participacoes_inicio.columns and modulo_selecionado:
                participacoes_inicio = participacoes_inicio[participacoes_inicio['NomeModulo'].isin(modulo_selecionado)]
            if 'TodosGruposUsuario' in participacoes_inicio.columns and grupo_selecionado:
                participacoes_inicio = participacoes_inicio[participacoes_inicio['TodosGruposUsuario'].isin(grupo_selecionado)]

            participacoes_inicio = participacoes_inicio.rename(columns={'DataInicioModulo': 'DataAcesso'})
            # Conta usuários únicos por dia (participaram em início)
            participacoes_inicio = participacoes_inicio.groupby('DataAcesso')['UsuarioID'].nunique().reset_index()
            participacoes_inicio = participacoes_inicio.rename(columns={'UsuarioID': 'Usuarios_participantes'})

            # Consolidação de acessos por dia
            consolidado = df.groupby('DataAcesso')['UsuarioID'].nunique().reset_index()
            consolidado = consolidado.rename(columns={'UsuarioID': 'Usuarios_com_acesso'})
            consolidado = consolidado.sort_values('DataAcesso')

            # Datas contínuas
            datas_continuas = pd.DataFrame({'DataAcesso': pd.date_range(start=data_inicio_total, end=data_fim_total)})
            datas_continuas['DataAcesso'] = datas_continuas['DataAcesso'].dt.date
            consolidado = datas_continuas.merge(consolidado, on='DataAcesso', how='left')

            # Merge com participações (apenas DataInicioModulo)
            consolidado = consolidado.merge(participacoes_inicio, on='DataAcesso', how='left')
            consolidado[['Usuarios_com_acesso', 'Usuarios_participantes']] = \
                consolidado[['Usuarios_com_acesso', 'Usuarios_participantes']].fillna(0).astype(int)

            # Filtro de período com opções rápidas (usando range total)
            st.markdown("### Período")
            ano_atual = data_fim_total.year
            ano_passado = ano_atual - 1
            # Calcula datas de início e fim para este ano e ano passado
            inicio_ano_atual = pd.to_datetime(f"01/01/{ano_atual}", dayfirst=True).date()
            fim_ano_atual = pd.to_datetime(f"31/12/{ano_atual}", dayfirst=True).date()
            inicio_ano_passado = pd.to_datetime(f"01/01/{ano_passado}", dayfirst=True).date()
            fim_ano_passado = pd.to_datetime(f"31/12/{ano_passado}", dayfirst=True).date()
            # Garante que os limites estejam dentro do range dos dados
            inicio_ano_atual = max(inicio_ano_atual, data_inicio_total)
            fim_ano_atual = min(fim_ano_atual, data_fim_total)
            inicio_ano_passado = max(inicio_ano_passado, data_inicio_total)
            fim_ano_passado = min(fim_ano_passado, data_fim_total)
            opcoes_periodo = {
                'Período completo': (data_inicio_total, data_fim_total),
                'Últimos 7 dias': (data_fim_total - pd.Timedelta(days=6), data_fim_total),
                'Últimos 30 dias': (data_fim_total - pd.Timedelta(days=29), data_fim_total),
                'Este mês': (data_fim_total.replace(day=1), data_fim_total),
                'Mês passado': ((data_fim_total.replace(day=1) - pd.Timedelta(days=1)).replace(day=1), data_fim_total.replace(day=1) - pd.Timedelta(days=1)),
                'Este ano': (inicio_ano_atual, fim_ano_atual),
                'Ano passado': (inicio_ano_passado, fim_ano_passado),
                'Personalizado': None
            }
            escolha_periodo = st.selectbox("Selecione um período rápido ou escolha personalizado:", list(opcoes_periodo.keys()), index=0)
            if escolha_periodo != 'Personalizado':
                periodo = opcoes_periodo[escolha_periodo]
            else:
                periodo = st.date_input(
                    "Selecione o período:",
                    value=(data_inicio_total, data_fim_total),  # Sempre período completo por padrão
                    min_value=data_inicio_total,
                    max_value=data_fim_total,
                    format="DD/MM/YYYY"
                )

            if isinstance(periodo, tuple) and len(periodo) == 2:
                data_ini, data_fi = periodo
                mask = (consolidado['DataAcesso'] >= data_ini) & (consolidado['DataAcesso'] <= data_fi)
                consolidado_filtrado = consolidado.loc[mask]
            else:
                consolidado_filtrado = consolidado

            # KPIs (após filtros)
            total_usuarios = df['UsuarioID'].nunique()
            total_ambientes = df['NomeAmbiente'].nunique() if 'NomeAmbiente' in df.columns else 0
            total_perfis = df['PerfilNaTrilha'].nunique() if 'PerfilNaTrilha' in df.columns else 0
            participacoes_inicio_raw = df_ambientes.dropna(subset=['DataInicioModulo']).copy()
            participacoes_inicio_raw = participacoes_inicio_raw.rename(columns={'DataInicioModulo': 'DataAcesso'})

            # Aplicar os mesmos filtros
            if 'NomeAmbiente' in participacoes_inicio_raw.columns and ambiente_selecionado:
                participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['NomeAmbiente'].isin(ambiente_selecionado)]
            if 'PerfilNaTrilha' in participacoes_inicio_raw.columns and perfil_selecionado:
                participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['PerfilNaTrilha'].isin(perfil_selecionado)]
            if 'NomeTrilha' in participacoes_inicio_raw.columns and trilha_selecionada:
                participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['NomeTrilha'].isin(trilha_selecionada)]
            if 'NomeModulo' in participacoes_inicio_raw.columns and modulo_selecionado:
                participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['NomeModulo'].isin(modulo_selecionado)]
            if 'TodosGruposUsuario' in participacoes_inicio_raw.columns and grupo_selecionado:
                participacoes_inicio_raw = participacoes_inicio_raw[participacoes_inicio_raw['TodosGruposUsuario'].isin(grupo_selecionado)]

            # Agora sim, filtrar pelo período
            total_usuarios_com_participacao = participacoes_inicio_raw[
                (participacoes_inicio_raw['DataAcesso'] >= consolidado_filtrado['DataAcesso'].min()) &
                (participacoes_inicio_raw['DataAcesso'] <= consolidado_filtrado['DataAcesso'].max())
            ]['UsuarioID'].nunique()
            # Cálculo do total de acessos diretamente da aba original 'Acessos'
            df_acessos_filtrado = df_acessos.copy()
            if ambiente_selecionado and 'NomeAmbiente' in df_ambientes.columns:
                usuarios_ambiente = df_ambientes[df_ambientes['NomeAmbiente'].isin(ambiente_selecionado)]['UsuarioID'].unique()
                df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_ambiente)]
            if perfil_selecionado and 'PerfilNaTrilha' in df_ambientes.columns:
                usuarios_perfil = df_ambientes[df_ambientes['PerfilNaTrilha'].isin(perfil_selecionado)]['UsuarioID'].unique()
                df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_perfil)]
            if trilha_selecionada and 'NomeTrilha' in df_ambientes.columns:
                usuarios_trilha = df_ambientes[df_ambientes['NomeTrilha'].isin(trilha_selecionada)]['UsuarioID'].unique()
                df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_trilha)]
            if modulo_selecionado and 'NomeModulo' in df_ambientes.columns:
                usuarios_modulo = df_ambientes[df_ambientes['NomeModulo'].isin(modulo_selecionado)]['UsuarioID'].unique()
                df_acessos_filtrado = df_acessos_filtrado[df_acessos_filtrado['UsuarioID'].isin(usuarios_modulo)]
            if grupo_selecionado and 'TodosGruposUsuario' in df_ambientes.columns:
                usuarios_grupo = df_ambientes[df_ambientes['TodosGruposUsuario'].isin(grupo_selecionado)]['UsuarioID'].unique()
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

            # Indicador de Total de Participações
            participacoes_filtrado = df_ambientes.dropna(subset=['DataInicioModulo']).copy()
            participacoes_filtrado = participacoes_filtrado.rename(columns={'DataInicioModulo': 'DataAcesso'})
            if ambiente_selecionado and 'NomeAmbiente' in participacoes_filtrado.columns:
                participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['NomeAmbiente'].isin(ambiente_selecionado)]
            if perfil_selecionado and 'PerfilNaTrilha' in participacoes_filtrado.columns:
                participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['PerfilNaTrilha'].isin(perfil_selecionado)]
            if trilha_selecionada and 'NomeTrilha' in participacoes_filtrado.columns:
                participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['NomeTrilha'].isin(trilha_selecionada)]
            if modulo_selecionado and 'NomeModulo' in participacoes_filtrado.columns:
                participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['NomeModulo'].isin(modulo_selecionado)]
            if grupo_selecionado and 'TodosGruposUsuario' in participacoes_filtrado.columns:
                participacoes_filtrado = participacoes_filtrado[participacoes_filtrado['TodosGruposUsuario'].isin(grupo_selecionado)]
            participacoes_filtrado['DataAcesso'] = pd.to_datetime(participacoes_filtrado['DataAcesso'], dayfirst=True, errors='coerce').dt.date
            participacoes_filtrado = participacoes_filtrado[
                (participacoes_filtrado['DataAcesso'] >= consolidado_filtrado['DataAcesso'].min()) &
                (participacoes_filtrado['DataAcesso'] <= consolidado_filtrado['DataAcesso'].max())
            ]
            total_participacoes = participacoes_filtrado.shape[0]

            # Bloco 1: Indicadores principais
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

            # Bloco 2: Indicadores de acessos e médias
            col6, col7, col8, col9 = st.columns(4)
            col6.metric("Total de Acessos", total_acessos)
            col7.metric("Média diária de acessos", f"{media_diaria_acessos:.1f}")
            col8.metric("Média diária de participações", f"{media_diaria_participantes:.1f}")
            col9.metric("% de participação", f"{percentual_participacao:.1f}%")

            # Prepara dados para gráfico com legenda
            consolidado_long = pd.melt(
                consolidado_filtrado,
                id_vars=['DataAcesso'],
                value_vars=['Usuarios_com_acesso', 'Usuarios_participantes'],
                var_name='Tipo',
                value_name='Quantidade'
            )

            # Renomeia para legenda amigável
            consolidado_long['Tipo'] = consolidado_long['Tipo'].map({
                'Usuarios_com_acesso': 'Usuários com acesso',
                'Usuarios_participantes': 'Usuários participantes'
            })

            # Gráfico Altair com duas linhas
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
                        range=['#1f77b4', '#43A047']  # azul para acesso, verde para participantes
                    )
                ),
                strokeDash=alt.StrokeDash(
                    'Tipo:N',
                    legend=None,
                    scale=alt.Scale(
                        domain=['Usuários com acesso', 'Usuários participantes'],
                        range=[[6,6], []]  # Tracejado para acesso, sólido para participantes
                    )
                )
            )

            # Linhas com maior destaque
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

            # Tabela detalhada
            st.markdown("### Dados detalhados")
            st.dataframe(consolidado_filtrado, use_container_width=True)

            st.markdown("### Explorar dados brutos por dia")

            datas_disponiveis = consolidado_filtrado['DataAcesso'].drop_duplicates().sort_values()
            data_selecionada = st.selectbox(
                "Selecione uma data para ver os dados brutos:",
                datas_disponiveis,
                format_func=lambda d: d.strftime('%d/%m/%Y')
            )

            # Filtra os dados brutos do período e da data selecionada
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
else:
    st.info("Por favor, faça upload da planilha Excel original.")