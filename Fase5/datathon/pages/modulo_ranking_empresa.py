import App
import modelo
import pandas as pd
import streamlit as st
from io import BytesIO

st.title('Ranking de Vagas')
App.gerar_menu_lateral()


RANKING_DADOS_EXTERNOS = "Ranking com Dados Externos"
RANKING_DADOS_INTERNOS = "Ranking com Dados Internos"

tab_sistema, tab_documentacao = st.tabs(["Sistema", "Documentação"])

class DataFrameValidationError(ValueError):
    """Exceção personalizada para erros de validação de DataFrame."""
    pass


def baixar_excel():
    # Carrega o arquivo Excel local (substitua 'seu_arquivo.xlsx' pelo caminho real)
    try:
        df = pd.read_excel('template/template_candidatos.xlsx')
    except FileNotFoundError:
        st.error("Arquivo Excel não encontrado.")
        return

    # Converte o DataFrame para bytes no formato Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        #df.to_excel(writer, sheet_name='candidatos', index=False)
        worksheet = writer.book.add_worksheet('candidatos')
        #texto a esquerda
        #alinhamento a esquerda
        # Formatação do cabeçalho   
         # Formatação para alinhar o texto à esquerda

        header_format = writer.book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter'})

        left_align_format = writer.book.add_format({'align': 'left', 'valign': 'vcenter'})

        # Escreve o cabeçalho com a formatação
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        
        writer.sheets['candidatos'].set_column('B:B', 30, left_align_format)
        writer.sheets['candidatos'].set_column('A:A', 15, left_align_format)  
        writer.sheets['candidatos'].set_column('B:B', 30, left_align_format)  
        writer.sheets['candidatos'].set_column('C:C', 25, left_align_format)
        writer.sheets['candidatos'].set_column('D:D', 150, left_align_format)
        writer.sheets['candidatos'].set_column('E:E', 150, left_align_format)
        filter_range = 'A1:E1'  # Defina o intervalo de filtro (cabeçalho)
        writer.sheets['candidatos'].autofilter(filter_range)  # Adiciona o filtro ao cabeçalho
        
        
        writer.close()
    excel_data = buffer.getvalue()

    # Oferece o botão de download
    st.download_button(
        label="Baixar Arquivo Excel",
        data=excel_data,
        file_name="template_candidatos.xlsx",
        mime="application/vnd.ms-excel"
    )




