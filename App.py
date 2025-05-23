import streamlit as st

st.set_page_config(layout="wide")
# Logo apenas na sidebar expandida
st.markdown("""
<style>
    /* Posiciona o logo fixo no topo */
    [data-testid="stSidebar"] img {
        position: sticky;
        top: 10px;
        margin-bottom: 30px !important;
        max-width: 200px !important;
    }
    
    /* Remove padding da sidebar */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
</style>
""", unsafe_allow_html=True)

# Logo como primeiro elemento da sidebar
with st.sidebar:
    st.image(
        "assets/logo-transparente.png",
        use_container_width=True,  # Parâmetro atualizado
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
