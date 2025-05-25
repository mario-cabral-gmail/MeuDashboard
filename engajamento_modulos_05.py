import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def app(arquivo, filtros):
    st.title("Engajamento de Módulos")
    if arquivo:
        abas = pd.read_excel(arquivo, sheet_name=None)
        if 'UsuariosAmbientes' in abas:
            df_ambientes = abas['UsuariosAmbientes']
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