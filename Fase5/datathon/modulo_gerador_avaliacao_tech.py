# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import json
import apoio_tech as at # Mantido como está, pois é o nome do módulo importado
import os
import markdown # Importado para converter a resposta
from fpdf import FPDF # Mantido como está, nome da biblioteca
import re

st.set_page_config(layout="wide")

# --- Constantes ---
# ... (constantes inalteradas) ...
COR_NAO_SEI = "#D3D3D3"
COR_ERROU = "#FF0000"
COR_INCOMPLETA = "#FFA500"
COR_COMPLETA = "#008000"
COR_SELECAO_BORDA = "#000080"
COR_CALCULAR = "#0000FF"
COR_TEXTO_BOTAO_CLARO = "black"
COR_TEXTO_BOTAO_ESCURO = "white"

TRADUCAO_NAO_SEI = "Não sei a resposta"
TRADUCAO_ERROU = "Errou a resposta"
TRADUCAO_INCOMPLETA = "Resposta incompleta"
TRADUCAO_COMPLETA = "Resposta completa"
OPCAO_OUTRO_ROTULO = "Outro (digitar)"
METODO_ENTRADA_ESTRUTURADO = "Usar Campos Estruturados"
METODO_ENTRADA_TEXTO_LIVRE = "Descrever a Vaga Livremente"
METODO_ENTRADA_SELECIONAR_VAGA = "Selecionar Vagas" # <-- Nova constante
TIPO_PERGUNTA_DESAFIO = "desafio"

# --- Funções Auxiliares ---
# ... (carregar_lista_json, carregar_dados_api inalteradas) ...
@st.cache_data(ttl=3600)
def carregar_lista_json(caminho_arquivo):
    """
    Carrega uma lista de strings de um arquivo JSON.

    Args:
        caminho_arquivo (str): O caminho para o arquivo JSON.

    Returns:
        list: Uma lista de strings carregada do JSON, ou uma lista vazia em caso de erro.
    """    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            if isinstance(dados, list):
                return dados
            else:
                st.error(f"Erro: O arquivo {caminho_arquivo} não contém uma lista JSON válida.")
                return []
    except FileNotFoundError:
        st.error(f"Erro: Arquivo não encontrado - {caminho_arquivo}")
        return []
    except json.JSONDecodeError:
        st.error(f"Erro: Falha ao decodificar JSON do arquivo - {caminho_arquivo}")
        return []
    except Exception as e:
        st.error(f"Erro inesperado ao carregar {caminho_arquivo}: {e}")
        return []

# @st.cache_data # Cache da API pode ser reativado se necessário
def carregar_dados_api(prompt_api):
    """
    Chama a API Generativa e tenta analisar a resposta JSON.

    Args:
        prompt_api (str): O prompt a ser enviado para a API.

    Returns:
        list | None: Uma lista de dicionários representando as perguntas e respostas
                     se a análise for bem-sucedida, caso contrário None.
    """
    
    
    resposta_api_bruta = None
    # Gerar animacao enquanto carrega o download da api
    with st.spinner(f"Gerando perguntas com base em: '{prompt_api[:100]}...'"):
        # Chama a API com o prompt fornecido
        # A função at.generate() deve ser definida no módulo apoio_tech.py
        # e deve lidar com a chamada à API Gemini.
        # Aqui, apenas chamamos a função e retornamos o resultado.
        resposta_api_bruta = at.generate(prompt_api)
        print(f"Prompt enviado para API: {prompt_api}")

    
    print(f"Resposta da API: {resposta_api_bruta}")
    if not resposta_api_bruta:
        st.error("A API não retornou resposta.")
        return None

    try:
        # Limpa possíveis marcadores de código antes de analisar o JSON
        resposta_json_limpa = resposta_api_bruta.strip().removeprefix("```json").removesuffix("```").strip()
        json_parseado = json.loads(resposta_json_limpa)

        # Verifica se a API retornou um erro conhecido (estrutura específica definida no prompt)
        if isinstance(json_parseado, list) and len(json_parseado) > 0 and json_parseado[0].get("problema") == "erro":
             st.error(f"Erro da API: {json_parseado[0].get('resposta', 'Erro desconhecido ao processar o pedido.')}")
             return None # Retorna None em caso de erro da API

        if not isinstance(json_parseado, list):
             st.error(f"Erro: A API não retornou uma lista JSON válida. Resposta: {resposta_json_limpa}")
             return None
        return json_parseado
    except json.JSONDecodeError as e:
        st.error(f"Erro ao decodificar JSON da API: {e}")
        st.error(f"String recebida: {resposta_api_bruta}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado durante o processamento da resposta da API: {e}")
        return None

# --- Funções de Geração de PDF ---
# ... (Classe PDF e gerar_pdf inalteradas) ...
class PDF(FPDF):
    """
    Classe personalizada herdando de FPDF para definir cabeçalho e rodapé
    com tratamento de erro básico para codificação de caracteres.
    """
    def header(self):
        """Define o cabeçalho do PDF com o título."""
        try:
            self.set_font(self.font_family, 'B', 12)
            # Tenta codificar o título para latin-1, substituindo caracteres inválidos
            titulo_codificado = self.title.encode('latin-1', 'replace').decode('latin-1')
            self.cell(0, 10, titulo_codificado, 0, 1, 'C')
        except Exception as e:
            print(f"Erro ao definir header do PDF: {e}")
            # Fallback para um título genérico se houver erro
            self.cell(0, 10, 'Titulo PDF', 0, 1, 'C')
        self.ln(10) # Pula linha após o cabeçalho

    def footer(self):
        """Define o rodapé do PDF com o número da página."""
        self.set_y(-15) # Posiciona 1.5 cm da parte inferior
        try:
            self.set_font(self.font_family, 'I', 8) # Fonte itálica pequena
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C') # Centraliza número da página
        except Exception as e:
            print(f"Erro ao definir footer do PDF: {e}")
# --- Função Principal da Aplicação Streamlit ---

def atualizar_limite_perguntas():
    print("chamou callback")
    """Callback para ajustar o número de perguntas ao mudar a permissão de código."""
    permitir_codigo = st.session_state.get('check_codigo_resposta', False) # Pega o estado ATUAL do checkbox
    


