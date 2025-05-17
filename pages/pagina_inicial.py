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

## Módulo: Ranking de Vagas

Este módulo, intitulado "**Ranking de Vagas**", é uma ferramenta interativa projetada para auxiliar no processo de recrutamento, permitindo a classificação de candidatos para vagas de emprego específicas.

Ele oferece duas modalidades principais para gerar rankings:

### Ranking com Dados Externos:

*   O usuário pode baixar um **template em Excel** para preencher com os dados dos candidatos (ID, nome, senioridade, currículo).
*   Em seguida, faz o **upload dessa planilha** preenchida.
*   O sistema **valida o arquivo** (verificando colunas obrigatórias, dados vazios ou nulos) e exibe os dados carregados de forma paginada.
*   O usuário insere a **descrição da vaga** desejada.
*   É possível definir quantos dos **melhores candidatos** devem ser retornados no ranking.
*   Ao clicar em "**Criar Ranking**", a ferramenta processa as informações e apresenta uma lista classificada dos candidatos mais adequados para a vaga, com base na descrição fornecida e nos currículos.

### Ranking com Dados Internos:

*   Esta modalidade é destinada a classificar candidatos utilizando **dados já existentes em um sistema interno** da empresa (atualmente, parece usar dados simulados ou de uma base interna).
*   O usuário também insere a **descrição da vaga**.
*   Define o **número de candidatos** a serem retornados.
*   Ao clicar em "**Criar Ranking**", obtém a lista classificada.

Além da funcionalidade principal de ranking, a página possui uma aba de "**Documentação**" que explica em detalhes como utilizar o módulo, incluindo os passos para upload de arquivos, preenchimento da descrição da vaga e interpretação dos resultados.

Em resumo, o "Ranking de Vagas" visa **otimizar a triagem de candidatos**, fornecendo uma classificação baseada na adequação de seus perfis a uma determinada vaga.

## Módulo: Gerador de Avaliação Técnica

Este módulo, intitulado "**Gerador de Avaliação Técnica**", complementa o processo de seleção, permitindo a criação e aplicação de testes técnicos personalizados.

Suas principais funcionalidades incluem:

### Geração de Perguntas Personalizadas:

*   **Configuração da Vaga:** Permite definir o perfil da vaga através de:
    *   **Campos Estruturados:** Selecionando profissão, conhecimentos/tecnologias e nível de senioridade em listas pré-definidas ou inserindo valores personalizados.
    *   **Texto Livre:** Descrevendo a vaga detalhadamente em um campo de texto.
*   **Opções de Geração:**
    *   Definir a **quantidade de perguntas** padrão desejadas.
    *   Opcionalmente, incluir uma **pergunta "desafio"** (problema/solução), que possui um peso maior na avaliação.
    *   Especificar se as **respostas esperadas devem incluir exemplos de código**.
*   **Integração com IA Generativa:** Utiliza uma API (como Google Gemini) para gerar perguntas e respostas relevantes com base nas configurações da vaga.

### Interface de Avaliação Interativa:

*   Após a geração, as perguntas e suas respectivas respostas esperadas são exibidas.
*   O avaliador pode classificar a resposta de um candidato para cada pergunta utilizando botões intuitivos:
    *   **Não sabe a resposta**
    *   **Errou a resposta**
    *   **Resposta incompleta**
    *   **Resposta completa**

### Cálculo de Resultados e Feedback:

*   Com base nas classificações, o sistema calcula uma **pontuação final** para o candidato.
*   A pergunta "desafio", se utilizada e respondida de forma incompleta ou completa, tem sua pontuação dobrada, refletindo sua maior complexidade.
*   Apresenta um **status final** (Aprovado/Reprovado) com base em um limiar de aprovação.

### Exportação em PDF:

*   Permite gerar e baixar dois tipos de arquivos PDF:
    *   Um contendo apenas as **perguntas** (ideal para ser enviado ao candidato).
    *   Outro contendo as **perguntas e as respostas esperadas** (para uso do avaliador).

Este módulo visa **padronizar e aprofundar a avaliação técnica** dos candidatos, fornecendo uma ferramenta flexível e automatizada para criar testes relevantes e objetivos.

Ambos os módulos, "Ranking de Vagas" e "Gerador de Avaliação Técnica", trabalham em conjunto para oferecer um suporte robusto e eficiente às diversas etapas do processo de recrutamento e seleção.
"""
)
