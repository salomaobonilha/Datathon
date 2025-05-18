import pandas as pd
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import re
import json
from modelo import SistemaRecomendacao
import apoio_tech as inteligencia_st
st.title('Ranking de Vagas')



def extrair_json_colunas(df, colunas):
    """
    Extrai colunas específicas de um DataFrame e converte para JSON.
    
    Parâmetros:
    df (DataFrame): O DataFrame de entrada.
    colunas (list): Lista de nomes de colunas a serem extraídas.
    
    Retorna:
    str: String Dataframe atualizado com as colunas extraídas.
    """
    try:
        
        for coluna in colunas: # Itera sobre cada coluna que contém JSON
            # Normaliza a estrutura JSON da coluna especificada para um novo DataFrame.
            # Isso transforma objetos JSON aninhados em colunas planas.
            df_normalizado = pd.json_normalize(df[coluna])
            # Adiciona um prefixo ao nome das novas colunas para evitar conflitos
            # com colunas existentes e para indicar sua origem.
            df_normalizado = df_normalizado.add_prefix(f'{coluna}_') 
            df = df.drop(coluna, axis=1)
            df = pd.concat([df, df_normalizado], axis=1)            
        return df
    except KeyError as e:
        # Captura erro se uma coluna especificada não existir no DataFrame.
        print(f"Erro: Coluna não encontrada - {e}. Verifique os nomes das colunas.")
        KeyError(e)

@st.cache_data # Cacheia o resultado desta função para otimizar o carregamento.
def carregar_vagas():
    print("Carregando vagas...")
    with open('dataset/vagas.json', 'r', encoding='utf-8') as f: # Abre o arquivo JSON de vagas.
        vagas = json.load(f)
    
    dados_vagas = []
    for id_vaga, info in vagas.items():
        dados_vagas.append({
            'id_vaga': id_vaga,
            'titulo': info.get('informacoes_basicas', {}).get('titulo_vaga', 'Sem título'),
            # Concatena atividades e competências para formar uma descrição completa da vaga.
            'descricao': f"{info.get('perfil_vaga', {}).get('principais_atividades', '')} {info.get('perfil_vaga', {}).get('competencia_tecnicas_e_comportamentais', '')}" 
        })
    return pd.DataFrame(dados_vagas)