def gerar_pdf(titulo, itens_pdf):
    """
    Gera um arquivo PDF a partir de uma lista de dicionários, renderizando
    Markdown básico (negrito, itálico, código inline, blocos de código)
    e tratando quebras de linha dentro de blocos de código.

    Args:
        titulo (str): O título do documento PDF.
        itens_pdf (list): Uma lista de dicionários, onde cada dicionário deve ter
                          as chaves 'prefix' (str, opcional) e 'text' (str).
                          O conteúdo de 'text' pode conter Markdown.

    Returns:
        bytes: O conteúdo do PDF gerado como bytes, ou bytes vazios em caso de erro.
    """
    pdf_doc = PDF()
    pdf_doc.title = titulo
    pdf_doc.font_family = 'Arial' # Define a família da fonte padrão

    try:
        # Tenta definir a fonte padrão para o corpo do texto
        pdf_doc.set_font(pdf_doc.font_family, '', 11)
    except Exception as e:
        st.error(f"Erro ao definir a fonte padrão para o PDF: {e}")
        # Continua mesmo se a fonte padrão falhar, pode usar fallback interno do FPDF

    pdf_doc.add_page()
    # Inicializa o parser Markdown com extensões para blocos de código
    markdown_parser = markdown.Markdown(extensions=['fenced_code', 'codehilite'])

    for item_pdf in itens_pdf:
        # Renderiza o Prefixo (se existir)
        try:
            pdf_doc.set_font(pdf_doc.font_family, 'B', 11) # Negrito para o prefixo
            texto_prefixo = item_pdf.get('prefix', '')
            # Verifica se há Markdown básico no prefixo para decidir como renderizar
            if '**' in texto_prefixo or '*' in texto_prefixo or '`' in texto_prefixo:
                 html_prefixo = markdown_parser.convert(texto_prefixo)
                 # Substitui \n por <br> dentro de blocos de código <pre><code> no prefixo
                 html_prefixo = re.sub(r'(<pre.*?><code.*?>)(.*?)(</code></pre>)',
                                      lambda m: m.group(1) + m.group(2).replace('\n', '<br>\n') + m.group(3),
                                      html_prefixo, flags=re.DOTALL)
                 pdf_doc.write_html(html_prefixo)
            else:
                 # Se não houver markdown, usa multi_cell para texto simples (trata quebras de linha)
                 # Codifica para latin-1 com substituição para evitar erros no FPDF
                 pdf_doc.multi_cell(0, 7, texto_prefixo.encode('latin-1', 'replace').decode('latin-1'))
            pdf_doc.set_font(pdf_doc.font_family, '', 11) # Volta para fonte normal
        except Exception as e:
             print(f"Erro ao escrever prefixo no PDF: {e} - Texto: {item_pdf.get('prefix', '')[:50]}...")
             # Fallback para indicar erro no PDF
             pdf_doc.multi_cell(0, 7, "[Erro ao renderizar prefixo]")

        # Renderiza o Texto Principal (com Markdown)
        try:
            texto_item_md = item_pdf.get('text', '')
            texto_item_html = markdown_parser.convert(texto_item_md)

            # Substitui \n por <br>\n DENTRO das tags <pre><code> para forçar quebras de linha
            texto_item_html_com_br = re.sub(r'(<pre.*?><code.*?>)(.*?)(</code></pre>)',
                                       lambda m: m.group(1) + m.group(2).replace('\n', '<br>\n') + m.group(3),
                                       texto_item_html, flags=re.DOTALL)

            pdf_doc.write_html(texto_item_html_com_br) # Escreve o HTML processado
            pdf_doc.ln(5) # Adiciona um pequeno espaço após o item
        except Exception as e:
             print(f"Erro ao escrever texto HTML no PDF: {e} - Texto MD: {texto_item_md[:50]}...")
             # Fallback para texto simples se write_html falhar
             pdf_doc.multi_cell(0, 7, texto_item_md.encode('latin-1', 'replace').decode('latin-1'))
             pdf_doc.ln(5)

    # Retorna o conteúdo do PDF como bytes
    try:
        return pdf_doc.output(dest='B')
    except Exception as e:
        st.error(f"Erro ao gerar o arquivo PDF final: {e}")
        return b""

# --- Função Principal da Aplicação Streamlit ---

