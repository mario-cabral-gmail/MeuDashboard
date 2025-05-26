import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def app(arquivo, filtros):
    st.title("Horas treinadas")
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
            # Verificar existência da coluna TempoAcessoModuloEmHoras
            if 'TempoAcessoModuloEmHoras' not in df_filtros.columns:
                st.warning("Coluna 'TempoAcessoModuloEmHoras' não encontrada na aba 'UsuariosAmbientes'.")
                return
            df_filtros = df_filtros.dropna(subset=['TempoAcessoModuloEmHoras'])
            # Converter TempoAcessoModuloEmHoras para timedelta
            try:
                df_filtros['HorasTreinadas'] = pd.to_timedelta(df_filtros['TempoAcessoModuloEmHoras'])
            except Exception:
                st.warning("Não foi possível converter 'TempoAcessoModuloEmHoras' para duração.")
                return
            # Conversão das datas dos módulos (SEM hora)
            df_filtros['DataInicioModulo'] = pd.to_datetime(df_filtros['DataInicioModulo'], format='%d/%m/%Y', errors='coerce')
            df_filtros['DataConclusaoModulo'] = pd.to_datetime(df_filtros['DataConclusaoModulo'], format='%d/%m/%Y', errors='coerce')
            # Filtro de período
            if filtros.get('periodo') and (isinstance(filtros['periodo'], list) or isinstance(filtros['periodo'], tuple)) and len(filtros['periodo']) == 2:
                data_inicio_filtro = pd.to_datetime(filtros['periodo'][0], format='%d/%m/%Y')
                data_fim_filtro = pd.to_datetime(filtros['periodo'][1], format='%d/%m/%Y')
                mask_inicio = (df_filtros['DataInicioModulo'].notna()) & (df_filtros['DataInicioModulo'] >= data_inicio_filtro) & (df_filtros['DataInicioModulo'] <= data_fim_filtro)
                mask_conclusao = (df_filtros['DataConclusaoModulo'].notna()) & (df_filtros['DataConclusaoModulo'] >= data_inicio_filtro) & (df_filtros['DataConclusaoModulo'] <= data_fim_filtro)
                df_filtros = df_filtros[mask_inicio | mask_conclusao]
            if df_filtros.empty:
                st.info("Nenhum dado encontrado após aplicação dos filtros.")
                return
            total_horas = df_filtros['HorasTreinadas'].sum()
            media_horas = df_filtros.groupby('UsuarioID')['HorasTreinadas'].sum().mean()
            usuario_mais_horas = df_filtros.groupby(['UsuarioID', 'PerfilNaTrilha'])['HorasTreinadas'].sum().reset_index()
            usuario_mais_horas = usuario_mais_horas.sort_values('HorasTreinadas', ascending=False).head(1)
            ambiente_mais_horas = df_filtros.groupby('NomeAmbiente')['HorasTreinadas'].sum().reset_index()
            ambiente_mais_horas = ambiente_mais_horas.sort_values('HorasTreinadas', ascending=False).head(1)
            # Função para formatar timedelta para HH:MM
            def format_horas(td):
                if pd.isnull(td) or td is None:
                    return '00:00'
                td = pd.to_timedelta(td)  # Garante que é pd.Timedelta
                total_seconds = int(td.total_seconds())
                horas = total_seconds // 3600
                minutos = (total_seconds % 3600) // 60
                return f"{horas:02d}:{minutos:02d}"

            # Buscar coluna de login
            col_login = None
            for col in ['Login', 'login', 'Email', 'E-mail', 'email']:
                if col in df_filtros.columns:
                    col_login = col
                    break

            total_horas_str = format_horas(total_horas)
            media_horas_str = format_horas(media_horas)
            usuario_mais_horas_valor = format_horas(usuario_mais_horas['HorasTreinadas'].values[0]) if not usuario_mais_horas.empty else '00:00'
            ambiente_mais_horas_valor = format_horas(ambiente_mais_horas['HorasTreinadas'].values[0]) if not ambiente_mais_horas.empty else '00:00'

            # Centralizar valor e texto juntos, com fonte maior
            st.markdown(f"""
            <div style='text-align:center; margin-bottom: 30px;'>
                <span style='font-size:3.5em; color:#0077A3; font-weight: bold'>{total_horas_str}</span><br>
                <span style='color:#0077A3; font-size:1.5em; font-weight: 500'>Total de horas</span>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div style='text-align:center; margin-bottom: 10px;'><span style='font-size:2.5em; color:#444; font-weight: bold'>{media_horas_str}</span><br><span style='color:#888; font-size:1.1em;'>Média de horas por pessoa</span></div>", unsafe_allow_html=True)
            with col2:
                usuario_login = '-'
                usuario_id_val = usuario_mais_horas['UsuarioID'].values[0] if not usuario_mais_horas.empty else None
                if usuario_id_val is not None and 'LoginUsuario' in df_filtros.columns:
                    login_row = df_filtros[(df_filtros['UsuarioID'] == usuario_id_val) & (df_filtros['LoginUsuario'].notnull())]
                    if not login_row.empty:
                        usuario_login = str(login_row.iloc[0]['LoginUsuario'])
                if usuario_login == '-' and 'Acessos' in abas and usuario_id_val is not None:
                    df_acessos = abas['Acessos']
                    if 'LoginUsuario' in df_acessos.columns:
                        login_row = df_acessos[(df_acessos['UsuarioID'] == usuario_id_val) & (df_acessos['LoginUsuario'].notnull())]
                        if not login_row.empty:
                            usuario_login = str(login_row.iloc[0]['LoginUsuario'])
                st.markdown(f"<div style='text-align:center; margin-bottom: 10px;'><span style='font-size:2.5em; color:#444; font-weight: bold'>{usuario_mais_horas_valor}</span><br><span style='color:#888; font-size:1.1em;'>Usuário c/ mais horas</span><br><b style='font-size:1.1em'>{usuario_login}</b></div>", unsafe_allow_html=True)
            with col3:
                ambiente_nome = ambiente_mais_horas['NomeAmbiente'].values[0] if not ambiente_mais_horas.empty else '-'
                st.markdown(f"<div style='text-align:center; margin-bottom: 10px;'><span style='font-size:2.5em; color:#444; font-weight: bold'>{ambiente_mais_horas_valor}</span><br><span style='color:#888; font-size:1.1em;'>Ambiente com mais horas</span><br><b style='font-size:1.1em'>{ambiente_nome}</b></div>", unsafe_allow_html=True)
            with st.expander("Detalhar dados filtrados"):
                st.dataframe(df_filtros)
        else:
            st.error("Sua planilha precisa ter a aba 'UsuariosAmbientes'.")
    else:
        st.info("Por favor, faça upload da planilha Excel original.")

if __name__ == '__main__':
    app(arquivo, filtros) 