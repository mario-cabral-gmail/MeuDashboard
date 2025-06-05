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
        Engajamento
        <span class="tooltip">
            <b style="color:#888; font-size:1.1em; cursor:help;">&#9432;</b>
            <span class="tooltiptext">
                Exibe a proporção de usuários cadastrados que acessaram a trilha no período.<br>
                🕒 Usuários cadastrados até a data final do período são considerados. Acessos devem estar dentro do intervalo de datas.
            </span>
        </span>
    </h3>
    ''', unsafe_allow_html=True)
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
            # Merge para trazer PerfilNaTrilha para df_acessos, priorizando Obrigatório > Participa > Gestor
            if 'UsuarioID' in df_acessos.columns and 'UsuarioID' in df_ambientes.columns:
                prioridade = {'Obrigatório': 1, 'Participa': 2, 'Gestor': 3}
                df_perfis = df_ambientes[['UsuarioID', 'PerfilNaTrilha']].dropna().copy()
                df_perfis['prioridade'] = df_perfis['PerfilNaTrilha'].map(prioridade).fillna(99)
                df_perfis = df_perfis.sort_values('prioridade').drop_duplicates('UsuarioID', keep='first')
                df_perfis = df_perfis[['UsuarioID', 'PerfilNaTrilha']]
                df_acessos = df_acessos.drop(columns=['PerfilNaTrilha'], errors='ignore')
                df_acessos = df_acessos.merge(df_perfis, on='UsuarioID', how='left')
            # Aplicar filtro de perfil diretamente em df_acessos
            if filtros.get('perfil') and 'PerfilNaTrilha' in df_acessos.columns:
                df_acessos = df_acessos[df_acessos['PerfilNaTrilha'].isin(filtros['perfil'])]
            # Ajuste: usar DataCadastro da aba Acessos, se existir
            if 'DataCadastro' in df_acessos.columns:
                df_acessos['DataCadastro'] = pd.to_datetime(df_acessos['DataCadastro'], format='%d/%m/%Y', errors='coerce').dt.date
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
            if filtros.get('trilha'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeTrilha'].isin(filtros['trilha'])]
            if filtros.get('modulo'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeModulo'].isin(filtros['modulo'])]
            if filtros.get('grupo'):
                df_amb_filtros = df_amb_filtros[df_amb_filtros['TodosGruposUsuario'].isin(filtros['grupo'])]
            # Ajuste: só calcula data_inicio_total se existir DataCadastro na aba Acessos
            data_inicio_total = df_acessos['DataCadastro'].min() if 'DataCadastro' in df_acessos.columns else None
            data_fim_total = df_acessos['DataAcesso'].max() if 'DataAcesso' in df_acessos.columns else None
            # Usar o período recebido nos filtros
            periodo = filtros.get('periodo')
            if periodo and isinstance(periodo, tuple) and len(periodo) == 2 and 'DataCadastro' in df_acessos.columns:
                data_ini, data_fi = periodo
                data_ini = pd.to_datetime(data_ini).date()
                data_fi = pd.to_datetime(data_fi).date()
                df_acessos['DataCadastro'] = pd.to_datetime(df_acessos['DataCadastro'], format='%d/%m/%Y', errors='coerce')
                usuarios_cadastrados = df_acessos[df_acessos['DataCadastro'].dt.date <= data_fi]
            else:
                usuarios_cadastrados = df_acessos
            total_usuarios = usuarios_cadastrados['UsuarioID'].nunique() if 'UsuarioID' in usuarios_cadastrados.columns else 0
            if total_usuarios > 0:
                usuarios_ids = usuarios_cadastrados['UsuarioID'].unique()
                df_acessos_filtros = df_acessos[df_acessos['UsuarioID'].isin(usuarios_ids)]
                # Só filtra por data se data_ini e data_fi existirem
                if (
                    periodo and isinstance(periodo, tuple) and len(periodo) == 2 and
                    ('DataCadastro' in df_acessos.columns)
                ):
                    df_acessos_filtros = df_acessos_filtros[(df_acessos_filtros['DataAcesso'] >= data_ini) & (df_acessos_filtros['DataAcesso'] <= data_fi)]
                usuarios_com_acesso = df_acessos_filtros['UsuarioID'].nunique()
            else:
                usuarios_com_acesso = 0
            percentual = (usuarios_com_acesso / total_usuarios * 100) if total_usuarios > 0 else 0
            # NOVAS FAIXAS DO GAUGE
            if percentual > 60:
                classificacao = "Excelente"
            elif percentual > 20:
                classificacao = "Bom"
            else:
                classificacao = "Regular"
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
                        {'range': [0, 20], 'color': '#FF6F6F'},  # Regular (vermelho)
                        {'range': [20, 60], 'color': '#FFD180'}, # Bom (amarelo)
                        {'range': [60, 100], 'color': '#66E396'} # Excelente (verde)
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
                st.metric("Usuários Cadastrados", total_usuarios)
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
                st.metric("Usuários com acesso", usuarios_com_acesso)
            if fig is not None and hasattr(fig, 'to_plotly_json'):
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Erro ao gerar o gráfico: objeto inválido.")
        else:
            st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == "__main__":
    st.info("Este arquivo deve ser importado e chamado via dashboard.py para funcionar corretamente.")