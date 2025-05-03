import streamlit as st

st.set_page_config(page_title="Início", layout="wide",
    menu_items={
        'Get Help': None,  # Remove o link "Get Help"
        'Report a bug': None,  # Remove o link "Report a bug"
        'About': None  # Remove o link "About"
    }
)

st.title('Datathon - Tech Challenge')


    
st.markdown(''' lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Donec euismod, nisl eget consectetur sagittis, nisl nunc egestas nisi, vitae facilisis nunc nisl eget nunc.''')
    # Código HTML + CSS para centralizar a imagem
st.markdown(
        """
        <div style="display: flex; justify-content: center;">
            <img src="https://webrh.decisionbr.com.br/assets/Bootstrap/img/examples/logotipo_decision_pequeno.png" width="320">
        </div>
        """,
        unsafe_allow_html=True
    )


st.info("ipsum dolor sit amet, consectetur adipiscing elit. Donec euismod, nisl eget consectetur sagittis, nisl nunc egestas nisi, vitae facilisis nunc nisl eget nunc.")


def gerar_menu_lateral():
    hide_pages_nav_css = """
                            <style>
                                div[data-testid="stSidebarNav"] {
                                    display: none;
                                }
                            </style>
                        """
    st.markdown(hide_pages_nav_css, unsafe_allow_html=True)
    
    st.sidebar.image("https://webrh.decisionbr.com.br/assets/Bootstrap/img/examples/logotipo_decision_pequeno.png", width=280)
    st.sidebar.title("Menu")
    st.sidebar.write("Navegue pelas páginas abaixo:")
    st.sidebar.page_link(page="App.py", label="🏠 Página Inicial") 
    st.sidebar.page_link("pages/modulo_ranking_empresa.py", label="📊 Ranking Vagas") # Certifique-se que este arquivo está em 'pages/'
    st.sidebar.page_link("pages/modulo_gerador_avaliacao_tech.py", label="🧑‍💻 Gerador Avaliação Técnica") 
 



gerar_menu_lateral()
st.markdown("---")