def main():
    st.subheader('Sistema de Recomendação de Candidatos')
    
    RANKING_DADOS_EXTERNOS = "Dados Externos (Upload Excel)"
    RANKING_DADOS_INTERNOS = "Dados Internos (Sistema)"
    
    tab_sistema, tab_documentacao = st.tabs(["Sistema", "Documentação"]) # Cria abas na interface.

    uploaded_file = None
    
    with tab_sistema:
        fonte_dados = st.radio(
            "Selecione a fonte de dados dos candidatos:",
            (RANKING_DADOS_EXTERNOS, RANKING_DADOS_INTERNOS),
            horizontal=True
        )
        
        df_candidatos = None
        col_download, col_upload  = st.columns(2,border=True)
        # Lógica para carregar dados de candidatos externos via upload de Excel.
        if fonte_dados == RANKING_DADOS_EXTERNOS:
            col_download, col_upload  = st.columns(2,border=True)
            with col_download:
                st.markdown("## Carregar Candidatos via Excel")
                
                # Define a estrutura do DataFrame para o template Excel.
                template_df = pd.DataFrame(columns=[
                    'id_candidato', 
                    'nome_candidato', 
                    'senioridade', 
                    'curriculo',
                    'informacoes_adicionais'
                ])
                    
                    
                buffer = BytesIO() # Cria um buffer em memória para o arquivo Excel.
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:                    
                    worksheet = writer.book.add_worksheet('candidatos')
                    # Formatação para o cabeçalho e células.
                    header_format = writer.book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter'})
                    left_align_format = writer.book.add_format({'align': 'left', 'valign': 'vcenter'})

                    # Escreve o cabeçalho no worksheet.
                    for col_num, value in enumerate(template_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Define a largura das colunas para melhor visualização.
                    writer.sheets['candidatos'].set_column('B:B', 30, left_align_format)
                    writer.sheets['candidatos'].set_column('A:A', 15, left_align_format)  
                    writer.sheets['candidatos'].set_column('B:B', 30, left_align_format)  
                    writer.sheets['candidatos'].set_column('C:C', 25, left_align_format)
                    writer.sheets['candidatos'].set_column('D:D', 150, left_align_format) # Coluna de currículo com maior largura.
                    writer.sheets['candidatos'].set_column('E:E', 150, left_align_format)
                    filter_range = 'A1:E1'
                    writer.sheets['candidatos'].autofilter(filter_range)
                
                st.download_button(
                    label="📥 Baixar Template",
                    data=buffer.getvalue(),
                    file_name="template_candidatos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_upload:
                
                uploaded_file = st.file_uploader("Carregar planilha de candidatos", type="xlsx") # Widget para upload de arquivo.

        if uploaded_file is not None:
            try:

                df_candidatos = pd.read_excel(uploaded_file)
                # Define as colunas obrigatórias que o arquivo Excel deve conter.
                colunas_obrigatorias = ['id_candidato', 'nome_candidato', 'senioridade', 'curriculo']
                colunas_faltantes = [col for col in colunas_obrigatorias if col not in df_candidatos.columns]

                # Validação da presença das colunas obrigatórias.
                if colunas_faltantes:
                    raise ValueError(
                        f"O arquivo Excel carregado não contém as seguintes colunas obrigatórias: {', '.join(colunas_faltantes)}. "
                        "Por favor, verifique o arquivo ou baixe o template para o formato correto."
                    )
                if df_candidatos.empty:
                    st.warning("A planilha do Excel enviada está vazia. Verifique o arquivo carregado.")
                    st.stop()

                # Validação de dados nulos nas colunas obrigatórias.
                if df_candidatos[colunas_obrigatorias].isnull().any().any():
                    st.warning("Atenção: Foram encontrados dados nulos na planilha. "
                            "Por favor, verifique e preencha todos os campos obrigatórios.")

                    df_campos_faltantes = df_candidatos[colunas_obrigatorias].isna().sum().reset_index()

                    df_campos_faltantes.columns = ['Campo', 'Quantidade de Nulos']

                    st.dataframe(df_campos_faltantes, hide_index=True, use_container_width=True)
                    st.stop() 
                st.success("Arquivo carregado com sucesso!")
                st.toast(f"{len(df_candidatos)} candidatos carregados", icon="👥")
                st.markdown("### Dados dos Candidatos")
                # Inicializa o estado da paginação se não existir.
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = 0
                
                items_per_page = 10  
                total_items = len(df_candidatos)  
                # Calcula o número total de páginas.
                total_pages = (total_items + items_per_page - 1) // items_per_page
                # Define os índices de início e fim para a fatia do DataFrame da página atual.
                start_idx = st.session_state.current_page * items_per_page
                end_idx = start_idx + items_per_page
                st.dataframe(df_candidatos.iloc[start_idx:end_idx], hide_index=True) # Exibe a página atual dos dados.
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
            except Exception as e:
                if isinstance(e, ValueError):
                    # Trata erros específicos de valor, como colunas faltantes.
                    st.error(f"Erro ao processar o arquivo Excel: {e}")
                       
        elif fonte_dados == RANKING_DADOS_INTERNOS:
                st.subheader("Carregar candidatos do sistema interno")
                try:
                    @st.cache_data # Cacheia os dados internos para evitar recarregamentos.
                    def carregar_dados_internos():                        
                       
                        # Lista de colunas consideradas importantes para formar o campo 'curriculo' consolidado.
                        colunas_importantes = ["cv_pt", "cv_en", "informacoes_profissionais_titulo_profissional", "informacoes_profissionais_area_atuacao", "informacoes_profissionais_conhecimentos_tecnicos", "informacoes_profissionais_certificacoes", "informacoes_profissionais_outras_certificacoes", "informacoes_profissionais_nivel_profissional", "informacoes_profissionais_qualificacoes", "informacoes_profissionais_experiencias", "formacao_e_idiomas_nivel_academico", "formacao_e_idiomas_nivel_ingles", "formacao_e_idiomas_nivel_espanhol", "formacao_e_idiomas_outro_idioma", "formacao_e_idiomas_cursos", "formacao_e_idiomas_outro_curso"]
                        df_applicants = pd.read_json("dataset/applicants.json", encoding="utf-8")
                        df_applicants = df_applicants.T # Transpõe o DataFrame (IDs de candidatos como linhas).
                        # Seleciona colunas que contêm JSON e precisam ser normalizadas, excluindo CVs.
                        colunas_applicants = df_applicants.columns.drop(['cv_pt','cv_en'])                        
                        # Normaliza as colunas JSON.
                        df_applicants = extrair_json_colunas(df_applicants, list(colunas_applicants))                        
                        df_applicants.reset_index(names="id_candidato", inplace=True)
                        # Cria uma coluna 'curriculo' unindo o conteúdo das 'colunas_importantes'.
                        # Valores nulos são preenchidos com string vazia antes da agregação.
                        df_applicants['curriculo'] = df_applicants[colunas_importantes].fillna('').agg(' '.join, axis=1)
                        df_applicants.rename(columns={'infos_basicas_nome':'nome_candidato'}, inplace=True)

                        # Seleciona as colunas finais e remove linhas com valores nulos em colunas essenciais.
                        df_applicants = df_applicants[["id_candidato","nome_candidato", "curriculo"]]
                        df_applicants.dropna(axis=0, how='any', inplace=True)
                        
                        return pd.DataFrame(df_applicants)
                    
                    with st.spinner("Carregando base de candidatos..."):
                        df_candidatos = carregar_dados_internos() # Carrega e processa os dados.
                        st.toast(f"{len(df_candidatos)} candidatos carregados", icon="👥")
                    
                    with st.expander("Visualizar base interna", expanded=False):
                        st.dataframe(df_candidatos.head(10), use_container_width=True)
                
                except Exception as e:
                    st.error(f"Erro ao carregar dados internos: {str(e)}")
                    st.stop()
        # Continua o fluxo apenas se os dados dos candidatos (df_candidatos) foram carregados.
        if df_candidatos is not None:            
            st.divider()
            MODO_DESCRICAO = "Escrever descrição manual"
            MODO_SELECAO_VAGA = "Selecionar vaga existente"
            
            st.markdown("### Quais as informações da vaga?")
            metodo_descricao = st.radio(
                "",
                (MODO_DESCRICAO, MODO_SELECAO_VAGA),
                horizontal=True
            )
            
            descricao_vaga = ""
            # Lógica para selecionar uma vaga existente.
            if metodo_descricao == MODO_SELECAO_VAGA:
                print("Carregando vagas...")
                df_vagas = carregar_vagas() # Carrega as vagas do JSON.
                vagas_lista = [f"{row['id_vaga']} - {row['titulo']}" for _, row in df_vagas.iterrows()]
                
                col1, col2 = st.columns([2, 3])
                with col1:
                    vaga_selecionada = st.selectbox(
                        "Selecione uma vaga:",
                        options=vagas_lista,
                        index=0
                    )
                
                if vaga_selecionada:
                    # Extrai o ID da vaga selecionada para buscar sua descrição.
                    id_vaga = vaga_selecionada.split(' - ')[0]
                    descricao_vaga = df_vagas[df_vagas['id_vaga'] == id_vaga]['descricao'].values[0]
                    
                    with col2:
                        with st.expander("Detalhes da vaga selecionada", expanded=True):
                            st.write(descricao_vaga)
            else: # Lógica para inserir a descrição da vaga manualmente.
                descricao_vaga = st.text_area("Descrição detalhada da vaga:", height=200,
                                             placeholder="Insira os requisitos, responsabilidades e detalhes da vaga...")
            if descricao_vaga:
                st.divider()
                num_candidatos = st.slider("Número de candidatos para recomendar:", 
                                         1, 10, 
                                         min(1, 10))
                
                if st.button("Gerar Recomendações", type="primary"):
                    with st.status("Processando recomendações...", expanded=True) as status:                        
                        instancia = SistemaRecomendacao()

                        # Carrega o modelo de recomendação pré-treinado.
                        instancia._carregar_modelo(
                            df_candidatos=df_candidatos,
                            model_path="modelo_final.keras"
                        )
                        # Utiliza a IA para melhorar/refinar a descrição da vaga fornecida.
                        descricao_vaga_melhorada = inteligencia_st.melhorar_descricao_vaga(descricao_vaga)
                        print(f"descrição nova :{descricao_vaga_melhorada}")
                        st.write("📊 Calculando similaridades...")
                        # Gera as recomendações com base na descrição da vaga melhorada.
                        resultados = instancia.recomendar_candidatos(
                            descricao_vaga=descricao_vaga_melhorada,
                            top_n=num_candidatos
                        )
                        
                        st.write("🧹 Processando resultados...")
                        # Preenche valores nulos em colunas específicas para melhor apresentação.
                        resultados.fillna({
                            'senioridade': 'Não especificado',
                            'nome_candidato': 'Nome não informado',
                            'cv_texto_pt': 'Currículo não disponível' # Assume 'cv_texto_pt' como uma coluna possível.
                        }, inplace=True)
                        
                        status.update(label="✅ Processo completo!", state="complete", expanded=False)
                        st.balloons()
                    
                    st.divider()
                    st.subheader("Resultados da Recomendação")

                    # Ajusta as colunas exibidas se a fonte de dados for interna.
                    if fonte_dados == RANKING_DADOS_INTERNOS:
                        resultados = resultados[['id_candidato', 'nome_candidato', 'curriculo', 'similaridade']]
                    
                    

                    st.dataframe(
                        resultados,                  
                        column_config={
                            # Configura a coluna 'similaridade' para ser exibida como uma barra de progresso.
                            "similaridade": st.column_config.ProgressColumn(
                                format="%.2f",
                                min_value=0,
                                max_value=1,
                                label="Similaridade"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )

    with tab_documentacao:
        st.markdown('''
        ### Guia de Uso: Módulo de Ranking de Vagas

        Este módulo é uma ferramenta interativa projetada para auxiliar no processo de recrutamento,
        permitindo a classificação de candidatos para vagas de emprego específicas.

        #### Funcionalidades Principais (Aba "Sistema"):

        1.  **Seleção da Fonte de Dados dos Candidatos:**
            *   O usuário pode escolher entre:
                *   **"Dados Externos (Upload Excel)"**: Para carregar candidatos a partir de uma planilha.
                *   **"Dados Internos (Sistema)"**: Para utilizar uma base de candidatos já existente no sistema.

        2.  **Para "Dados Externos (Upload Excel)":**
            *   **Download do Template:**
                *   Um botão "📥 Baixar Template" permite o download de um arquivo Excel (`template_candidatos.xlsx`).
                *   Este template possui as colunas: `id_candidato`, `nome_candidato`, `senioridade`, `curriculo`, `informacoes_adicionais`, com formatação e filtros pré-definidos.
            *   **Upload da Planilha:**
                *   O usuário pode carregar sua planilha Excel preenchida através do widget "Carregar planilha de candidatos".
            *   **Validações Automáticas:**
                *   **Colunas Obrigatórias:** Verifica se as colunas `id_candidato`, `nome_candidato`, `senioridade`, `curriculo` estão presentes.
                *   **Planilha Vazia:** Alerta se a planilha carregada não contiver dados.
                *   **Dados Nulos:** Verifica se há valores nulos nas colunas obrigatórias e, em caso positivo, exibe uma tabela com a contagem de nulos por campo, interrompendo o processo.
            *   **Visualização dos Dados:**
                *   Após o carregamento e validação, os dados dos candidatos são exibidos em uma tabela paginada (10 itens por página).

        3.  **Para "Dados Internos (Sistema)":**
            *   **Carregamento Automático:**
                *   Os dados são carregados de uma fonte interna (atualmente, `dataset/applicants.json`).
                *   O sistema processa esses dados: normaliza campos JSON, consolida informações relevantes (de várias colunas como `cv_pt`, `informacoes_profissionais_titulo_profissional`, etc.) na coluna `curriculo`, e renomeia a coluna `infos_basicas_nome` para `nome_candidato`.
            *   **Visualização dos Dados:**
                *   Uma prévia dos primeiros 10 candidatos da base interna pode ser visualizada em uma seção expansível ("Visualizar base interna").

        4.  **Definição das Informações da Vaga (após carregar os candidatos):**
            *   O usuário escolhe como fornecer os detalhes da vaga através da seção "Quais as informações da vaga?":
                *   **"Escrever descrição manual"**: Um campo de texto permite inserir livremente a descrição, requisitos e responsabilidades da vaga.
                *   **"Selecionar vaga existente"**:
                    *   Carrega uma lista de vagas pré-definidas (de `dataset/vagas.json`).
                    *   O usuário seleciona uma vaga da lista (formato: `ID - Título`).
                    *   Os detalhes (descrição completa) da vaga selecionada são exibidos automaticamente em uma seção expansível ("Detalhes da vaga selecionada").

        5.  **Geração das Recomendações:**
            *   **Número de Candidatos:** Um controle deslizante ("Número de candidatos para recomendar:") permite definir quantos dos melhores candidatos devem ser retornados (entre 1 e 10).
            *   **Processamento:** Ao clicar em "Gerar Recomendações":
                *   O sistema utiliza um modelo de recomendação pré-treinado (`modelo_final.keras`).
                *   A descrição da vaga fornecida é otimizada por uma IA para melhorar a precisão da busca.
                *   As similaridades entre os currículos dos candidatos e a descrição da vaga otimizada são calculadas.
            *   **Exibição dos Resultados:**
                *   Os candidatos recomendados são exibidos em uma tabela.
                *   A coluna "Similaridade" mostra o quão aderente o candidato é à vaga, representada por uma barra de progresso (0 a 1).
                *   Se a fonte de dados for "Internos", as colunas exibidas são `id_candidato`, `nome_candidato`, `curriculo`, `similaridade`. Para dados externos, outras colunas originais da planilha podem ser mantidas.

        #### Como Usar o Módulo:

        1.  **Acesse a Aba "Sistema":**
            *   A interface principal do módulo é exibida na aba "Sistema".

        2.  **Selecione a Fonte de Dados dos Candidatos:**
            *   Escolha entre "Dados Externos (Upload Excel)" ou "Dados Internos (Sistema)".

        3.  **Se "Dados Externos (Upload Excel)" for selecionado:**
            *   **Baixe o Template (Recomendado):** Clique em "📥 Baixar Template" e preencha a planilha com os dados dos candidatos. As colunas `id_candidato`, `nome_candidato`, `senioridade` e `curriculo` são obrigatórias e não devem conter valores nulos.
            *   **Carregue sua Planilha:** Utilize o widget "Carregar planilha de candidatos" para fazer o upload do arquivo `.xlsx`.
            *   **Aguarde a Validação:** O sistema verificará o arquivo. Se houver erros (colunas obrigatórias faltantes, planilha vazia, dados nulos nas colunas obrigatórias), mensagens de alerta serão exibidas e o processo pode ser interrompido.
            *   **Visualize os Dados:** Se o carregamento for bem-sucedido, os dados dos candidatos aparecerão em uma tabela paginada. Use os botões "⬅️ Anterior" e "Próxima ➡️" para navegar.

        4.  **Se "Dados Internos (Sistema)" for selecionado:**
            *   Os dados dos candidatos serão carregados automaticamente da base interna.
            *   Você pode expandir a seção "Visualizar base interna" para ver uma amostra dos dados carregados.

        5.  **Forneça as Informações da Vaga:**
            *   Esta seção ("Quais as informações da vaga?") aparecerá após os dados dos candidatos serem carregados com sucesso.
            *   **Opção 1: "Escrever descrição manual"**
                *   Digite os detalhes da vaga (requisitos, responsabilidades, etc.) no campo "Descrição detalhada da vaga:".
            *   **Opção 2: "Selecionar vaga existente"**
                *   Escolha uma vaga na lista suspensa "Selecione uma vaga:".
                *   Os detalhes da vaga selecionada serão exibidos na seção expansível "Detalhes da vaga selecionada" para sua conferência.

        6.  **Configure e Gere as Recomendações:**
            *   Certifique-se de que uma descrição de vaga válida (manual ou selecionada) esteja presente.
            *   Ajuste o "Número de candidatos para recomendar:" usando o controle deslizante (slider) para definir quantos dos melhores candidatos você deseja ver (entre 1 e 10).
            *   Clique no botão "Gerar Recomendações".

        7.  **Analise os Resultados:**
            *   Aguarde o processamento. Uma mensagem de status indicará o progresso.
            *   Após a conclusão, uma tabela com os "Resultados da Recomendação" será exibida.
            *   A coluna "Similaridade" indica a compatibilidade do candidato com a vaga, onde valores mais próximos de 1 representam maior aderência.

        #### Observações Adicionais:
        *   **Qualidade da Descrição da Vaga:** Para obter recomendações mais precisas, forneça uma descrição de vaga detalhada e clara, especialmente ao usar o modo manual. A IA tentará otimizar a descrição, mas uma boa base é fundamental.
        *   **Validação de Dados Externos:** É crucial que a planilha Excel siga o formato do template e que os dados nas colunas obrigatórias (`id_candidato`, `nome_candidato`, `senioridade`, `curriculo`) estejam preenchidos corretamente e sem valores nulos para evitar interrupções no processo.
        *   **Modelo de Recomendação:** O sistema utiliza um modelo de aprendizado profundo para calcular a similaridade semântica entre os currículos dos candidatos e a descrição da vaga.
        *   **Processamento de Dados Internos:** Ao usar dados internos, o sistema realiza uma etapa de pré-processamento para consolidar diversas informações textuais dos candidatos em um único campo de "currículo" para análise.
    ''')

if __name__ == "__main__":
    main()           
