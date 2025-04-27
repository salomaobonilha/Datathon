import pandas as pd
import streamlit as st
import json
import apoio_tech as at

# Cores (usadas no CSS)
cor_nao_sei = "#D3D3D3"      # Cinza Claro
cor_errou = "#FF0000"        # Vermelho
cor_incompleta = "#FFA500"    # Laranja
cor_completa = "#008000"      # Verde
cor_selecao_borda = "#000080" # Azul Marinho (para indicar seleção)
cor_calcular = "#0000FF"      # Azul (para o botão calcular)
cor_texto_botao_claro = "black"
cor_texto_botao_escuro = "white"

@st.cache_data
def load_data(pergunta):
    # Limpeza simples do JSON retornado pela API
    raw_json = at.generate(pergunta)
    # Tenta remover ```json e ```, mas lida com casos onde podem não estar presentes
    clean_json = raw_json.strip().removeprefix("```json").removesuffix("```").strip()
    return clean_json

def quiz():
    # --- Injetar CSS para Cores dos Botões ---
    # Usamos seletores baseados na ordem das colunas e um ID para o botão final
    # Usamos !important para garantir que nossos estilos sobrescrevam os padrões do Streamlit
    # --- Injetar CSS para Cores dos Botões ---
    # Aplicar cores específicas APENAS quando o botão for selecionado (kind="primary")
    custom_css = f"""
    <style>
        /* Estilo base para botões de resposta (não selecionados) - Opcional */
        /* Você pode descomentar e ajustar se quiser um estilo base diferente do padrão */
        /*
        div[data-testid="stHorizontalBlock"] button {{
            border: 1px solid #cccccc !important;
            border-radius: 5px !important;
        }}
        */

        /* Coluna 1: Não sei - SELECIONADO */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="primary"] {{
            background-color: {cor_nao_sei} !important;
            color: {cor_texto_botao_claro} !important;
            border: 2px solid {cor_selecao_borda} !important; /* Borda de seleção */
            border-radius: 5px !important;
        }}
        /* Coluna 2: Errou - SELECIONADO */
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="primary"] {{
            background-color: {cor_errou} !important;
            color: {cor_texto_botao_escuro} !important;
            border: 2px solid {cor_selecao_borda} !important; /* Borda de seleção */
            border-radius: 5px !important;
        }}
        /* Coluna 3: Incompleta - SELECIONADO */
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) button[kind="primary"] {{
            background-color: {cor_incompleta} !important;
            color: {cor_texto_botao_claro} !important;
            border: 2px solid {cor_selecao_borda} !important; /* Borda de seleção */
            border-radius: 5px !important;
        }}
        /* Coluna 4: Completa - SELECIONADO */
        div[data-testid="stHorizontalBlock"] > div:nth-child(4) button[kind="primary"] {{
            background-color: {cor_completa} !important;
            color: {cor_texto_botao_escuro} !important;
            border: 2px solid {cor_selecao_borda} !important; /* Borda de seleção */
            border-radius: 5px !important;
        }}

        /* Removemos a regra genérica de borda/sombra para [kind="primary"] */
        /* As regras específicas por coluna acima cuidam disso */

        /* Estilo para o botão FINAL (Calcular Resultado) - Mantido */
        #final-button-container button {{
            background-color: {cor_calcular} !important;
            color: {cor_texto_botao_escuro} !important;
            border: 1px solid {cor_calcular} !important;
            border-radius: 5px !important;
            width: 100%; /* Ocupa a largura do container */
        }}
        /* Efeito hover para o botão final - Mantido */
        #final-button-container button:hover {{
            background-color: #0000CC !important; /* Azul um pouco mais escuro */
            border-color: #000099 !important;
        }}

        /* Efeito hover geral para botões de resposta (opcional) - Mantido */
        /* Pode ser útil para dar feedback mesmo nos não selecionados */
        div[data-testid="stHorizontalBlock"] button:hover {{
            opacity: 0.9;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # --- Inicialização do Estado da Sessão ---
    if 'questions' not in st.session_state:
        try:
            json_string = load_data("Vaga desenvolvedor python junior, com conhecimento em pandas, flask e django")
            st.session_state.questions = json.loads(json_string)
            num_questions = len(st.session_state.questions)
            st.session_state.scores = [None] * num_questions
            st.session_state.responses = [None] * num_questions
            st.session_state.selected_options = [None] * num_questions
        except json.JSONDecodeError as e:
            st.error(f"Erro ao decodificar JSON da API: {e}")
            st.error(f"String recebida: {json_string}")
            st.stop()
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
            st.stop()

    # Acessa as variáveis do estado da sessão
    questions = st.session_state.questions
    scores = st.session_state.scores
    responses = st.session_state.responses
    selected_options = st.session_state.selected_options
    num_questions = len(questions)

    st.title("Avaliação de Conhecimentos")

    traducao_nao_sei = "Não sei a resposta"
    traducao_errou = "Errou a resposta"
    traducao_incompleta = "Resposta incompleta"
    traducao_completa = "Resposta completa"

    # Função para atualizar o estado da sessão (sem alterações)
    def update_response(question_index, score, response, button_key):
        st.session_state.scores[question_index] = score
        st.session_state.responses[question_index] = response
        st.session_state.selected_options[question_index] = button_key

    # --- Loop das Perguntas ---
    for i, q in enumerate(questions):
        st.caption(f"Nível: {q.get('nivel', 'N/A')}")
        st.info(f"{i+1}. {q.get('pergunta', 'Pergunta não encontrada')}")
        st.markdown(f"**Resposta Esperada:**\n {q.get('resposta', 'Resposta não encontrada')}")

        # Define os botões e seus dados associados
        button_options = [
            {"label": traducao_nao_sei, "score": 0, "key_prefix": "nsr"},
            {"label": traducao_errou, "score": -1, "key_prefix": "er"},
            {"label": traducao_incompleta, "score": 0.5, "key_prefix": "ri"},
            {"label": traducao_completa, "score": 1, "key_prefix": "rc"},
        ]

        cols = st.columns(len(button_options)) # Cria colunas dinamicamente

        for idx, option in enumerate(button_options):
            with cols[idx]:
                button_key = f"{option['key_prefix']}_{i}"
                # Determina o tipo do botão baseado na seleção atual (primary/secondary)
                # O CSS vai cuidar da cor de fundo e da borda de seleção para 'primary'
                button_type = "primary" if selected_options[i] == button_key else "secondary"

                # Cria o botão usando st.button
                if st.button(option["label"], key=button_key, type=button_type, use_container_width=True):
                    update_response(i, option["score"], option["label"], button_key)
                    # Força o rerun para atualizar a aparência dos botões imediatamente
                    st.rerun()
        st.divider() # Adiciona um separador entre as perguntas

    # --- Cálculo e Exibição do Resultado ---
    # Envolve o botão em um container com ID para aplicar o CSS específico
    st.markdown('<div id="final-button-container">', unsafe_allow_html=True)
    calculate_clicked = st.button(
        "Calcular Resultado Final",
        key="calcular_final",
        use_container_width=True # Faz o botão ocupar a largura do container
    )
    st.markdown('</div>', unsafe_allow_html=True)


    if calculate_clicked:
        # Filtra apenas scores que não são None (perguntas respondidas)
        valid_scores = [s for s in scores if s is not None]
        answered_questions = len(valid_scores)

        if answered_questions > 0:
            total_score = sum(valid_scores)
            percentage_overall = (total_score / num_questions) * 100 if num_questions > 0 else 0
            approval_threshold = 65.0

            st.subheader("Resultado da Avaliação")
            
            st.metric("Pontuação Total", f"{total_score:.1f} / {answered_questions:.1f} (Máx. nas respondidas)")
            st.metric("Percentual de Acerto (Geral)", f"{percentage_overall:.2f}%")
            st.metric("Questões Respondidas", f"{answered_questions} / {num_questions}")

            if percentage_overall >= approval_threshold:
                st.success(f"APROVADO(A)! (Atingiu {percentage_overall:.2f}% >= {approval_threshold}%)")
            else:
                st.error(f"REPROVADO(A). (Atingiu {percentage_overall:.2f}% < {approval_threshold}%)")

            # Opcional: Mostrar detalhes das respostas
            st.write("Respostas Dadas:")
            results_data = []
            for idx, q in enumerate(questions):
                 results_data.append({
                     "Pergunta": q.get('pergunta', 'N/A'),
                     "Sua Resposta": responses[idx] if responses[idx] is not None else "Não respondida",
                     "Pontuação": scores[idx] if scores[idx] is not None else "N/A"
                 })
            st.dataframe(pd.DataFrame(results_data), use_container_width=True)

        else:
            st.warning("Nenhuma pergunta foi respondida ainda.")

if __name__ == "__main__":
    quiz()
