import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import re
import nltk
import json
import tensorflow as tf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Configurações iniciais
nltk.download('stopwords')
nltk.download('punkt')
st.set_page_config(page_title="Sistema de Recomendação de Vagas", layout="wide")

class SistemaRecomendacao:
    def __init__(self, df_candidatos, df_vagas, model_path):
        self.df_candidatos = df_candidatos
        self.df_vagas = df_vagas
        self.model = tf.keras.models.load_model(model_path)
        self.vectorizer, self.embeddings_cv = self._preparar_dados()
    
    def _preprocessar_texto(self, text):
        stop_words = stopwords.words('portuguese')
        text = re.sub(r'\d+', '', str(text).lower())
        text = re.sub(r'[^\w\s]', '', text)
        tokens = word_tokenize(text)
        return ' '.join([t for t in tokens if t not in stop_words and len(t) > 2])
    
    def _preparar_dados(self):
        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1,2),
            preprocessor=self._preprocessar_texto
        )
        textos_cv = self.df_candidatos['cv_texto_pt'].apply(self._preprocessar_texto)
        embeddings = vectorizer.fit_transform(textos_cv)
        return vectorizer, embeddings
    
    def _processar_vaga(self, descricao_vaga):
        processed = self._preprocessar_texto(descricao_vaga)
        return self.vectorizer.transform([processed])
    
    def recomendar_candidatos(self, descricao_vaga, top_n=5):
        embedding_vaga = self._processar_vaga(descricao_vaga)
        similaridades = cosine_similarity(embedding_vaga, self.embeddings_cv).flatten()
        top_indices = similaridades.argsort()[-top_n:][::-1]
        
        resultados = self.df_candidatos.iloc[top_indices].copy()
        resultados['similaridade'] = similaridades[top_indices]
        return resultados.sort_values('similaridade', ascending=False)

@st.cache_data
def carregar_vagas():
    with open('fiap-tech-challenge-pos-tech-data-analytics/Fase5/datathon/vagas.json', 'r', encoding='utf-8') as f:
        vagas = json.load(f)
    
    dados_vagas = []
    for id_vaga, info in vagas.items():
        dados_vagas.append({
            'id_vaga': id_vaga,
            'titulo': info.get('informacoes_basicas', {}).get('titulo_vaga', 'Sem título'),
            'descricao': f"{info.get('perfil_vaga', {}).get('principais_atividades', '')} {info.get('perfil_vaga', {}).get('competencia_tecnicas_e_comportamentais', '')}"
        })
    return pd.DataFrame(dados_vagas)

