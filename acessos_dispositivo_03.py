import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Ícones SVG para Desktop, Mobile e App
ICONS = {
    'Desktop': "<svg width='32' height='32' fill='#4285F4' viewBox='0 0 24 24'><path d='M4 5v11h16V5H4zm16-2c1.1 0 2 .9 2 2v11c0 1.1-.9 2-2 2h-7v2h3v2H8v-2h3v-2H4c-1.1 0-2-.9-2-2V5c0-1.1.9-2 2-2h16z'/></svg>",
    'Mobile': "<svg width='32' height='32' fill='#4285F4' viewBox='0 0 24 24'><path d='M17 1H7C5.9 1 5 1.9 5 3v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-2-2-2zm0 18H7V5h10v14zm-5 3c-.55 0-1-.45-1-1h2c0 .55-.45 1-1 1z'/></svg>",
    'App': "<svg width='32' height='32' fill='#4285F4' viewBox='0 0 24 24'><circle cx='12' cy='12' r='10'/><rect x='9' y='7' width='6' height='10' fill='#fff'/></svg>"
}


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
        Acessos por Dispositivo
        <span class="tooltip">
            <b style="color:#888; font-size:1.1em; cursor:help;">&#9432;</b>
            <span class="tooltiptext">
                Exibe o percentual de acessos feitos por desktop, mobile ou app.<br>
                🕒 Somente acessos com DataAcesso dentro do período selecionado são incluídos no cálculo.
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
            # Merge para trazer PerfilNaTrilha prioritário para df
            if 'UsuarioID' in df_acessos.columns and 'UsuarioID' in df_ambientes.columns:
                prioridade = {'Obrigatório': 1, 'Participa': 2, 'Gestor': 3}
                df_perfis = df_ambientes[['UsuarioID', 'PerfilNaTrilha']].dropna().copy()
                df_perfis['prioridade'] = df_perfis['PerfilNaTrilha'].map(prioridade).fillna(99)
                df_perfis = df_perfis.sort_values('prioridade').drop_duplicates('UsuarioID', keep='first')
                df_perfis = df_perfis[['UsuarioID', 'PerfilNaTrilha']]
                df = df_acessos.drop(columns=['PerfilNaTrilha'], errors='ignore')
                df = df.merge(df_perfis, on='UsuarioID', how='left')
            # Aplicar filtros na aba UsuariosAmbientes
            df_amb_filtros = df_ambientes.copy()
            if filtros.get('ambiente') and 'NomeAmbiente' in df_amb_filtros.columns:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeAmbiente'].isin(filtros['ambiente'])]
            if filtros.get('perfil') and 'PerfilNaTrilha' in df_amb_filtros.columns:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['PerfilNaTrilha'].isin(filtros['perfil'])]
            if filtros.get('trilha') and 'NomeTrilha' in df_amb_filtros.columns:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeTrilha'].isin(filtros['trilha'])]
            if filtros.get('modulo') and 'NomeModulo' in df_amb_filtros.columns:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['NomeModulo'].isin(filtros['modulo'])]
            if filtros.get('grupo') and 'TodosGruposUsuario' in df_amb_filtros.columns:
                df_amb_filtros = df_amb_filtros[df_amb_filtros['TodosGruposUsuario'].isin(filtros['grupo'])]
            usuarios_filtrados = df_amb_filtros['UsuarioID'].unique()
            # Filtrar a aba Acessos pelos usuarios filtrados
            df = df_acessos[df_acessos['UsuarioID'].isin(usuarios_filtrados)].copy()
            # Filtro de período
            if filtros.get('periodo') and 'DataAcesso' in df.columns:
                periodo = filtros['periodo']
                if isinstance(periodo, tuple) and len(periodo) == 2:
                    data_ini, data_fi = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
                    df['DataAcesso'] = pd.to_datetime(df['DataAcesso'], dayfirst=True, errors='coerce')
                    df = df[(df['DataAcesso'] >= data_ini) & (df['DataAcesso'] <= data_fi)]
            if 'Dispositivo' not in df.columns:
                st.warning("Coluna 'Dispositivo' não encontrada na aba 'Acessos'.")
                return
            # Padronizar valores de Dispositivo
            dispositivo_map = {
                'Computador': 'Desktop',
                'Dispositivo Móvel': 'Mobile',
                'Aplicativo': 'App',
                'App': 'App',
                'Desktop': 'Desktop',
                'Mobile': 'Mobile'
            }
            df['DispositivoPadrao'] = df['Dispositivo'].map(dispositivo_map).fillna('Outro')
            total = df.shape[0]
            if total == 0:
                st.info("Nenhum dado encontrado após aplicação dos filtros.")
                return
            dispositivos = df['DispositivoPadrao'].value_counts().to_dict()
            percentuais = {k: (v / total * 100) if total > 0 else 0 for k, v in dispositivos.items()}
            # Garantir que todos os tipos apareçam
            tipos = ['Desktop', 'Mobile', 'App']
            valores = [dispositivos.get(t, 0) for t in tipos]
            percentuais_lista = [percentuais.get(t, 0) for t in tipos]
            # Gráfico donut
            fig = go.Figure(data=[
                go.Pie(
                    labels=tipos,
                    values=valores,
                    hole=0.6,
                    marker=dict(colors=['#4285F4', '#90CAF9', '#B2DFDB']),
                    textinfo='none',
                )
            ])
            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=300
            )
            col_graf, col_info = st.columns([2,3])
            with col_graf:
                if fig is not None and hasattr(fig, 'to_plotly_json'):
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Erro ao gerar o gráfico: objeto inválido.")
            with col_info:
                blocos = []
                for i, tipo in enumerate(tipos):
                    icone = ICONS[tipo]
                    valor = percentuais_lista[i]
                    blocos.append(f"""
                        <div style='display:inline-block; width:110px; text-align:center; margin-right:10px'>
                            {icone}<br>
                            <span style='font-size:1.1em; color:#222'><b>{tipo}</b></span><br>
                            <span style='font-size:2em; color:#222'><b>{valor:.1f}%</b></span>
                        </div>
                    """)
                st.markdown(''.join(blocos), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("detalhar"):
                st.dataframe(df[['UsuarioID', 'DataAcesso', 'Dispositivo', 'DispositivoPadrao']])
                st.markdown("**Valores únicos e contagem em 'DispositivoPadrao':**")
                st.dataframe(df['DispositivoPadrao'].value_counts())
        else:
            st.error("Sua planilha precisa ter as abas 'Acessos' e 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == '__main__':
    app(arquivo, filtros) 