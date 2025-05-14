import re
import os
import json
import markdown
import pandas as pd
from fpdf import FPDF
import streamlit as st
from apoio_tech import generate


COR_NAO_SEI = "#D3D3D3"
COR_ERROU = "#FF0000"
COR_INCOMPLETA = "#FFA500"
COR_COMPLETA = "#008000"
COR_SELECAO_BORDA = "#000080"
COR_CALCULAR = "#0000FF"
COR_TEXTO_BOTAO_CLARO = "black"
COR_TEXTO_BOTAO_ESCURO = "white"

TRADUCAO_NAO_SABE = "Não sabe a resposta"
TRADUCAO_ERROU = "Errou a resposta"
TRADUCAO_INCOMPLETA = "Resposta incompleta"
TRADUCAO_COMPLETA = "Resposta completa"
OPCAO_OUTRO_ROTULO = "Outro (digitar)"
METODO_ENTRADA_ESTRUTURADO = "Usar Campos Estruturados"
METODO_ENTRADA_TEXTO_LIVRE = "Descrever a Vaga Livremente"
METODO_ENTRADA_SELECIONAR_VAGA = "Selecionar Vagas"
TIPO_PERGUNTA_DESAFIO = "desafio"

# O CSS para ocultar a navegação padrão e a geração do menu
# são removidos para usar a navegação padrão do Streamlit.
# App.gerar_menu_horizontal() # Esta linha não é mais necessária

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
    with st.spinner(f"Gerando perguntas com base em: '{prompt_api[:100]}...'"):
        resposta_api_bruta = generate(prompt_api)
        print(f"Prompt enviado para API: {prompt_api}")

    print(f"Resposta da API: {resposta_api_bruta}")
    if not resposta_api_bruta:
        st.error("A API não retornou resposta.")
        return None

    try:
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


