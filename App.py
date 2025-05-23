import streamlit as st

st.set_page_config(layout="wide")
st.markdown("""
<style>
    /* Esconde o logo quando o menu está recolhido */
    [data-testid="collapsedControl"] + .stLogo {
        display: none !important;
    }
    
    /* Ajusta o tamanho e posição do logo */
    .stLogo {
        width: 248px !important;
        height: 172px !important;
        position: absolute;
        top: -40px;
        left: -40px;
        transition: opacity 0.3s;
    }
    
    /* Suaviza a transição ao recolher/expandir */
    [data-testid="stSidebar"] {
        transition: width 0.3s;
    }
</style>
""", unsafe_allow_html=True)
st.logo("assets/logo-transparente.png")

pg = st.navigation([
    st.Page("pages/pagina_inicial.py", title="Página inicial", icon="🏠", default=True),
    st.Page("pages/modulo_ranking_empresa.py", title="Ranking", icon="📊"),
    st.Page("pages/modulo_gerador_avaliacao_tech.py", title="Apoio Tech", icon="🧑‍💻"),
    st.Page("pages/sobre.py", title="Sobre", icon="ℹ️"),
    
])
pg.run()

st.write("<style> .stLogo { width: 248px; height: 172px; } </style>", unsafe_allow_html=True)
