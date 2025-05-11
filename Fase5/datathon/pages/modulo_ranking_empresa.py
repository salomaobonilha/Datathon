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

                # Validação das colunas do DataFrame
                colunas_obrigatorias = ['id_candidato', 'nome_candidato', 'senioridade', 'curriculo']
                colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]

                if colunas_faltantes:
                    raise DataFrameValidationError(
                        f"O arquivo Excel carregado não contém as seguintes colunas obrigatórias: {', '.join(colunas_faltantes)}. "
                        "Por favor, verifique o arquivo ou baixe o template para o formato correto."
                    )
                if df.empty:
                    st.warning("A planilha do Excel enviada está vazia. Verifique o arquivo carregado.")
                    st.stop()

              
              

              

                if df[colunas_obrigatorias].isnull().any().any():
                    st.warning("Atenção: Foram encontrados dados nulos na planilha. "
                               "Por favor, verifique e preencha todos os campos obrigatórios.")
                    # Você pode decidir se quer parar o processamento aqui com st.stop() ou apenas avisar.

                    df_campos_faltantes = df[colunas_obrigatorias].isna().sum().reset_index()

                    df_campos_faltantes.columns = ['Campo', 'Quantidade de Nulos']

                    st.dataframe(df_campos_faltantes, hide_index=True, use_container_width=True)
                    st.stop() # Descomente se a presença de nulos deve impedir o prosseguimento.
                st.success("Arquivo carregado com sucesso!")
                st.markdown("### Dados dos Candidatos")

                # Inicializar o estado da paginação
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = 0
                
                items_per_page = 10  # Defina quantos itens por página

                total_items = len(df)  # Total de itens no DataFrame

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
                    # Esta mensagem pode precisar de ajuste dependendo de como você quer tratar outros ValueErrors
                    st.error(f"Erro ao processar o arquivo Excel: {e}")
                elif isinstance(e, DataFrameValidationError):
                    st.error(f"Erro de validação: {e}")
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
            Ele fornece uma visão dos candidatos já existente para vaga disponivel.
        ''')
        # Adicione aqui a lógica para dados internos, se houver.

        st.markdown("### Descrição da Vaga")
        st.markdown("Aqui você pode adicionar a descrição da vaga")
        st.session_state.descricao_vaga_dados_internos = st.text_area(" ", max_chars=3000, label_visibility="collapsed",
                                                                            height=200,
                                                                            placeholder="Digite a descrição da vaga aqui...")
        if st.session_state.descricao_vaga_dados_internos:
                
                numero_candidatos = st.slider(
                    "Selecione o número de candidatos que deseja retornar:",
                    min_value=1,
                    max_value=100, 
                    value=10,  # Valor padrão
                    step=1,
                )
                if st.button("Criar Ranking", type="primary", key="criar_ranking"):
                    df_resultado_ranking = modelo.gerar_ranking_vagas(
                        descricao_vaga=st.session_state.descricao_vaga_dados_internos,                        
                        numero_candidatos=numero_candidatos,  # Defina o número de vagas que deseja retornar
                        
                    )
                    st.success("Ranking gerado com sucesso!")
                    st.markdown("### Ranking Gerado")
                    st.dataframe(df_resultado_ranking, hide_index=True)
    

with tab_documentacao:
    st.markdown('''
        ### Documentação do Módulo de Ranking de Vagas

        Este módulo foi projetado para auxiliar na priorização de candidatos para vagas específicas,
        utilizando diferentes fontes de dados. Ele permite gerar um ranking de candidatos
        com base em uma descrição de vaga e um conjunto de dados de candidatos.

        #### Funcionalidades Principais (Aba "Sistema"):

        *   **Ranking com Dados Externos:**
            *   **Template de Candidatos:** Oferece um botão para baixar um template Excel (`template_candidatos.xlsx`) que serve como modelo para a inserção dos dados dos candidatos. O template já vem com formatação e filtros no cabeçalho para facilitar o uso.
            *   Permite o upload de uma planilha Excel (.xlsx) contendo os dados dos candidatos.
            *   **Validação de Dados:** Ao carregar o arquivo, o sistema verifica:
                *   Se as colunas obrigatórias (`id_candidato`, `nome_candidato`, `senioridade`, `curriculo`) estão presentes.
                *   Se a planilha não está vazia.
                *   Se há dados nulos nas colunas obrigatórias, exibindo um resumo dos campos faltantes.
            *   Exibe os dados dos candidatos carregados de forma paginada para fácil visualização.
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
            *   **Baixar Template (Opcional, mas Recomendado):**
                *   Clique em "Baixar Arquivo Excel" na seção "Template de Candidatos" para obter o modelo formatado.
                *   Preencha este template com os dados dos seus candidatos.
            *   **Upload do Arquivo Excel:**
                *   Na seção "Carregue sua Planilha de Candidatos", clique no botão "Escolha um arquivo Excel".
                *   Selecione o arquivo `.xlsx` do seu computador que contém os dados dos candidatos.
                *   **Observação:** O arquivo deve conter uma aba chamada `candidatos` e as colunas obrigatórias: `id_candidato`, `nome_candidato`, `senioridade`, `curriculo`. O sistema realizará validações e informará sobre quaisquer problemas.
            *   **Visualização e Validação dos Dados:**
                *   Se o arquivo for carregado com sucesso e passar nas validações iniciais, uma mensagem de sucesso será exibida.
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
            *   Esta opção utiliza um conjunto de dados de candidatos internos (atualmente simulados com dados fixos) para gerar o ranking.
            *   **Descrição da Vaga:**
                *   No campo de texto abaixo de "Descrição da Vaga", insira uma descrição detalhada da vaga.
            *   **Número de Candidatos para o Ranking:**
                *   Utilize o controle deslizante ("Selecione o número de candidatos que deseja retornar:") para definir quantos dos melhores candidatos você deseja ver no ranking final. O valor padrão é 10, com um máximo de 100 (baseado nos dados simulados disponíveis).
            *   **Gerar Ranking:**
                *   Após preencher a descrição da vaga e selecionar o número de candidatos, clique no botão "Criar Ranking".
            *   **Visualizar Resultado:**
                *   O sistema processará os dados e exibirá o "Ranking Gerado" em uma nova tabela, mostrando os candidatos selecionados e suas respectivas pontuações/ranking.

        #### Observações Adicionais:        
        *   Certifique-se de que o arquivo Excel carregado esteja no formato correto e contenha os dados esperados para evitar erros. O sistema tentará validar a estrutura do arquivo e a presença de dados nulos.
    ''')

    st.markdown("---")