with tab_sistema:
    st.session_state.metodo_entrada = st.radio(
                "Escolha o tipo de ranking que deseja gerar:",
                (RANKING_DADOS_EXTERNOS, RANKING_DADOS_INTERNOS),
                key='radio_ranking', horizontal=True,
            )
    
    if st.session_state.metodo_entrada == RANKING_DADOS_EXTERNOS:
        st.markdown('''
            ### Ranking com Dados Externos
            Este ranking é gerado com base em dados coletados de fontes externas.
            Ele fornece uma visão abrangente das oportunidades disponíveis no mercado.
        ''')

        ### Excel template para preenchimento
        st.markdown("### Template de Candidatos")
        st.markdown("Baixe o template de candidatos para preencher com os dados necessários.")

        baixar_excel()
        st.markdown("### Carregue sua Planilha de Candidatos")
        
        
        

        ### Codigo que recebe uma planilha do excel para ser usado como dataframe
        uploaded_file = st.file_uploader("Escolha um arquivo Excel", type="xlsx", help="Carregue um arquivo Excel com os dados dos candidatos. O arquivo deve conter uma aba chamada 'candidatos' use o arquivo de exemplo")
        if uploaded_file is not None:
            try:

                
                df = pd.read_excel(uploaded_file)               
                
                st.success("Arquivo carregado com sucesso!")
                st.markdown("### Dados dos Candidatos")

                # Inicializar o estado da paginação
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = 0
                
                items_per_page = 10  # Defina quantos itens por página

                total_items = len(df)  # Total de itens no DataFrame
                if total_items == 0:
                    st.warning("A planilha do excel enviada está vazia. Verifique o arquivo carregado.")
                    st.stop()

                total_pages = (total_items + items_per_page - 1) // items_per_page

                start_idx = st.session_state.current_page * items_per_page
                end_idx = start_idx + items_per_page
                
                # Exibe a fatia do DataFrame para a página atual
                st.dataframe(df.iloc[start_idx:end_idx], hide_index=True)

                # Controles de Paginação
                col1, col2, col3 = st.columns([1,2,1])

                with col1:
                    if st.button("⬅️ Anterior", disabled=(st.session_state.current_page == 0)):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col2:
                    st.write(f"Página {st.session_state.current_page + 1} de {total_pages}")

                with col3:
                    if st.button("Próxima ➡️", disabled=(st.session_state.current_page >= total_pages - 1)):
                        st.session_state.current_page += 1
                        st.rerun()
                
                # Aqui você pode adicionar mais lógica para processar o DataFrame conforme necessário

            except Exception as e:
                if isinstance(e, ValueError):
                    st.error("Erro ao carregar dados do Excel: O arquivo não contém a aba chamada 'candidatos ou descricao_vaga'.")
            except DataFrameValidationError as e:
                st.error(f"Erro de validação: {e}")


            ## descricao da vaga
            st.markdown("### Descrição da Vaga")
            st.markdown("Aqui você pode adicionar a descrição da vaga")
            st.session_state.descricao_vaga = st.text_area(" ", max_chars=3000, label_visibility="collapsed",
                                                                                height=200,
                                                                                placeholder="Digite a descrição da vaga aqui...")
            
            #Percentual vaga
            quantidade_candidato = len(df)
            if quantidade_candidato > 50:
                percentual_vaga = 0.20
            if quantidade_candidato > 100:
                percentual_vaga = 0.10
            if quantidade_candidato > 200:
                percentual_vaga = 0.05
            if quantidade_candidato > 500:
                percentual_vaga = 0.02           
            

            
            if st.session_state.descricao_vaga:
                
                numero_candidatos = st.slider(
                    "Selecione o número de candidatos que deseja retornar:",
                    min_value=1,
                    max_value=quantidade_candidato, 
                    value=int(quantidade_candidato*percentual_vaga),  # Valor padrão
                    step=1,
                )
                if st.button("Criar Ranking", type="primary", key="criar_ranking"):
                    df_resultado_ranking = modelo.gerar_ranking_vagas(
                        descricao_vaga=st.session_state.descricao_vaga,
                        df=df,
                        numero_candidatos=numero_candidatos,  # Defina o número de vagas que deseja retornar
                        tipo_ranking=st.session_state.metodo_entrada
                    )
                    st.success("Ranking gerado com sucesso!")
                    st.markdown("### Ranking Gerado")
                    st.dataframe(df_resultado_ranking, hide_index=True)
               

                
                    
                


    if st.session_state.metodo_entrada == RANKING_DADOS_INTERNOS:
        st.markdown('''
            ### Ranking com Dados Internos
            Este ranking é gerado com base em dados coletados internamente.
            Ele fornece uma visão específica das oportunidades disponíveis na sua organização.
        ''')
        # Adicione aqui a lógica para dados internos, se houver.
    