class PDF(FPDF):
    """
    Classe personalizada herdando de FPDF para definir cabeçalho e rodapé
    com tratamento de erro básico para codificação de caracteres.
    """
    def header(self):
        """Define o cabeçalho do PDF com o título."""
        try:
            self.set_font(self.font_family, 'B', 12)            
            titulo_codificado = self.title.encode('latin-1', 'replace').decode('latin-1')
            self.cell(0, 10, titulo_codificado, 0, 1, 'C')
        except Exception as e:
            print(f"Erro ao definir header do PDF: {e}")
            self.cell(0, 10, 'Titulo PDF', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        """Define o rodapé do PDF com o número da página."""
        self.set_y(-15)
        try:
            self.set_font(self.font_family, 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C') # Centraliza número da página
        except Exception as e:
            print(f"Erro ao definir footer do PDF: {e}")

def atualizar_limite_perguntas():    
    """Callback para ajustar o número de perguntas ao mudar a permissão de código."""
    permitir_codigo = st.session_state.get('check_codigo_resposta', False)
    limit_max_com_codigo = 20
    if permitir_codigo:
        st.session_state.max_perguntas_padrao = limit_max_com_codigo
        quantidade_desejada_atual = st.session_state.get('numero_perguntas_desejadas', False)
        if quantidade_desejada_atual > limit_max_com_codigo:
            st.session_state.numero_perguntas_desejadas = limit_max_com_codigo
    else:
        st.session_state.max_perguntas_padrao = 30

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
    pdf_doc.font_family = 'Arial'

    try:
        pdf_doc.set_font(pdf_doc.font_family, '', 11)
    except Exception as e:
        st.error(f"Erro ao definir a fonte padrão para o PDF: {e}")

    pdf_doc.add_page()
    markdown_parser = markdown.Markdown(extensions=['fenced_code', 'codehilite'])

    for item_pdf in itens_pdf:
        try:
            pdf_doc.set_font(pdf_doc.font_family, 'B', 11)
            texto_prefixo = item_pdf.get('prefix', '')
            if '**' in texto_prefixo or '*' in texto_prefixo or '`' in texto_prefixo:
                 html_prefixo = markdown_parser.convert(texto_prefixo)
                 html_prefixo = re.sub(r'(<pre.*?><code.*?>)(.*?)(</code></pre>)',
                                      lambda m: m.group(1) + m.group(2).replace('\n', '<br>\n') + m.group(3),
                                      html_prefixo, flags=re.DOTALL)
                 pdf_doc.write_html(html_prefixo)
            else:
                 pdf_doc.multi_cell(0, 7, texto_prefixo.encode('latin-1', 'replace').decode('latin-1'))
            pdf_doc.set_font(pdf_doc.font_family, '', 11)
        except Exception as e:
             print(f"Erro ao escrever prefixo no PDF: {e} - Texto: {item_pdf.get('prefix', '')[:50]}...")
             pdf_doc.multi_cell(0, 7, "[Erro ao renderizar prefixo]")

        try:
            texto_item_md = item_pdf.get('text', '')
            texto_item_html = markdown_parser.convert(texto_item_md)

            
            
            
            texto_item_html_com_br = re.sub(r'(<pre.*?><code.*?>)(.*?)(</code></pre>)',
                                       lambda m: m.group(1) + m.group(2).replace('\n', '<br>\n') + m.group(3),
                                       texto_item_html, flags=re.DOTALL)

            pdf_doc.write_html(texto_item_html_com_br) 
            pdf_doc.ln(5) 
        except Exception as e:
             print(f"Erro ao escrever texto HTML no PDF: {e} - Texto MD: {texto_item_md[:50]}...")
             pdf_doc.multi_cell(0, 7, texto_item_md.encode('latin-1', 'replace').decode('latin-1'))
             pdf_doc.ln(5)

    try:        
        return pdf_doc.output(dest='B')
    except Exception as e:
        st.error(f"Erro ao gerar o arquivo PDF final: {e}")
        return b""



def exibir_quiz():
    """
    Função principal que renderiza a interface do Streamlit para gerar
    e realizar a avaliação técnica, agora com abas.
    """
    st.title("Gerador de Avaliação Técnica")

    st.markdown("""
    <style>
        div[data-baseweb="tab-list"] button[role="tab"] {
            font-size: 18px !important;
            font-weight: bold !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if 'pdf_perguntas_data' not in st.session_state: st.session_state.pdf_perguntas_data = None
    if 'pdf_respostas_data' not in st.session_state: st.session_state.pdf_respostas_data = None
    if 'pdf_perguntas_pronto' not in st.session_state: st.session_state.pdf_perguntas_pronto = False
    if 'pdf_respostas_pronto' not in st.session_state: st.session_state.pdf_respostas_pronto = False

    tab_sistema, tab_documentacao = st.tabs(["Sistema", "Documentação"])

    with tab_sistema:
        
        diretorio_script = f"{os.path.basename(__file__)}/../dataset"        
        base_profissoes = carregar_lista_json(os.path.join(diretorio_script, "profissoes.json"))
        base_linguagens = carregar_lista_json(os.path.join(diretorio_script, "linguagens.json"))
        base_senioridades = carregar_lista_json(os.path.join(diretorio_script, "senioridades.json"))        

        opcoes_profissoes = base_profissoes + [OPCAO_OUTRO_ROTULO]
        opcoes_linguagens = base_linguagens + [OPCAO_OUTRO_ROTULO]
        opcoes_senioridades = base_senioridades + [OPCAO_OUTRO_ROTULO]

        st.subheader("Configure a Vaga")

        if 'metodo_entrada' not in st.session_state: st.session_state.metodo_entrada = METODO_ENTRADA_ESTRUTURADO
        if 'descricao_vaga' not in st.session_state: st.session_state.descricao_vaga = ""

        st.session_state.metodo_entrada = st.radio(
            "Como deseja definir a vaga?",
            (METODO_ENTRADA_ESTRUTURADO, METODO_ENTRADA_TEXTO_LIVRE, METODO_ENTRADA_SELECIONAR_VAGA),
            key='radio_metodo_entrada', horizontal=True,
        )

        if st.session_state.metodo_entrada == METODO_ENTRADA_ESTRUTURADO:
            
            if 'profissao_selecionada' not in st.session_state: st.session_state.profissao_selecionada = opcoes_profissoes[0] if opcoes_profissoes else None            
            if 'profissao_personalizada' not in st.session_state: st.session_state.profissao_personalizada = ""
            if 'linguagens_selecionadas' not in st.session_state: st.session_state.linguagens_selecionadas = [opcoes_linguagens[0]] if opcoes_linguagens else []
            if 'linguagens_personalizadas' not in st.session_state: st.session_state.linguagens_personalizadas = ""
            if 'senioridade_selecionada' not in st.session_state: st.session_state.senioridade_selecionada = opcoes_senioridades[0] if opcoes_senioridades else None
            if 'senioridade_personalizada' not in st.session_state: st.session_state.senioridade_personalizada = ""
            if 'detalhes_opcionais' not in st.session_state: st.session_state.detalhes_opcionais = ""

            coluna1, coluna2, coluna3 = st.columns(3)
            with coluna1:
                profissao_anterior = st.session_state.profissao_selecionada
                st.session_state.profissao_selecionada = st.selectbox("Profissão:", opcoes_profissoes, index=opcoes_profissoes.index(st.session_state.profissao_selecionada) if st.session_state.profissao_selecionada in opcoes_profissoes else 0, key='select_profissao')
                if st.session_state.profissao_selecionada != OPCAO_OUTRO_ROTULO and profissao_anterior == OPCAO_OUTRO_ROTULO: st.session_state.profissao_personalizada = ""
                if st.session_state.profissao_selecionada == OPCAO_OUTRO_ROTULO: st.session_state.profissao_personalizada = st.text_input("Digite a profissão:", value=st.session_state.profissao_personalizada, key='input_profissao_outro')
            with coluna2:
                linguagens_anteriores = st.session_state.linguagens_selecionadas
                st.session_state.linguagens_selecionadas = st.multiselect("Conhecimentos:", opcoes_linguagens, default=st.session_state.linguagens_selecionadas, key='multiselect_linguagens')
                if OPCAO_OUTRO_ROTULO not in st.session_state.linguagens_selecionadas and OPCAO_OUTRO_ROTULO in linguagens_anteriores: st.session_state.linguagens_personalizadas = ""
                if OPCAO_OUTRO_ROTULO in st.session_state.linguagens_selecionadas: st.session_state.linguagens_personalizadas = st.text_input("Outros conhecimentos (separados por vírgula):", value=st.session_state.linguagens_personalizadas, key='input_linguagens_outro')
            with coluna3:
                senioridade_anterior = st.session_state.senioridade_selecionada
                st.session_state.senioridade_selecionada = st.selectbox("Senioridade:", opcoes_senioridades, index=opcoes_senioridades.index(st.session_state.senioridade_selecionada) if st.session_state.senioridade_selecionada in opcoes_senioridades else 0, key='select_senioridade')
                if st.session_state.senioridade_selecionada != OPCAO_OUTRO_ROTULO and senioridade_anterior == OPCAO_OUTRO_ROTULO: st.session_state.senioridade_personalizada = ""
                if st.session_state.senioridade_selecionada == OPCAO_OUTRO_ROTULO: st.session_state.senioridade_personalizada = st.text_input("Digite a senioridade:", value=st.session_state.senioridade_personalizada, key='input_senioridade_outro')

            st.session_state.detalhes_opcionais = st.text_area(
                "Detalhes Adicionais da Vaga (Opcional):",
                value=st.session_state.detalhes_opcionais,
                max_chars=500,
                height=100,
                key='text_area_detalhes_opcionais',
                help="Informe aqui outros requisitos, responsabilidades ou contexto relevante sobre a vaga."
            )

        elif st.session_state.metodo_entrada == METODO_ENTRADA_TEXTO_LIVRE:
            st.session_state.descricao_vaga = st.text_area(
                "Descreva a vaga desejada:",
                value=st.session_state.descricao_vaga,
                max_chars=1500,
                height=200,
                key='text_area_vaga'
            )

        elif st.session_state.metodo_entrada == METODO_ENTRADA_SELECIONAR_VAGA:
            st.info("(Ainda não implementado)")

        st.markdown("---")
        st.subheader("Opções de Geração")
        coluna_opcoes1, coluna_opcoes2, coluna_opcoes3 = st.columns(3)

        with coluna_opcoes1:
            if 'numero_perguntas_desejadas' not in st.session_state: st.session_state.numero_perguntas_desejadas = 10
            st.session_state.numero_perguntas_desejadas = st.slider(
                "Quantidade de perguntas:",
                min_value=3, max_value=st.session_state.max_perguntas_padrao,
                value=st.session_state.numero_perguntas_desejadas,
                step=1,
                key='num_perguntas',
                help="Número de perguntas no formato padrão (pergunta/resposta/nível)."
            )

        with coluna_opcoes2:
            if 'check_desafio' not in st.session_state: st.session_state.check_desafio = False
            st.write("")
            st.write("")
            st.checkbox(
                "Incluir Pergunta Desafio?",
                value=st.session_state.check_desafio,
                key='check_desafio',
                help="Adiciona uma pergunta sobre um problema técnico com 3 possíveis soluções."
            )

        with coluna_opcoes3:
            
            
            if 'check_codigo_resposta' not in st.session_state: st.session_state.check_codigo_resposta = False
            st.write("") 
            st.write("") 
            st.checkbox( 
                "Permitir Código nas Respostas?",
                value=st.session_state.check_codigo_resposta,
                key='check_codigo_resposta',
                on_change=atualizar_limite_perguntas,
                help="Marque se deseja que as respostas esperadas possam incluir exemplos de código."
            )
            if st.session_state.check_codigo_resposta:
                st.warning("Limite de 20 perguntas padrão quando o código é permitido nas respostas.")

        botao_gerar_desabilitado = st.session_state.metodo_entrada == METODO_ENTRADA_SELECIONAR_VAGA

        if st.button("Gerar Perguntas da Avaliação", type="primary", disabled=botao_gerar_desabilitado):
            numero_perguntas_padrao = st.session_state.numero_perguntas_desejadas
            incluir_desafio = st.session_state.check_desafio
            permitir_codigo = st.session_state.check_codigo_resposta
            prompt_para_api = ""
            entrada_valida = True            
            informacao_vaga = ""
            texto_detalhes_opcionais = ""

            
            if st.session_state.metodo_entrada == METODO_ENTRADA_ESTRUTURADO:
            
                profissao_final = st.session_state.profissao_personalizada.strip() if st.session_state.profissao_selecionada == OPCAO_OUTRO_ROTULO else st.session_state.profissao_selecionada
                senioridade_final = st.session_state.senioridade_personalizada.strip() if st.session_state.senioridade_selecionada == OPCAO_OUTRO_ROTULO else st.session_state.senioridade_selecionada
                conhecimentos_finais = [lang for lang in st.session_state.linguagens_selecionadas if lang != OPCAO_OUTRO_ROTULO] if st.session_state.linguagens_selecionadas else []
                if OPCAO_OUTRO_ROTULO in st.session_state.linguagens_selecionadas and st.session_state.linguagens_personalizadas.strip():
                    linguagens_personalizadas_lista = [lang.strip() for lang in st.session_state.linguagens_personalizadas.split(',') if lang.strip()]
                    conhecimentos_finais.extend(linguagens_personalizadas_lista)
                conhecimentos_finais = list(dict.fromkeys(conhecimentos_finais))
                conhecimentos_str = ", ".join(conhecimentos_finais)
                texto_detalhes_opcionais = st.session_state.detalhes_opcionais.strip()

                
                if not profissao_final: st.warning("Selecione ou digite a Profissão."); entrada_valida = False
                if not senioridade_final: st.warning("Selecione ou digite a Senioridade."); entrada_valida = False
                if not conhecimentos_str: st.warning("Selecione ou digite os Conhecimentos."); entrada_valida = False

                if entrada_valida:
                    informacao_vaga = f"para a vaga {profissao_final} {senioridade_final}, com conhecimento em {conhecimentos_str}"
                    if texto_detalhes_opcionais:
                        informacao_vaga += f". incluir tambem perguntas sobre: {texto_detalhes_opcionais}"


            elif st.session_state.metodo_entrada == METODO_ENTRADA_TEXTO_LIVRE:                 
                descricao_vaga_texto = st.session_state.descricao_vaga.strip()
                if not descricao_vaga_texto: st.warning("Descreva a vaga no campo de texto."); entrada_valida = False                
                elif len(descricao_vaga_texto) < 20: st.warning("Descrição da vaga muito curta."); entrada_valida = False

                if entrada_valida:
                    informacao_vaga = f"com base na seguinte descrição de vaga: '{descricao_vaga_texto}'"


            
            if not isinstance(numero_perguntas_padrao, int) or numero_perguntas_padrao < 3:                 
                 st.warning("Insira um número válido de perguntas padrão (mínimo 3)."); entrada_valida = False

            if entrada_valida and informacao_vaga:
                instrucao_codigo = "As respostas DEVEM incluir exemplos de código relevantes quando apropriado." if permitir_codigo else "As respostas devem focar em conceitos e definições, EVITANDO exemplos de código sempre que possível."

                if incluir_desafio:
                    prompt_para_api = (
                        f"Gere {numero_perguntas_padrao} perguntas técnicas padrão e com mais 1 pergunta desafio de problema/solução "
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

                if perguntas_carregadas is not None:
                     if len(perguntas_carregadas) != total_perguntas_esperado:
                         st.warning(f"A API gerou {len(perguntas_carregadas)} perguntas, mas foram solicitadas {total_perguntas_esperado}. Exibindo as perguntas geradas.")

                     st.session_state.perguntas = perguntas_carregadas
                     numero_real_perguntas = len(st.session_state.perguntas)
                     st.session_state.pontuacoes = [None] * numero_real_perguntas
                     st.session_state.respostas_avaliacao = [None] * numero_real_perguntas
                     st.session_state.opcoes_selecionadas = [None] * numero_real_perguntas
                     st.session_state.quiz_gerado = True
                     if 'mostrar_resultados' in st.session_state:
                         del st.session_state['mostrar_resultados']
                     st.rerun()
                else:                     
                     st.session_state.perguntas = []
                     st.session_state.quiz_gerado = False
                     if 'mostrar_resultados' in st.session_state:
                         del st.session_state['mostrar_resultados']


        st.divider()

        if st.session_state.get('quiz_gerado', False) and 'perguntas' in st.session_state and st.session_state.perguntas:

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

                .resposta-destaque {{
                    background-color: #e9ecef;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                    border: 1px solid #ced4da;
                }}
                .resposta-destaque pre {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                }}
            </style>
            """
            st.markdown(css_personalizado, unsafe_allow_html=True)

            st.header("Avaliação de Conhecimentos")


            perguntas = st.session_state.perguntas
            pontuacoes = st.session_state.pontuacoes
            respostas_avaliacao = st.session_state.respostas_avaliacao
            opcoes_selecionadas = st.session_state.opcoes_selecionadas

            def atualizar_resposta(indice_pergunta, pontuacao, resposta_avaliacao, chave_botao):
                """
                Atualiza o estado da sessão para uma pergunta específica quando um
                botão de avaliação é clicado.
                """
                st.session_state.pontuacoes[indice_pergunta] = pontuacao
                st.session_state.respostas_avaliacao[indice_pergunta] = resposta_avaliacao
                st.session_state.opcoes_selecionadas[indice_pergunta] = chave_botao
                if 'mostrar_resultados' in st.session_state:                    
                    del st.session_state['mostrar_resultados']

            
            for i, q in enumerate(perguntas):
                eh_desafio = q.get('tipo') == TIPO_PERGUNTA_DESAFIO

            
                texto_legenda = f"Nível: {q.get('nivel', 'N/A')}"
                if eh_desafio: texto_legenda += " (Desafio: Problema/Solução)"
                st.caption(texto_legenda)

            
                st.info(f"{i+1}. {q.get('pergunta', 'Pergunta/Problema não encontrado')}")

                st.markdown(f"**Resposta Esperada:**")
                resposta_bruta = q.get('resposta', 'Resposta/Soluções não encontrada')

                try:
                    st.markdown(resposta_bruta, unsafe_allow_html=True)
                except Exception as e:
                    print(f"Erro ao renderizar resposta Markdown: {e}")
                    st.markdown(f'<div class="resposta-destaque"><pre>{resposta_bruta}</pre></div>', unsafe_allow_html=True)                

                opcoes_botoes = [
                    {"label": TRADUCAO_NAO_SABE, "score": 0, "key_prefix": "nsr"},
                    {"label": TRADUCAO_ERROU, "score": -1, "key_prefix": "er"},
                    {"label": TRADUCAO_INCOMPLETA, "score": 0.5, "key_prefix": "ri"},
                    {"label": TRADUCAO_COMPLETA, "score": 1, "key_prefix": "rc"},
                ]
                colunas_botoes = st.columns(len(opcoes_botoes))
                for indice_botao, opcao_botao in enumerate(opcoes_botoes):
                    with colunas_botoes[indice_botao]:
                        chave_botao = f"{opcao_botao['key_prefix']}_{i}"
                        tipo_botao = "primary" if opcoes_selecionadas[i] == chave_botao else "secondary"
                        if st.button(opcao_botao["label"], key=chave_botao, type=tipo_botao, use_container_width=True):
                            atualizar_resposta(i, opcao_botao["score"], opcao_botao["label"], chave_botao)
                            st.rerun()
                st.divider()

            st.subheader("O que deseja fazer agora?") 

            coluna_calcular, coluna_pdf1, coluna_pdf2 = st.columns(3)

            with coluna_calcular:
                st.markdown('<div id="container-botao-final">', unsafe_allow_html=True)
                botao_calcular_clicado = st.button("Calcular Resultado Final", key="calcular_final", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if botao_calcular_clicado:
                    st.session_state['mostrar_resultados'] = True
                    
                    st.rerun()

            
            perguntas_para_pdf = []
            respostas_para_pdf = []
            
            if 'perguntas' in st.session_state and st.session_state.perguntas:
                for i, q in enumerate(st.session_state.perguntas):
                    texto_pergunta = q.get('pergunta', 'N/A')
                    texto_nivel = f"Nível: {q.get('nivel', 'N/A')}{' (Desafio)' if q.get('tipo') == TIPO_PERGUNTA_DESAFIO else ''}"
                    texto_resposta = q.get('resposta', 'N/A')

                    prefixo_perguntas_pdf = f"**{i+1}. Pergunta:** {texto_pergunta}\n"
                    perguntas_para_pdf.append({
                         "prefix": prefixo_perguntas_pdf,
                         "text": "Resposta:  <br><br><br><br><br><br><br><br><br>"
                    })

                    prefixo_respostas_pdf = f"**{i+1}. Pergunta:** {texto_pergunta}\n    *({texto_nivel})*"
                    respostas_para_pdf.append({
                        "prefix": prefixo_respostas_pdf,
                        "text": texto_resposta
                    })

            with coluna_pdf1:
                st.markdown('<div id="container-botao-pdf">', unsafe_allow_html=True)
                if st.button("Gerar PDF das Perguntas", key="prep_perguntas", use_container_width=True):
                    with st.spinner("Gerando PDF das perguntas..."):
                        if perguntas_para_pdf:
                            pdf_data = gerar_pdf("Perguntas da Avaliação", perguntas_para_pdf)
                            if pdf_data:
                                st.session_state.pdf_perguntas_data = pdf_data
                                st.session_state.pdf_perguntas_pronto = True
                                st.session_state.pdf_respostas_pronto = False 
                                st.rerun() 
                            else:
                                st.error("Falha ao gerar PDF das perguntas.")
                                st.session_state.pdf_perguntas_pronto = False
                        else:
                            st.warning("Não há perguntas carregadas para gerar o PDF.")
                            st.session_state.pdf_perguntas_pronto = False

                if st.session_state.get('pdf_perguntas_pronto', False) and st.session_state.get('pdf_perguntas_data'):
                    st.download_button(
                        label="⬇️ Baixar PDF das Perguntas",
                        data=bytes(st.session_state.pdf_perguntas_data),
                        file_name="perguntas_avaliacao.pdf",
                        mime="application/pdf",
                        key="download_perguntas_final",
                        use_container_width=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)    
                    

            with coluna_pdf2:
                st.markdown('<div id="container-botao-pdf">', unsafe_allow_html=True)
                if st.button("Gerar PDF das das Perguntas com Respostas", key="prep_respostas", use_container_width=True):
                    with st.spinner("Gerando PDF das respostas..."):
                        if respostas_para_pdf:
                            pdf_data = gerar_pdf("Respostas Esperadas da Avaliação", respostas_para_pdf)                            
                            if pdf_data:
                                st.session_state.pdf_respostas_data = pdf_data
                                st.session_state.pdf_respostas_pronto = True
                                st.session_state.pdf_perguntas_pronto = False 
                                st.rerun() 
                            else:
                                st.error("Falha ao gerar PDF das respostas.")
                                st.session_state.pdf_respostas_pronto = False
                        else:
                             st.warning("Não há respostas carregadas para gerar o PDF.")
                             st.session_state.pdf_respostas_pronto = False

                if st.session_state.get('pdf_respostas_pronto', False) and st.session_state.get('pdf_respostas_data'):
                    st.download_button(
                        label="⬇️ Baixar PDF das Perguntas e Respostas",
                        data=bytes(st.session_state.pdf_respostas_data),
                        file_name="respostas_avaliacao.pdf",
                        mime="application/pdf",
                        key="download_respostas_final",
                        use_container_width=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)
             
            if st.session_state.get('mostrar_resultados', False):
                pontuacoes_padrao = []
                pontuacao_desafio = None
                resposta_desafio = None
                num_perguntas_padrao_geradas = 0
                indice_pergunta_desafio = -1
                desafio_respondido_com_peso = False

                
                for i, q in enumerate(perguntas):
                     eh_pergunta_desafio = q.get('tipo') == TIPO_PERGUNTA_DESAFIO
                     if eh_pergunta_desafio:
                         indice_pergunta_desafio = i
                         if pontuacoes[i] is not None:
                             pontuacao_desafio = pontuacoes[i]
                             resposta_desafio = respostas_avaliacao[i]
                             if pontuacao_desafio > 0:
                                 desafio_respondido_com_peso = True
                     else:
                         num_perguntas_padrao_geradas += 1
                         if pontuacoes[i] is not None:
                             pontuacoes_padrao.append(pontuacoes[i])

                perguntas_padrao_respondidas = len(pontuacoes_padrao)
                desafio_respondido = pontuacao_desafio is not None

                if perguntas_padrao_respondidas > 0 or desafio_respondido:
                    st.subheader("Resultado da Avaliação")

                    pontuacao_total_padrao = sum(pontuacoes_padrao)
                    contribuicao_final_pontuacao_desafio = 0
                    pontuacao_maxima_possivel_padrao = num_perguntas_padrao_geradas
                    pontuacao_maxima_possivel_desafio = 0

                    if desafio_respondido:
                        if desafio_respondido_com_peso:
                            contribuicao_final_pontuacao_desafio = pontuacao_desafio * 2
                            pontuacao_maxima_possivel_desafio = 1 * 2
                        else:
                            contribuicao_final_pontuacao_desafio = pontuacao_desafio
                            pontuacao_maxima_possivel_desafio = 1

                    pontuacao_final_total = pontuacao_total_padrao + contribuicao_final_pontuacao_desafio
                    pontuacao_maxima_possivel_final = pontuacao_maxima_possivel_padrao + pontuacao_maxima_possivel_desafio

                    percentual_geral = (pontuacao_final_total / pontuacao_maxima_possivel_final) * 100 if pontuacao_maxima_possivel_final > 0 else 0
                    limiar_aprovacao = 65.0

                    st.metric("Questões Padrão Respondidas", f"{perguntas_padrao_respondidas} / {num_perguntas_padrao_geradas}")
                    st.metric("Pontuação Total (Padrão - sem desafio)", f"{pontuacao_total_padrao:.1f} / {pontuacao_maxima_possivel_padrao:.1f}")

                    if indice_pergunta_desafio != -1:
                        st.markdown("---")
                        st.write("**Avaliação da Pergunta Desafio:**")
                        if desafio_respondido:
                            texto_resposta_desafio = resposta_desafio
                            texto_pontuacao_desafio = f"{pontuacao_desafio:.1f}"
                            st.metric("Sua Avaliação (Desafio)", texto_resposta_desafio, delta=f"{texto_pontuacao_desafio} (Contribuição: {contribuicao_final_pontuacao_desafio:.1f})", delta_color="off")
                        else:
                            st.info("Pergunta desafio não avaliada.")
                        st.markdown("---")

                    
                    st.metric("Pontuação Final Ajustada (com peso do desafio)", f"{pontuacao_final_total:.1f} / {pontuacao_maxima_possivel_final:.1f}")
                    st.metric("Percentual Final (sobre máx. possível ajustado)", f"{percentual_geral:.2f}%")

                    if percentual_geral >= limiar_aprovacao:
                        st.success(f"APROVADO(A)! (Atingiu {percentual_geral:.2f}% >= {limiar_aprovacao}%)")
                    else:
                        st.error(f"REPROVADO(A). (Atingiu {percentual_geral:.2f}% < {limiar_aprovacao}%)")

                else:                    
                    st.warning("Nenhuma pergunta foi respondida ainda para calcular o resultado.")

        elif st.session_state.get('quiz_gerado', False) and not st.session_state.get('perguntas'):
             st.error("Não foi possível gerar as perguntas. Verifique os logs ou a resposta da API.")

    with tab_documentacao:        
        st.header("Documentação do Gerador de Avaliação Técnica")
        
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
                *   **Não sabe a resposta:** (0 pontos) O candidato não soube responder.
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

if __name__ == "__main__":
    if 'quiz_gerado' not in st.session_state: st.session_state.quiz_gerado = False
    if 'incluir_pergunta_desafio' not in st.session_state: st.session_state.incluir_pergunta_desafio = False
    if 'permitir_codigo_na_resposta' not in st.session_state: st.session_state.permitir_codigo_na_resposta = False
    if 'max_perguntas_padrao' not in st.session_state: st.session_state.max_perguntas_padrao = 30
    
    
    exibir_quiz()
 
    
    
  
    