def main():
    st.title('Sistema de Recomendação de Candidatos')
    
    RANKING_DADOS_EXTERNOS = "Dados Externos (Upload Excel)"
    RANKING_DADOS_INTERNOS = "Dados Internos (Sistema)"
    
    tab_sistema, tab_documentacao = st.tabs(["Sistema", "Documentação"])
    
    with tab_sistema:
        # Passo 1: Seleção da fonte de dados
        fonte_dados = st.radio(
            "Selecione a fonte de dados dos candidatos:",
            (RANKING_DADOS_EXTERNOS, RANKING_DADOS_INTERNOS),
            horizontal=True
        )
        
        df_candidatos = None
        
        # Passo 2: Carregamento dos candidatos
        if fonte_dados == RANKING_DADOS_EXTERNOS:
            st.subheader("Carregar Candidatos via Excel")
            
            with st.expander("Obter Template", expanded=False):
                template_df = pd.DataFrame(columns=[
                    'id_candidato', 
                    'nome_candidato', 
                    'senioridade', 
                    'curriculo'
                ])
                
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    template_df.to_excel(writer, index=False)
                    worksheet = writer.sheets['Sheet1']
                    worksheet.set_column('A:D', 30)
                
                st.download_button(
                    label="📥 Baixar Template",
                    data=buffer.getvalue(),
                    file_name="template_candidatos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            uploaded_file = st.file_uploader("Carregar planilha de candidatos", type="xlsx")
            if uploaded_file:
                try:
                    with st.spinner("Processando arquivo Excel..."):
                        df_candidatos = pd.read_excel(uploaded_file)
                        df_candidatos.rename(columns={'curriculo': 'cv_texto_pt'}, inplace=True)
                        st.toast("Arquivo processado com sucesso!", icon="✅")
                    
                    required_columns = ['id_candidato', 'nome_candidato', 'senioridade', 'cv_texto_pt']
                    if not all(col in df_candidatos.columns for col in required_columns):
                        missing = [col for col in required_columns if col not in df_candidatos.columns]
                        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}")
                    
                    with st.expander("Visualizar dados carregados", expanded=False):
                        st.dataframe(df_candidatos.head(10), use_container_width=True)
                
                except Exception as e:
                    st.error(f"Erro no processamento: {str(e)}")
                    st.stop()
        
        else:
            st.subheader("Carregar candidatos do sistema interno")  # Dados Internos
            try:
                @st.cache_data
                def carregar_dados_internos():
                    with open('fiap-tech-challenge-pos-tech-data-analytics/Fase5/datathon/applicants.json', 'r', encoding='utf-8') as f:
                        candidatos = json.load(f)
                    
                    dados = []
                    for id_cand, info in candidatos.items():
                        dados.append({
                            'id_candidato': id_cand,
                            'nome_candidato': info.get('infos_basicas', {}).get('nome', '') or \
                                   info.get('informacoes_pessoais', {}).get('nome', 'Nome não informado'),
                            'senioridade': info.get('informacoes_profissionais', {}).get('nivel_profissional', 'Não especificado'),
                            'cv_texto_pt': info.get('cv_pt', 'Currículo não disponível')
                        })
                    return pd.DataFrame(dados)
                
                with st.spinner("Carregando base de candidatos..."):
                    df_candidatos = carregar_dados_internos()
                    st.toast(f"{len(df_candidatos)} candidatos carregados", icon="👥")
                
                with st.expander("Visualizar base interna", expanded=False):
                    st.dataframe(df_candidatos.head(10), use_container_width=True)
            
            except Exception as e:
                st.error(f"Erro ao carregar dados internos: {str(e)}")
                st.stop()
        
        # Só mostra o restante se os dados foram carregados corretamente
        if df_candidatos is not None:
            # Passo 3: Seleção do método de definição da vaga
            st.divider()
            MODO_DESCRICAO = "Escrever descrição manual"
            MODO_SELECAO_VAGA = "Selecionar vaga existente"
            
            metodo_descricao = st.radio(
                "Como deseja definir a vaga?",
                (MODO_DESCRICAO, MODO_SELECAO_VAGA),
                horizontal=True
            )
            
            descricao_vaga = ""
            
            # Passo 4: Entrada dos dados da vaga
            if metodo_descricao == MODO_SELECAO_VAGA:
                df_vagas = carregar_vagas()
                vagas_lista = [f"{row['id_vaga']} - {row['titulo']}" for _, row in df_vagas.iterrows()]
                
                col1, col2 = st.columns([2, 3])
                with col1:
                    vaga_selecionada = st.selectbox(
                        "Selecione uma vaga:",
                        options=vagas_lista,
                        index=0
                    )
                
                if vaga_selecionada:
                    id_vaga = vaga_selecionada.split(' - ')[0]
                    descricao_vaga = df_vagas[df_vagas['id_vaga'] == id_vaga]['descricao'].values[0]
                    
                    with col2:
                        with st.expander("Detalhes da vaga selecionada", expanded=True):
                            st.write(descricao_vaga)
            else:
                descricao_vaga = st.text_area("Descrição detalhada da vaga:", height=200,
                                             placeholder="Insira os requisitos, responsabilidades e detalhes da vaga...")
            
            # Passo 5: Configurações e geração
            if descricao_vaga:
                st.divider()
                num_candidatos = st.slider("Número de candidatos para recomendar:", 
                                         1, 10, 
                                         min(1, 10))
                
                if st.button("Gerar Recomendações", type="primary"):
                    with st.status("Processando recomendações...", expanded=True) as status:
                        st.write("🔧 Inicializando modelo...")
                        sistema = SistemaRecomendacao(
                            df_candidatos=df_candidatos,
                            df_vagas=pd.DataFrame(),  # Não usado no processamento
                            model_path="fiap-tech-challenge-pos-tech-data-analytics/Fase5/datathon/modelo_final.keras"
                        )
                        
                        st.write("📊 Calculando similaridades...")
                        resultados = sistema.recomendar_candidatos(
                            descricao_vaga=descricao_vaga,
                            top_n=num_candidatos
                        )
                        
                        st.write("🧹 Processando resultados...")
                        resultados.fillna({
                            'senioridade': 'Não especificado',
                            'nome_candidato': 'Nome não informado',
                            'cv_texto_pt': 'Currículo não disponível'
                        }, inplace=True)
                        
                        status.update(label="✅ Processo completo!", state="complete", expanded=False)
                        st.balloons()
                    
                    st.divider()
                    st.subheader("Resultados da Recomendação")
                    st.dataframe(
                        resultados[['id_candidato', 'nome_candidato', 'senioridade','cv_texto_pt', 'similaridade']],
                        column_config={
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

if __name__ == "__main__":
    main()
