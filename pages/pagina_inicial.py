import streamlit as st
st.title("Pagina Inicial")


st.markdown(
    """
Esta é uma plataforma multifuncional de apoio ao recrutamento, oferecendo ferramentas para classificar candidatos e gerar avaliações técnicas personalizadas.

## Índice

*   [Módulo: Ranking de Vagas](#modulo-ranking-de-vagas)
    *   [Ranking com Dados Externos](#ranking-com-dados-externos)
    *   [Ranking com Dados Internos](#ranking-com-dados-internos)
*   [Módulo: Gerador de Avaliação Técnica](#modulo-gerador-de-avaliacao-tecnica)
    *   [Geração de Perguntas Personalizadas](#geracao-de-perguntas-personalizadas)
    *   [Interface de Avaliação Interativa](#interface-de-avaliacao-interativa)
    *   [Cálculo de Resultados e Feedback](#calculo-de-resultados-e-feedback)
    *   [Exportação em PDF](#exportacao-em-pdf)



---

## Módulo: Ranking de Vagas (Explicação)

O módulo "**Ranking de Vagas**" é uma ferramenta desenvolvida para otimizar o processo de recrutamento, classificando candidatos com base na sua adequação a uma vaga específica. Ele utiliza um modelo de recomendação e inteligência artificial para processar as informações.

### Principais Componentes e Funcionamento:

1.  **Fonte de Dados dos Candidatos:**
    *   **Dados Externos (Upload Excel):**
        *   Permite o carregamento de candidatos através de uma planilha Excel.
        *   Um **template (`template_candidatos.xlsx`)** é fornecido, especificando as colunas necessárias: `id_candidato`, `nome_candidato`, `senioridade`, `curriculo`, e `informacoes_adicionais`.
        *   O sistema realiza **validações** no arquivo carregado, verificando:
            *   A presença das colunas obrigatórias.
            *   Se a planilha está vazia.
            *   A existência de dados nulos nas colunas obrigatórias. Em caso de nulos, exibe um resumo e interrompe o processo.
        *   Os dados validados são exibidos em uma tabela paginada.
    *   **Dados Internos (Sistema):**
        *   Carrega candidatos de uma base de dados interna
        *   Os dados JSON são processados: colunas JSON aninhadas são normalizadas
        *   Um campo `curriculo` consolidado é criado, agregando informações de diversas colunas relevantes.        
        *   Uma amostra dos dados internos pode ser visualizada.

2.  **Definição das Informações da Vaga:**
    *   Após o carregamento dos candidatos, o usuário fornece os detalhes da vaga:
        *   **Descrição Manual:** Um campo de texto livre para inserir a descrição, requisitos e responsabilidades.
        *   **Seleção de Vaga Existente:**
            *   Carrega vagas pré-definidas.
            *   O usuário seleciona uma vaga, e sua descrição completa incluindo atividades e competências.

3.  **Geração das Recomendações:**
    *   O usuário define o número de candidatos a serem recomendados (top N).
    *   Ao acionar a geração:        
        *   O modelo de recomendação e os dados dos candidatos são carregados.
        *   A **descrição da vaga é otimizada** que usa uma IA para refinar o texto com foco em habilidades técnicas, visando melhorar a precisão do matching.
        *   O sistema Calcula as **similaridades** (usando embeddings TF-IDF dos currículos e da vaga processada) entre os currículos e a descrição da vaga otimizada.

4.  **Exibição dos Resultados:**
    *   Os candidatos mais compatíveis são exibidos em uma tabela.
    *   A coluna "Similaridade" é apresentada como uma barra de progresso, indicando o grau de aderência do candidato à vaga.
    *   As colunas exibidas são ajustadas dependendo da fonte de dados (interna ou externa).

Este módulo visa, portanto, automatizar e refinar a triagem inicial de candidatos, fornecendo uma lista classificada baseada em compatibilidade semântica.

## Módulo: Gerador de Avaliação Técnica (Explicação)

O módulo "**Gerador de Avaliação Técnica**" é uma ferramenta projetada para criar e aplicar avaliações técnicas personalizadas, utilizando inteligência artificial (API Gemini) para gerar perguntas e respostas.

### Principais Componentes e Funcionamento:

1.  **Configuração da Vaga para Geração de Perguntas:**
    *   O sistema oferece três métodos para definir o contexto da vaga:
        *   **Campos Estruturados:**
            *   O usuário seleciona/insere: Profissão, Conhecimentos/Tecnologias e Nível de Senioridade.
            *   Listas pré-definidas.
            *   Permite a inserção de valores personalizados ("Outro (digitar)").
            *   Um campo para "Detalhes Adicionais da Vaga" permite complementar a informação.
        *   **Descrição Livre:** O usuário insere uma descrição textual completa da vaga.
        *   **Seleção de Vagas Existentes:**
            *   Carrega vagas do arquivo fornecida pela empresa.
            *   Exibe informações da vaga selecionada (título, senioridade, áreas de atuação, resumo).
            *   *Nota: A geração direta de perguntas a partir desta seleção está desabilitada; o usuário deve usar os detalhes visualizados para preencher os outros modos.*
    *   As informações coletadas são usadas para construir o prompt para a API Gemini.

2.  **Opções de Geração de Perguntas:**
    *   **Quantidade de Perguntas Padrão:** Definida por um slider (mínimo 3). O limite máximo é 30, ou 20 se a opção de código nas respostas estiver ativa.
    *   **Pergunta Desafio:** Opcionalmente, pode-se incluir uma pergunta de maior complexidade (problema/solução), que terá peso dobrado na avaliação.
    *   **Código nas Respostas:** Permite especificar se as respostas esperadas devem incluir exemplos de código.

3.  **Geração de Perguntas via API Gemini:**
    *   Um prompt detalhado é enviado à API Gemini, contendo a descrição da vaga, quantidade de perguntas, inclusão de desafio, permissão de código, e instruções sobre o formato JSON esperado e o nível de senioridade.
    *   A API retorna uma string JSON com um array de objetos, cada um contendo "pergunta", "resposta", "nivel" e, opcionalmente, "tipo": "desafio".
    *   A função `carregar_dados_api` no módulo lida com a chamada à API e o parsing da resposta JSON.

4.  **Interface de Avaliação:**
    *   As perguntas geradas e suas respostas esperadas são exibidas.
    *   O avaliador classifica a resposta do candidato para cada pergunta usando botões: "Não sabe a resposta" (0 pts), "Errou a resposta" (-1 pt), "Resposta incompleta" (0.5 pts), "Resposta completa" (1 pt).

5.  **Cálculo de Resultados:**
    *   A pontuação total é calculada com base nas avaliações.
    *   A pergunta desafio, se respondida como "Incompleta" ou "Completa", tem sua pontuação (0.5 ou 1) dobrada (para 1 ou 2).
    *   Um status final (Aprovado/Reprovado) é determinado com base em um limiar de aprovação (atualmente 65%).

6.  **Exportação em PDF (usando FPDF):**
    *   A função de geração de PDF cria dois tipos de documentos:
        *   Um PDF contendo apenas as **perguntas**.
        *   Um PDF contendo as **perguntas e as respostas esperadas**.
    *   O conteúdo das perguntas/respostas é renderizado no PDF.

Este módulo visa padronizar e aprofundar a avaliação técnica, oferecendo flexibilidade na criação de testes e automatizando parte do processo de avaliação.

Ambos os módulos, "Ranking de Vagas" e "Gerador de Avaliação Técnica", trabalham em conjunto para oferecer um suporte robusto e eficiente às diversas etapas do processo de recrutamento e seleção.
"""
)
