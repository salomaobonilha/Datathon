import streamlit as st

st.set_page_config(layout="wide")
st.logo("assets/logo-transparente.png")

pg = st.navigation([
    st.Page("pages/pagina_inicial.py", title="Página inicial", icon="🏠", default=True),
    st.Page("pages/modulo_gerador_avaliacao_tech.py", title="Apoio Tech", icon="🧑‍💻"),
    st.Page("pages/modulo_ranking_empresa.py", title="Ranking", icon="📊"),
    st.Page("pages/sobre.py", title="Sobre", icon="ℹ️"),
    
])
pg.run()

st.write("<style> .stLogo { width: 248px; height: 172px; } </style>", unsafe_allow_html=True)