with tab_documentacao:
    st.markdown('''
        ### Documentação do Módulo de Ranking de Vagas

        Este módulo foi projetado para auxiliar na priorização de candidatos para vagas específicas,
        utilizando diferentes fontes de dados. Ele permite gerar um ranking de candidatos
        com base em uma descrição de vaga e um conjunto de dados de candidatos.

        #### Funcionalidades Principais:

        *   **Ranking com Dados Externos:**
            *   Permite o upload de uma planilha Excel (.xlsx) contendo os dados dos candidatos.
            *   Exibe os dados dos candidatos carregados de forma paginada para fácil visualização.
            *   Requer a inserção de uma descrição detalhada da vaga para a qual o ranking será gerado.
            *   Permite ao usuário definir o número de candidatos que devem ser incluídos no ranking final.
            *   Gera um ranking dos candidatos mais adequados com base na descrição da vaga (atualmente, o modelo de ranking é simulado).
            *   Apresenta o resultado do ranking em uma tabela.
        *   **Ranking com Dados Internos:**
            *   Previsto para utilizar dados de candidatos provenientes de sistemas internos da organização.
            *   (Funcionalidade a ser implementada ou detalhada conforme o sistema interno).

        #### Como Usar o Módulo:

        1.  **Acesse a Aba "Sistema":**
            *   No menu lateral, navegue até "📊 Ranking Vagas".
            *   A interface principal do módulo será exibida com duas abas: "Sistema" e "Documentação". Certifique-se de estar na aba "Sistema" para interagir com as funcionalidades.

        2.  **Selecione o Tipo de Ranking (na aba "Sistema"):**
            *   Você verá duas opções de rádio: "Ranking com Dados Externos" e "Ranking com Dados Internos".
            *   Escolha a opção desejada.

        3.  **Para "Ranking com Dados Externos":**
            *   **Upload do Arquivo Excel:**
                *   Clique no botão "Escolha um arquivo Excel".
                *   Selecione o arquivo `.xlsx` do seu computador que contém os dados dos candidatos.
                *   **Observação:** O arquivo deve estar formatado corretamente. O sistema espera encontrar colunas relevantes para os candidatos (ex: `id_candidato`, `nome_candidato`, `senioridade`, etc., conforme utilizado pelo modelo de ranking).
            *   **Visualização dos Dados:**
                *   Após o upload bem-sucedido, uma prévia dos dados dos candidatos ("Dados dos Candidatos") será exibida em uma tabela.
                *   Se houver muitos candidatos, a tabela será paginada (10 itens por página). Use os botões "⬅️ Anterior" e "Próxima ➡️" para navegar pelas páginas.
            *   **Descrição da Vaga:**
                *   No campo de texto abaixo de "Descrição da Vaga", insira uma descrição detalhada da vaga. Quanto mais informações você fornecer (habilidades, experiência, responsabilidades), mais preciso poderá ser o ranking (embora o modelo atual seja uma simulação).
            *   **Número de Candidatos para o Ranking:**
                *   Utilize o controle deslizante ("Selecione o número de candidatos que deseja retornar:") para definir quantos dos melhores candidatos você deseja ver no ranking final. O valor padrão é calculado automaticamente como um percentual do total de candidatos carregados (20% para >50, 10% para >100, 5% para >200, 2% para >500 candidatos).
            *   **Gerar Ranking:**
                *   Após preencher a descrição da vaga e selecionar o número de candidatos, clique no botão "Criar Ranking".
            *   **Visualizar Resultado:**
                *   O sistema processará os dados e exibirá o "Ranking Gerado" em uma nova tabela, mostrando os candidatos selecionados e suas respectivas pontuações/ranking.

        4.  **Para "Ranking com Dados Internos":**
            *   Esta seção descreverá como utilizar o ranking com dados internos da organização.
            *   (Atualmente, esta funcionalidade pode estar em desenvolvimento ou aguardando integração. Siga as instruções específicas que aparecerão nesta seção quando disponível).

        #### Observações Adicionais:
        *   O modelo de ranking atual no modo "Dados Externos" é uma simulação para fins de demonstração (gera um ranking e score sequenciais). Em uma implementação real, algoritmos de processamento de linguagem natural (NLP) ou outros métodos de correspondência seriam usados para comparar a descrição da vaga com os perfis dos candidatos.
        *   Certifique-se de que o arquivo Excel carregado esteja no formato correto e contenha os dados esperados para evitar erros. Se o arquivo estiver vazio ou mal formatado, mensagens de erro ou aviso serão exibidas.
    ''')

    st.markdown("---")