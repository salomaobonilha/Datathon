import streamlit as st

st.set_page_config(layout="wide")
# Logo apenas na sidebar expandida
st.markdown("""
<style>
    /* Container principal da sidebar */
    [data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    /* Posicionamento do logo */
    [data-testid="stSidebar"] img {
        order: -1;  /* Coloca o logo primeiro */
        align-self: flex-start;
        margin-top: -30px;
        margin-left: -15px;
        max-width: 250px !important;
    }

    /* Ajuste do menu de navegação */
    [data-testid="stNavigation"] {
        margin-top: -20px !important;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image(
        "assets/logo-transparente.png",
        use_container_width=True,
        output_format="PNG"
    )


pg = st.navigation([
    st.Page("pages/pagina_inicial.py", title="Página inicial", icon="🏠", default=True),
    st.Page("pages/modulo_ranking_empresa.py", title="Ranking", icon="📊"),
    st.Page("pages/modulo_gerador_avaliacao_tech.py", title="Apoio Tech", icon="🧑‍💻"),
    st.Page("pages/sobre.py", title="Sobre", icon="ℹ️"),
    
])
pg.run()

st.write("<style> .stLogo { width: 248px; height: 172px; } </style>", unsafe_allow_html=True)