def exibir_quiz():
    """
    Função principal que renderiza a interface do Streamlit para gerar
    e realizar a avaliação técnica, agora com abas.
    """
    st.title("Gerador de Avaliação Técnica")

    # --- CSS para aumentar fonte das abas ---
    st.markdown("""
    <style>
        /* Ajuste o valor de font-size conforme necessário */
        div[data-baseweb="tab-list"] button[role="tab"] {
            font-size: 18px !important;
            font-weight: bold !important; /* Opcional: Deixa em negrito */
        }
    </style>
    """, unsafe_allow_html=True)
    # --- Fim do CSS das abas ---

    # Inicializa estados para controle dos PDFs sob demanda
    if 'pdf_perguntas_data' not in st.session_state: st.session_state.pdf_perguntas_data = None
    if 'pdf_respostas_data' not in st.session_state: st.session_state.pdf_respostas_data = None
    if 'pdf_perguntas_pronto' not in st.session_state: st.session_state.pdf_perguntas_pronto = False
    if 'pdf_respostas_pronto' not in st.session_state: st.session_state.pdf_respostas_pronto = False

    # Cria as abas
    
    tab_sistema, tab_documentacao = st.tabs(["Sistema", "Documentação"])

    # --- Conteúdo da Aba Sistema ---
    with tab_sistema:
        # Carregar opções dos arquivos JSON
        # ... (código de carregamento inalterado) ...
        diretorio_script = os.path.dirname(__file__)
        diretorio_script = f"{diretorio_script}/dataset"
        base_profissoes = carregar_lista_json(os.path.join(diretorio_script, "profissoes.json"))
        base_linguagens = carregar_lista_json(os.path.join(diretorio_script, "linguagens.json"))
        base_senioridades = carregar_lista_json(os.path.join(diretorio_script, "senioridades.json"))        

        opcoes_profissoes = base_profissoes + [OPCAO_OUTRO_ROTULO]
        opcoes_linguagens = base_linguagens + [OPCAO_OUTRO_ROTULO]
        opcoes_senioridades = base_senioridades + [OPCAO_OUTRO_ROTULO]


        st.subheader("Configure a Vaga")

        # Inicializa estado da sessão se necessário
        # ... (código de inicialização inalterado) ...
        if 'metodo_entrada' not in st.session_state: st.session_state.metodo_entrada = METODO_ENTRADA_ESTRUTURADO
        if 'descricao_vaga' not in st.session_state: st.session_state.descricao_vaga = ""


        # Seleção do método de entrada (Estruturado, Texto Livre ou Selecionar Vaga)
        # ... (código do radio inalterado) ...
        st.session_state.metodo_entrada = st.radio(
            "Como deseja definir a vaga?",
            # Adiciona a nova opção ao tuple
            (METODO_ENTRADA_ESTRUTURADO, METODO_ENTRADA_TEXTO_LIVRE, METODO_ENTRADA_SELECIONAR_VAGA),
            key='radio_metodo_entrada', horizontal=True,
        )


        # Exibe campos de acordo com o método de entrada selecionado
        # ... (código dos métodos de entrada inalterado) ...
        if st.session_state.metodo_entrada == METODO_ENTRADA_ESTRUTURADO:
            # --- Seção de Campos Estruturados (código existente inalterado) ---
            # Inicializa estado da sessão para campos estruturados
            if 'profissao_selecionada' not in st.session_state: st.session_state.profissao_selecionada = opcoes_profissoes[0] if opcoes_profissoes else None
            if 'profissao_personalizada' not in st.session_state: st.session_state.profissao_personalizada = ""
            if 'linguagens_selecionadas' not in st.session_state: st.session_state.linguagens_selecionadas = [opcoes_linguagens[0]] if opcoes_linguagens else []
            if 'linguagens_personalizadas' not in st.session_state: st.session_state.linguagens_personalizadas = ""
            if 'senioridade_selecionada' not in st.session_state: st.session_state.senioridade_selecionada = opcoes_senioridades[0] if opcoes_senioridades else None
            if 'senioridade_personalizada' not in st.session_state: st.session_state.senioridade_personalizada = ""
            if 'detalhes_opcionais' not in st.session_state: st.session_state.detalhes_opcionais = ""

            coluna1, coluna2, coluna3 = st.columns(3)
            with coluna1: # Profissão
                profissao_anterior = st.session_state.profissao_selecionada
                st.session_state.profissao_selecionada = st.selectbox("Profissão:", opcoes_profissoes, index=opcoes_profissoes.index(st.session_state.profissao_selecionada) if st.session_state.profissao_selecionada in opcoes_profissoes else 0, key='select_profissao')
                # Limpa campo personalizado se 'Outro' for desmarcado
                if st.session_state.profissao_selecionada != OPCAO_OUTRO_ROTULO and profissao_anterior == OPCAO_OUTRO_ROTULO: st.session_state.profissao_personalizada = ""
                # Mostra campo de texto se 'Outro' estiver selecionado
                if st.session_state.profissao_selecionada == OPCAO_OUTRO_ROTULO: st.session_state.profissao_personalizada = st.text_input("Digite a profissão:", value=st.session_state.profissao_personalizada, key='input_profissao_outro')
            with coluna2: # Conhecimentos
                linguagens_anteriores = st.session_state.linguagens_selecionadas
                st.session_state.linguagens_selecionadas = st.multiselect("Conhecimentos:", opcoes_linguagens, default=st.session_state.linguagens_selecionadas, key='multiselect_linguagens')
                # Limpa campo personalizado se 'Outro' for desmarcado
                if OPCAO_OUTRO_ROTULO not in st.session_state.linguagens_selecionadas and OPCAO_OUTRO_ROTULO in linguagens_anteriores: st.session_state.linguagens_personalizadas = ""
                # Mostra campo de texto se 'Outro' estiver selecionado
                if OPCAO_OUTRO_ROTULO in st.session_state.linguagens_selecionadas: st.session_state.linguagens_personalizadas = st.text_input("Outros conhecimentos (separados por vírgula):", value=st.session_state.linguagens_personalizadas, key='input_linguagens_outro')
            with coluna3: # Senioridade
                senioridade_anterior = st.session_state.senioridade_selecionada
                st.session_state.senioridade_selecionada = st.selectbox("Senioridade:", opcoes_senioridades, index=opcoes_senioridades.index(st.session_state.senioridade_selecionada) if st.session_state.senioridade_selecionada in opcoes_senioridades else 0, key='select_senioridade')
                # Limpa campo personalizado se 'Outro' for desmarcado
                if st.session_state.senioridade_selecionada != OPCAO_OUTRO_ROTULO and senioridade_anterior == OPCAO_OUTRO_ROTULO: st.session_state.senioridade_personalizada = ""
                # Mostra campo de texto se 'Outro' estiver selecionado
                if st.session_state.senioridade_selecionada == OPCAO_OUTRO_ROTULO: st.session_state.senioridade_personalizada = st.text_input("Digite a senioridade:", value=st.session_state.senioridade_personalizada, key='input_senioridade_outro')

            # Campo para detalhes adicionais
            st.session_state.detalhes_opcionais = st.text_area(
                "Detalhes Adicionais da Vaga (Opcional):",
                value=st.session_state.detalhes_opcionais,
                max_chars=500,
                height=100,
                key='text_area_detalhes_opcionais',
                help="Informe aqui outros requisitos, responsabilidades ou contexto relevante sobre a vaga."
            )
            # --- Fim da Seção de Campos Estruturados ---

        elif st.session_state.metodo_entrada == METODO_ENTRADA_TEXTO_LIVRE:
            # --- Seção de Texto Livre (código existente inalterado) ---
            st.session_state.descricao_vaga = st.text_area(
                "Descreva a vaga desejada:",
                value=st.session_state.descricao_vaga,
                max_chars=1500,
                height=200,
                key='text_area_vaga'
            )
            # --- Fim da Seção de Texto Livre ---

        # --- NOVO: Condição para a opção "Selecionar Vagas" ---
        elif st.session_state.metodo_entrada == METODO_ENTRADA_SELECIONAR_VAGA:
            st.info("(Ainda não implementado)") # Exibe a mensagem desejada
        # --- FIM DA NOVA CONDIÇÃO ---


        # --- Seção de Opções de Geração (código existente inalterado) ---
        # ... (código das opções inalterado) ...
        st.markdown("---")
        st.subheader("Opções de Geração")
        coluna_opcoes1, coluna_opcoes2, coluna_opcoes3 = st.columns(3)

        with coluna_opcoes1:
            # Input para número de perguntas padrão
            # --- MODIFICAÇÃO: Troca selectbox por slider ---
            if 'numero_perguntas_desejadas' not in st.session_state: st.session_state.numero_perguntas_desejadas = 10
            # opcoes_numero_perguntas = list(range(3, 31)) # Não é mais necessário
            st.session_state.numero_perguntas_desejadas = st.slider(
                "Quantidade de perguntas:",
                min_value=3, max_value=st.session_state.max_perguntas_padrao, # Define o intervalo do slider
                value=st.session_state.numero_perguntas_desejadas, # Valor inicial/atual
                step=1, # Incremento de 1
                key='num_perguntas',
                help="Número de perguntas no formato padrão (pergunta/resposta/nível)."
            )

        with coluna_opcoes2:
            # Checkbox para incluir pergunta desafio
            if 'incluir_pergunta_desafio' not in st.session_state: st.session_state.incluir_pergunta_desafio = False
            st.write("") # Espaçamento vertical
            st.write("") # Espaçamento vertical
            st.session_state.incluir_pergunta_desafio = st.checkbox(
                "Incluir Pergunta Desafio?",
                value=st.session_state.incluir_pergunta_desafio,
                key='check_desafio',
                help="Adiciona uma pergunta sobre um problema técnico com 3 possíveis soluções."
            )

        with coluna_opcoes3:
            # Checkbox para permitir código nas respostas
            if 'permitir_codigo_na_resposta' not in st.session_state: st.session_state.permitir_codigo_na_resposta = False
            st.write("") # Espaçamento vertical
            st.write("") # Espaçamento vertical
            st.session_state.permitir_codigo_na_resposta = st.checkbox(
                "Permitir Código nas Respostas?",
                value=st.session_state.permitir_codigo_na_resposta,
                key='check_codigo_resposta',
                on_change=atualizar_limite_perguntas,
                help="Marque se deseja que as respostas esperadas possam incluir exemplos de código."
            )


        # --- Botão Gerar Perguntas (código existente inalterado) ---
        # ... (código do botão e chamada da API inalterado) ...
        botao_gerar_desabilitado = st.session_state.metodo_entrada == METODO_ENTRADA_SELECIONAR_VAGA

        if st.button("Gerar Perguntas da Avaliação", type="primary", disabled=botao_gerar_desabilitado):
            # O código dentro deste if só executa se o botão não estiver desabilitado
            numero_perguntas_padrao = st.session_state.numero_perguntas_desejadas
            incluir_desafio = st.session_state.incluir_pergunta_desafio
            permitir_codigo = st.session_state.permitir_codigo_na_resposta
            prompt_para_api = ""
            entrada_valida = True
            informacao_vaga = ""
            texto_detalhes_opcionais = ""

            # Constrói a descrição da vaga com base no método de entrada
            if st.session_state.metodo_entrada == METODO_ENTRADA_ESTRUTURADO:
                # ... (lógica de validação e construção do prompt para método estruturado - inalterada) ...
                profissao_final = st.session_state.profissao_personalizada.strip() if st.session_state.profissao_selecionada == OPCAO_OUTRO_ROTULO else st.session_state.profissao_selecionada
                senioridade_final = st.session_state.senioridade_personalizada.strip() if st.session_state.senioridade_selecionada == OPCAO_OUTRO_ROTULO else st.session_state.senioridade_selecionada
                # Processa conhecimentos, incluindo os personalizados
                conhecimentos_finais = [lang for lang in st.session_state.linguagens_selecionadas if lang != OPCAO_OUTRO_ROTULO] if st.session_state.linguagens_selecionadas else []
                if OPCAO_OUTRO_ROTULO in st.session_state.linguagens_selecionadas and st.session_state.linguagens_personalizadas.strip():
                    linguagens_personalizadas_lista = [lang.strip() for lang in st.session_state.linguagens_personalizadas.split(',') if lang.strip()]
                    conhecimentos_finais.extend(linguagens_personalizadas_lista)
                conhecimentos_finais = list(dict.fromkeys(conhecimentos_finais)) # Remove duplicados
                conhecimentos_str = ", ".join(conhecimentos_finais)
                texto_detalhes_opcionais = st.session_state.detalhes_opcionais.strip()

                # Validações básicas dos campos estruturados
                if not profissao_final: st.warning("Selecione ou digite a Profissão."); entrada_valida = False
                if not senioridade_final: st.warning("Selecione ou digite a Senioridade."); entrada_valida = False
                if not conhecimentos_str: st.warning("Selecione ou digite os Conhecimentos."); entrada_valida = False

                if entrada_valida:
                    informacao_vaga = f"para a vaga {profissao_final} {senioridade_final}, com conhecimento em {conhecimentos_str}"
                    if texto_detalhes_opcionais:
                        informacao_vaga += f". incluir tambem perguntas sobre: {texto_detalhes_opcionais}"


            elif st.session_state.metodo_entrada == METODO_ENTRADA_TEXTO_LIVRE:
                 # ... (lógica de validação e construção do prompt para método texto livre - inalterada) ...
                descricao_vaga_texto = st.session_state.descricao_vaga.strip()
                # Validações básicas do texto livre
                if not descricao_vaga_texto: st.warning("Descreva a vaga no campo de texto."); entrada_valida = False
                elif len(descricao_vaga_texto) < 20: st.warning("Descrição da vaga muito curta."); entrada_valida = False

                if entrada_valida:
                    informacao_vaga = f"com base na seguinte descrição de vaga: '{descricao_vaga_texto}'"


            # Validação do número de perguntas (inalterada)
            if not isinstance(numero_perguntas_padrao, int) or numero_perguntas_padrao < 3:
                 st.warning("Insira um número válido de perguntas padrão (mínimo 3)."); entrada_valida = False

            # Se a entrada for válida, monta o prompt e chama a API (inalterada)
            if entrada_valida and informacao_vaga:
                # ... (lógica de montagem do prompt e chamada da API - inalterada) ...
                instrucao_codigo = "As respostas DEVEM incluir exemplos de código relevantes quando apropriado." if permitir_codigo else "As respostas devem focar em conceitos e definições, EVITANDO exemplos de código sempre que possível."

                if incluir_desafio:
                    prompt_para_api = (
                        f"Gere {numero_perguntas_padrao} perguntas técnicas padrão E 1 pergunta desafio de problema/solução "
                        f"{informacao_vaga}. {instrucao_codigo} "
                        f"A pergunta desafio deve ter um problema como 'pergunta' e 3 soluções como 'resposta'. "
                        f"Siga o formato JSON especificado nas instruções do sistema."
                    )
                    total_perguntas_esperado = numero_perguntas_padrao + 1
                else:
                    prompt_para_api = (
                        f"Gere {numero_perguntas_padrao} perguntas técnicas padrão {informacao_vaga}. "
                        f"{instrucao_codigo} "
                        f"Siga o formato JSON especificado nas instruções do sistema."
                    )
                    total_perguntas_esperado = numero_perguntas_padrao

                print(f"Prompt enviado para API: {prompt_para_api}")
                perguntas_carregadas = carregar_dados_api(prompt_para_api)

                # Processa as perguntas carregadas se não houve erro da API
                if perguntas_carregadas is not None: # Verifica se não é None (erro tratado em carregar_dados_api)
                     # Avisa se o número de perguntas retornado for diferente do esperado
                     if len(perguntas_carregadas) != total_perguntas_esperado:
                         st.warning(f"A API gerou {len(perguntas_carregadas)} perguntas, mas foram solicitadas {total_perguntas_esperado}. Exibindo as perguntas geradas.")

                     # Armazena as perguntas e inicializa estados para o quiz
                     st.session_state.perguntas = perguntas_carregadas
                     numero_real_perguntas = len(st.session_state.perguntas)
                     st.session_state.pontuacoes = [None] * numero_real_perguntas
                     st.session_state.respostas_avaliacao = [None] * numero_real_perguntas
                     st.session_state.opcoes_selecionadas = [None] * numero_real_perguntas
                     st.session_state.quiz_gerado = True
                     # Limpa resultados anteriores ao gerar novas perguntas
                     if 'mostrar_resultados' in st.session_state:
                         del st.session_state['mostrar_resultados']
                     st.rerun() # Recarrega a página para exibir o quiz
                else:
                     # Limpa o estado se a API falhar ou retornar erro explícito
                     st.session_state.perguntas = []
                     st.session_state.quiz_gerado = False
                     if 'mostrar_resultados' in st.session_state:
                         del st.session_state['mostrar_resultados']


        st.divider()

        # --- Seção de Exibição do Quiz ---
        if st.session_state.get('quiz_gerado', False) and 'perguntas' in st.session_state and st.session_state.perguntas:

            # --- MODIFICAÇÃO: Adiciona a classe .resposta-destaque ao CSS ---
            css_personalizado = f"""
            <style>
     
                /* Estilos para os botões de avaliação */
                div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="primary"] {{ background-color: {COR_NAO_SEI} !important; color: {COR_TEXTO_BOTAO_CLARO} !important; border: 2px solid {COR_SELECAO_BORDA} !important; border-radius: 5px !important; }}
                div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="primary"] {{ background-color: {COR_ERROU} !important; color: {COR_TEXTO_BOTAO_ESCURO} !important; border: 2px solid {COR_SELECAO_BORDA} !important; border-radius: 5px !important; }}
                div[data-testid="stHorizontalBlock"] > div:nth-child(3) button[kind="primary"] {{ background-color: {COR_INCOMPLETA} !important; color: {COR_TEXTO_BOTAO_CLARO} !important; border: 2px solid {COR_SELECAO_BORDA} !important; border-radius: 5px !important; }}
                div[data-testid="stHorizontalBlock"] > div:nth-child(4) button[kind="primary"] {{ background-color: {COR_COMPLETA} !important; color: {COR_TEXTO_BOTAO_ESCURO} !important; border: 2px solid {COR_SELECAO_BORDA} !important; border-radius: 5px !important; }}
                /* Estilo para o botão de calcular resultado */
                #container-botao-final button {{ background-color: {COR_CALCULAR} !important; color: {COR_TEXTO_BOTAO_ESCURO} !important; border: 1px solid {COR_CALCULAR} !important; border-radius: 5px !important; width: 100%; }}
                #container-botao-final button:hover {{ background-color: #0000CC !important; border-color: #000099 !important; }}
                /* Efeito hover geral para botões nas colunas horizontais */
                div[data-testid="stHorizontalBlock"] button:hover {{ opacity: 0.9; }}

                /* Estilos para blocos de código (mantidos) */
                div[data-testid="stMarkdown"] pre {{
                    background-color: #f0f0f0;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ccc;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                
                div[data-testid="stMarkdown"] code {{
                    background-color: transparent;
                    padding: 0;
                }}

                /* Estilo para botões de download (mantidos) */
                .stDownloadButton button {{
                    width: 100%;
                    background-color: #6c757d;
                    color: white;
                    border: none;
                }}
                .stDownloadButton button:hover {{
                    background-color: #5a6268;
                    color: white;
                    border: none;
                }}

                /* --- NOVO: Estilo para destacar a resposta --- */
                .resposta-destaque {{
                    background-color: #e9ecef; /* Cinza claro */
                    padding: 15px;             /* Espaçamento interno */
                    border-radius: 5px;        /* Cantos arredondados */
                    margin-bottom: 15px;       /* Espaço abaixo */
                    border: 1px solid #ced4da; /* Borda sutil */
                }}
                /* Ajuste opcional para blocos de código dentro da resposta destacada */
                .resposta-destaque pre {{
                    background-color: #f8f9fa; /* Cinza um pouco diferente para código */
                    border: 1px solid #dee2e6;
                }}
                
                /* --- FIM DO NOVO ESTILO --- */
            </style>
            """
            st.markdown(css_personalizado, unsafe_allow_html=True)
            # --- FIM DA MODIFICAÇÃO CSS ---

            st.header("Avaliação de Conhecimentos")

            # Recupera dados do estado da sessão
            perguntas = st.session_state.perguntas
            pontuacoes = st.session_state.pontuacoes
            respostas_avaliacao = st.session_state.respostas_avaliacao
            opcoes_selecionadas = st.session_state.opcoes_selecionadas

            def atualizar_resposta(indice_pergunta, pontuacao, resposta_avaliacao, chave_botao):
                """
                Atualiza o estado da sessão para uma pergunta específica quando um
                botão de avaliação é clicado.
                (Docstring e código inalterados)
                """
                st.session_state.pontuacoes[indice_pergunta] = pontuacao
                st.session_state.respostas_avaliacao[indice_pergunta] = resposta_avaliacao
                st.session_state.opcoes_selecionadas[indice_pergunta] = chave_botao
                # Limpa o estado de resultado se uma resposta for alterada
                if 'mostrar_resultados' in st.session_state:
                    del st.session_state['mostrar_resultados']

            # Itera sobre as perguntas para exibi-las
            for i, q in enumerate(perguntas):
                eh_desafio = q.get('tipo') == TIPO_PERGUNTA_DESAFIO

                # Exibe nível e se é desafio
                texto_legenda = f"Nível: {q.get('nivel', 'N/A')}"
                if eh_desafio: texto_legenda += " (Desafio: Problema/Solução)"
                st.caption(texto_legenda)

                # Exibe a pergunta/problema
                st.info(f"{i+1}. {q.get('pergunta', 'Pergunta/Problema não encontrado')}")

                # Exibe a resposta esperada/soluções
                st.markdown(f"**Resposta Esperada:**")
                resposta_bruta = q.get('resposta', 'Resposta/Soluções não encontrada')

                # --- MODIFICAÇÃO: Passa o Markdown bruto diretamente para st.markdown dentro do div ---
                try:
                    # st.markdown pode renderizar markdown diretamente, incluindo code blocks
                    st.markdown(f'<div class="resposta-destaque">{resposta_bruta}</div>', unsafe_allow_html=True)
                except Exception as e:
                    print(f"Erro ao renderizar resposta Markdown: {e}")
                    # Fallback para texto simples pré-formatado dentro do div estilizado
                    st.markdown(f'<div class="resposta-destaque"><pre>{resposta_bruta}</pre></div>', unsafe_allow_html=True)
                # --- FIM DA MODIFICAÇÃO ---

                # Define as opções de botões de avaliação
                # ... (código dos botões inalterado) ...
                opcoes_botoes = [
                    {"label": TRADUCAO_NAO_SEI, "score": 0, "key_prefix": "nsr"},
                    {"label": TRADUCAO_ERROU, "score": -1, "key_prefix": "er"},
                    {"label": TRADUCAO_INCOMPLETA, "score": 0.5, "key_prefix": "ri"},
                    {"label": TRADUCAO_COMPLETA, "score": 1, "key_prefix": "rc"},
                ]
                # Cria colunas para os botões
                colunas_botoes = st.columns(len(opcoes_botoes))
                # Adiciona cada botão à sua coluna
                for indice_botao, opcao_botao in enumerate(opcoes_botoes):
                    with colunas_botoes[indice_botao]:
                        chave_botao = f"{opcao_botao['key_prefix']}_{i}"
                        # Define o tipo do botão (primário se selecionado, secundário caso contrário)
                        tipo_botao = "primary" if opcoes_selecionadas[i] == chave_botao else "secondary"
                        # Cria o botão e define a ação ao clicar
                        if st.button(opcao_botao["label"], key=chave_botao, type=tipo_botao, use_container_width=True):
                            atualizar_resposta(i, opcao_botao["score"], opcao_botao["label"], chave_botao)
                            st.rerun() # Recarrega para atualizar a aparência do botão
                st.divider() # Linha divisória entre as perguntas

            # Botão Calcular Resultado e Botões de Geração/Download PDF
            
            st.subheader("O que deseja fazer agora?") 

            coluna_calcular, coluna_pdf1, coluna_pdf2 = st.columns(3) # Define 3 colunas de largura igual

            with coluna_calcular:
                # Container para aplicar estilo específico ao botão de calcular
                st.markdown('<div id="container-botao-final">', unsafe_allow_html=True)
                botao_calcular_clicado = st.button("Calcular Resultado Final", key="calcular_final", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if botao_calcular_clicado:
                    st.session_state['mostrar_resultados'] = True # Marca para exibir a seção de resultados
                    # Opcional: Resetar estado dos PDFs ao calcular?
                    # st.session_state.pdf_perguntas_pronto = False
                    # st.session_state.pdf_respostas_pronto = False
                    # st.session_state.pdf_perguntas_data = None
                    # st.session_state.pdf_respostas_data = None
                    st.rerun() # Recarrega para mostrar resultados

            # Prepara dados para os PDFs (serão usados quando os botões "Preparar" forem clicados)
            perguntas_para_pdf = []
            respostas_para_pdf = []
            # Garante que as perguntas existem no estado da sessão antes de preparar os dados
            if 'perguntas' in st.session_state and st.session_state.perguntas:
                for i, q in enumerate(st.session_state.perguntas):
                    texto_pergunta = q.get('pergunta', 'N/A')
                    texto_nivel = f"Nível: {q.get('nivel', 'N/A')}{' (Desafio)' if q.get('tipo') == TIPO_PERGUNTA_DESAFIO else ''}"
                    texto_resposta = q.get('resposta', 'N/A')

                    # Formato para PDF de Perguntas (apenas pergunta e espaço para resposta)
                    prefixo_perguntas_pdf = f"**{i+1}. Pergunta:** {texto_pergunta}\n"
                    perguntas_para_pdf.append({
                         "prefix": prefixo_perguntas_pdf,
                         "text": "Resposta:  <br><br><br><br><br><br><br><br><br>" # Espaço em branco com quebras de linha HTML
                    })

                    # Formato para PDF de Respostas (pergunta, nível e resposta esperada)
                    prefixo_respostas_pdf = f"**{i+1}. Pergunta:** {texto_pergunta}\n    *({texto_nivel})*" # Nível em itálico
                    respostas_para_pdf.append({
                        "prefix": prefixo_respostas_pdf,
                        "text": texto_resposta # Resposta com possível markdown
                    })

            with coluna_pdf1:
                # Botão para PREPARAR o PDF de perguntas
                st.markdown('<div id="container-botao-pdf">', unsafe_allow_html=True)
                if st.button("Gerar PDF das Perguntas", key="prep_perguntas", use_container_width=True):
                    with st.spinner("Gerando PDF das perguntas..."):
                        if perguntas_para_pdf: # Verifica se há dados para gerar
                            pdf_data = gerar_pdf("Perguntas da Avaliação", perguntas_para_pdf)
                            if pdf_data:
                                st.session_state.pdf_perguntas_data = pdf_data
                                st.session_state.pdf_perguntas_pronto = True
                                st.session_state.pdf_respostas_pronto = False # Garante que só um botão de download apareça por vez
                                st.rerun() # Recarrega para mostrar o botão de download
                            else:
                                st.error("Falha ao gerar PDF das perguntas.")
                                st.session_state.pdf_perguntas_pronto = False
                        else:
                            st.warning("Não há perguntas carregadas para gerar o PDF.")
                            st.session_state.pdf_perguntas_pronto = False

                # Botão de DOWNLOAD (condicional)
                if st.session_state.get('pdf_perguntas_pronto', False) and st.session_state.get('pdf_perguntas_data'):
                    st.download_button(
                        label="⬇️ Baixar PDF das Perguntas",
                        data=bytes(st.session_state.pdf_perguntas_data), # Garante que são bytes
                        file_name="perguntas_avaliacao.pdf",
                        mime="application/pdf",
                        key="download_perguntas_final",
                        use_container_width=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)    
                    # Opcional: Botão para ocultar o download se não quiser mais baixar
                    # if st.button("Ocultar Download Perguntas", key="cancel_pdf_perguntas", use_container_width=True):
                    #     st.session_state.pdf_perguntas_pronto = False
                    #     st.session_state.pdf_perguntas_data = None
                    #     st.rerun()

            with coluna_pdf2:
                # Botão para PREPARAR o PDF de respostas
                st.markdown('<div id="container-botao-pdf">', unsafe_allow_html=True)
                if st.button("Gerar PDF das das Perguntas com Respostas", key="prep_respostas", use_container_width=True):
                    with st.spinner("Gerando PDF das respostas..."):
                        if respostas_para_pdf: # Verifica se há dados para gerar
                            pdf_data = gerar_pdf("Respostas Esperadas da Avaliação", respostas_para_pdf)
                            if pdf_data:
                                st.session_state.pdf_respostas_data = pdf_data
                                st.session_state.pdf_respostas_pronto = True
                                st.session_state.pdf_perguntas_pronto = False # Garante que só um botão de download apareça por vez
                                st.rerun() # Recarrega para mostrar o botão de download
                            else:
                                st.error("Falha ao gerar PDF das respostas.")
                                st.session_state.pdf_respostas_pronto = False
                        else:
                             st.warning("Não há respostas carregadas para gerar o PDF.")
                             st.session_state.pdf_respostas_pronto = False

                # Botão de DOWNLOAD (condicional)
                if st.session_state.get('pdf_respostas_pronto', False) and st.session_state.get('pdf_respostas_data'):
                    st.download_button(
                        label="⬇️ Baixar PDF das Perguntas e Respostas",
                        data=bytes(st.session_state.pdf_respostas_data), # Garante que são bytes
                        file_name="respostas_avaliacao.pdf",
                        mime="application/pdf",
                        key="download_respostas_final",
                        use_container_width=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)
                    # Opcional: Botão para ocultar o download
                    # if st.button("Ocultar Download Respostas", key="cancel_pdf_respostas", use_container_width=True):
                    #     st.session_state.pdf_respostas_pronto = False
                    #     st.session_state.pdf_respostas_data = None
                    #     st.rerun()


            # Exibição do Resultado (Condicional, se o botão 'Calcular' foi clicado)
            # ... (código de cálculo e exibição de resultados inalterado) ...
            if st.session_state.get('mostrar_resultados', False):
                pontuacoes_padrao = []
                pontuacao_desafio = None
                resposta_desafio = None
                num_perguntas_padrao_geradas = 0
                indice_pergunta_desafio = -1
                # Flag para indicar se o desafio foi respondido com pontuação > 0 (terá peso dobrado)
                desafio_respondido_com_peso = False

                # Separa pontuações padrão e desafio, identifica índice do desafio
                for i, q in enumerate(perguntas):
                     eh_pergunta_desafio = q.get('tipo') == TIPO_PERGUNTA_DESAFIO
                     if eh_pergunta_desafio:
                         indice_pergunta_desafio = i
                         if pontuacoes[i] is not None: # Se a pergunta desafio foi avaliada
                             pontuacao_desafio = pontuacoes[i]
                             resposta_desafio = respostas_avaliacao[i]
                             # Verifica se a resposta foi 'incompleta' ou 'completa' para dobrar o peso
                             if pontuacao_desafio > 0: # Corresponde a 0.5 ou 1
                                 desafio_respondido_com_peso = True
                     else:
                         num_perguntas_padrao_geradas += 1
                         if pontuacoes[i] is not None: # Se a pergunta padrão foi avaliada
                             pontuacoes_padrao.append(pontuacoes[i])

                perguntas_padrao_respondidas = len(pontuacoes_padrao)
                desafio_respondido = pontuacao_desafio is not None

                # Verifica se alguma pergunta foi respondida para calcular o resultado
                if perguntas_padrao_respondidas > 0 or desafio_respondido:
                    st.subheader("Resultado da Avaliação")

                    # Cálculo da pontuação
                    pontuacao_total_padrao = sum(pontuacoes_padrao)
                    contribuicao_final_pontuacao_desafio = 0
                    # Máximo possível para padrão é o número de perguntas padrão geradas
                    pontuacao_maxima_possivel_padrao = num_perguntas_padrao_geradas
                    pontuacao_maxima_possivel_desafio = 0 # Inicializa

                    if desafio_respondido:
                        if desafio_respondido_com_peso:
                            # Dobra o score do desafio se for incompleto (0.5*2=1) ou completo (1*2=2)
                            contribuicao_final_pontuacao_desafio = pontuacao_desafio * 2
                            pontuacao_maxima_possivel_desafio = 1 * 2 # Peso máximo dobrado é 2
                        else:
                            # Mantém o score original se for 'Não sei' (0) ou 'Errou' (-1)
                            contribuicao_final_pontuacao_desafio = pontuacao_desafio
                            # O peso máximo base é 1 se a resposta não for incompleta/completa
                            pontuacao_maxima_possivel_desafio = 1

                    # Calcula o score total final e o máximo possível final (considerando pesos)
                    pontuacao_final_total = pontuacao_total_padrao + contribuicao_final_pontuacao_desafio
                    pontuacao_maxima_possivel_final = pontuacao_maxima_possivel_padrao + pontuacao_maxima_possivel_desafio

                    # Calcula o percentual final sobre o máximo possível ajustado
                    percentual_geral = (pontuacao_final_total / pontuacao_maxima_possivel_final) * 100 if pontuacao_maxima_possivel_final > 0 else 0
                    limiar_aprovacao = 65.0 # Limiar de aprovação em percentual

                    # Exibição dos Resultados
                    st.metric("Questões Padrão Respondidas", f"{perguntas_padrao_respondidas} / {num_perguntas_padrao_geradas}")
                    st.metric("Pontuação Total (Padrão - sem desafio)", f"{pontuacao_total_padrao:.1f} / {pontuacao_maxima_possivel_padrao:.1f}")

                    # Exibe detalhes da avaliação do desafio, se houver
                    if indice_pergunta_desafio != -1:
                        st.markdown("---")
                        st.write("**Avaliação da Pergunta Desafio:**")
                        if desafio_respondido:
                            texto_resposta_desafio = resposta_desafio
                            texto_pontuacao_desafio = f"{pontuacao_desafio:.1f}"
                            # Mostra a avaliação, a pontuação base e a contribuição ajustada (com peso)
                            st.metric("Sua Avaliação (Desafio)", texto_resposta_desafio, delta=f"{texto_pontuacao_desafio} (Contribuição: {contribuicao_final_pontuacao_desafio:.1f})", delta_color="off")
                        else:
                            st.info("Pergunta desafio não avaliada.")
                        st.markdown("---")

                    # Exibe o resultado final consolidado
                    st.metric("Pontuação Final Ajustada (com peso do desafio)", f"{pontuacao_final_total:.1f} / {pontuacao_maxima_possivel_final:.1f}")
                    st.metric("Percentual Final (sobre máx. possível ajustado)", f"{percentual_geral:.2f}%")

                    # Determina e exibe se foi aprovado ou reprovado
                    if percentual_geral >= limiar_aprovacao:
                        st.success(f"APROVADO(A)! (Atingiu {percentual_geral:.2f}% >= {limiar_aprovacao}%)")
                    else:
                        st.error(f"REPROVADO(A). (Atingiu {percentual_geral:.2f}% < {limiar_aprovacao}%)")

                else:
                    # Aviso se nenhuma pergunta foi respondida
                    st.warning("Nenhuma pergunta foi respondida ainda para calcular o resultado.")


        # Mensagem de erro se o quiz foi marcado como gerado, mas não há perguntas
        elif st.session_state.get('quiz_gerado', False) and not st.session_state.get('perguntas'):
             st.error("Não foi possível gerar as perguntas. Verifique os logs ou a resposta da API.")
        # --- Fim da Seção de Exibição do Quiz ---

    # --- Conteúdo da Aba Documentação (inalterado) ---
    with tab_documentacao:
        st.header("Documentação do Gerador de Avaliação Técnica")
        # ... (código da documentação inalterado) ...
        st.markdown("""
        Esta aplicação permite gerar e realizar avaliações técnicas personalizadas com base em descrições de vagas ou campos estruturados.

        **Funcionalidades Principais:**

        *   **Geração de Perguntas:** Cria perguntas técnicas relevantes para uma vaga específica usando a API Generativa do Google (Gemini).
        *   **Configuração Flexível:** Permite definir a vaga usando campos (Profissão, Conhecimentos, Senioridade), texto livre ou selecionando vagas pré-definidas (futuro).
        *   **Opções Avançadas:**
            *   Definir o número de perguntas padrão.
            *   Incluir uma pergunta "desafio" (problema/solução) com peso diferenciado na pontuação.
            *   Permitir ou não exemplos de código nas respostas esperadas.
        *   **Interface de Avaliação:** Apresenta as perguntas geradas com as respostas esperadas e botões para o avaliador classificar a resposta do candidato.
        *   **Cálculo de Resultado:** Calcula a pontuação final com base nas avaliações, aplicando peso dobrado para a pergunta desafio (se respondida de forma incompleta ou completa) e indica aprovação ou reprovação.
        *   **Exportação em PDF:** Gera dois arquivos PDF: um com as perguntas (para o candidato) e outro com as perguntas e respostas esperadas (para o avaliador).

        **Como Usar:**

        1.  **Configure a Vaga:**
            *   Escolha o método de entrada: "Usar Campos Estruturados", "Descrever a Vaga Livremente" ou "Selecionar Vagas".
            *   Se usar campos ou texto livre, preencha as informações. Use a opção "Outro (digitar)" se necessário.
            *   A opção "Selecionar Vagas" ainda não está implementada.
            *   (Opcional) Adicione detalhes adicionais no campo correspondente (para métodos estruturado/livre).
        2.  **Defina as Opções de Geração:**
            *   Ajuste o número de "Perguntas Padrão".
            *   Marque "Incluir Pergunta Desafio?" se desejar.
            *   Marque "Permitir Código nas Respostas?" se relevante.
        3.  **Gere as Perguntas:** Clique no botão "Gerar Perguntas da Avaliação". Aguarde a API processar a solicitação. (Este botão estará desabilitado se "Selecionar Vagas" estiver ativo).
        4.  **Realize a Avaliação:**
            *   As perguntas e respostas esperadas serão exibidas.
            *   Para cada pergunta, avalie a resposta do candidato usando os botões:
                *   **Não sei a resposta:** (0 pontos) O candidato não soube responder.
                *   **Errou a resposta:** (-1 ponto) A resposta está incorreta.
                *   **Resposta incompleta:** (0.5 pontos) A resposta está parcialmente correta ou falta profundidade.
                *   **Resposta completa:** (1 ponto) A resposta está correta e completa.
        5.  **Calcule o Resultado:** Após avaliar todas as perguntas desejadas, clique em "Calcular Resultado Final".
            *   A pontuação total, o percentual e o status (Aprovado/Reprovado) serão exibidos.
            *   **Importante:** A pergunta desafio, se incluída e respondida como "Incompleta" ou "Completa", tem sua pontuação (0.5 ou 1) dobrada (para 1 ou 2) no cálculo final, aumentando seu peso na avaliação.
        6.  **Gere os PDFs:** Use os botões "Gerar PDF das Perguntas" e "Gerar PDF das Respostas" para baixar os documentos.

        **Tecnologias Utilizadas:**

        *   **Streamlit:** Para a interface web interativa.
        *   **Google Gemini API:** Para a geração de conteúdo (perguntas e respostas).
        *   **FPDF (fpdf2):** Para a criação dos arquivos PDF.
        *   **Markdown:** Para formatação de texto.
        """)


# Ponto de entrada da aplicação
if __name__ == "__main__":
    # Inicializa estados da sessão que controlam a lógica da UI, se ainda não existirem
    # ... (código de inicialização inalterado) ...
    if 'quiz_gerado' not in st.session_state: st.session_state.quiz_gerado = False
    if 'incluir_pergunta_desafio' not in st.session_state: st.session_state.incluir_pergunta_desafio = False
    if 'permitir_codigo_na_resposta' not in st.session_state: st.session_state.permitir_codigo_na_resposta = False
    if 'max_perguntas_padrao' not in st.session_state: st.session_state.max_perguntas_padrao = 20
    # 'mostrar_resultados' é controlado pelo clique do botão, não inicializado aqui

    exibir_quiz() # Chama a função principal para renderizar a página
