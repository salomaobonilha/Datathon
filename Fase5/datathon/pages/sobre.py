import streamlit as st
import base64
import os

# Função para converter imagem local para base64
def get_image_as_base64(image_path):
    """
    Converte um arquivo de imagem local para uma string de dados Base64.
    Assume que o image_path é relativo ao diretório raiz do projeto Streamlit (onde App.py está).
    """
    # Resolve o caminho relativo ao diretório de trabalho atual (CWD)
    # Streamlit geralmente define o CWD como a raiz do projeto.
    full_image_path = os.path.abspath(image_path)

    if not os.path.exists(full_image_path):
        st.error(f"Imagem não encontrada em: {full_image_path}. Verifique se o caminho '{image_path}' está correto e o arquivo existe na pasta 'assets' na raiz do projeto.")
        return None
    
    try:
        with open(full_image_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        
        # Determinar o tipo MIME a partir da extensão do arquivo
        ext = image_path.split('.')[-1].lower()
        mime_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif"}
        mime_type = mime_types.get(ext, "application/octet-stream") # Fallback
        
        if mime_type == "application/octet-stream" and ext not in mime_types:
            st.warning(f"Tipo de imagem não reconhecido para '{image_path}': {ext}. Usando mime-type genérico.")
            
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        st.error(f"Erro ao carregar e codificar a imagem {full_image_path}: {e}")
        return None

# Dados dos criadores
creators_data = [
    {
        "name": "William de Araujo Almeida",
        "funcao": "Engenheiro de T.I e Dados",
        "email": "estudoswill@gmail.com",
        "linkedin": "https://www.linkedin.com/in/williamalmeidadev/",
        "image_url": "assets/william.jpg" 
    },
    {
        "name": "Ana Carolina da Silva Carriel",
        "email": "carolcarriel2009@hotmail.com",
        "linkedin": "https://www.linkedin.com/in/anacarolinadasilvacarriel/", 
        "image_url": "assets/default-woman.jpg"
    },
    {
        "name": "Salomão José Freitas Bonilha",
        "email": "sabonilha@hotmail.com",
        "linkedin": "https://www.linkedin.com/in/salomaobonilha/", 
        "image_url": "assets/default-man.jpg"
    },
    {
        "name": "Gabriel Madeira Menacho",
        "email": "menacho.sjc@gmail.com",
        "linkedin": "https://www.linkedin.com/in/gabrielmenacho/",
        "image_url": "assets/default-man.jpg" 
    }
]

# CSS para estilizar as imagens como circulares e layout
st.markdown("""
<style>
    .profile-pic { /* Imagem do perfil */
        width: 180px;  /* Aumentado de 120px para 180px (50% maior) */
        height: 180px; /* Aumentado de 120px para 180px (50% maior) */
        border-radius: 50%; /* Torna a imagem circular */
        object-fit: cover; /* Garante que a imagem cubra o espaço sem distorcer, cortando se necessário */
        margin-bottom: 10px; /* Espaço abaixo da imagem */
    }
    .creator-text-column {
        padding-left: 0px; /* Removido padding para alinhar totalmente à esquerda da coluna */
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centraliza o texto verticalmente na coluna */
    }
    .creator-info h3 {
        margin-top: 0; /* Remove margem superior do nome para melhor alinhamento */
        margin-bottom: 10px; /* Espaço abaixo do nome */
    }
    .creator-info p {
        margin-bottom: 5px; /* Espaço entre os parágrafos de email e LinkedIn */
    }
</style>
""", unsafe_allow_html=True)

st.title("👥 Sobre os Criadores")
st.markdown("---")

# Loop para exibir cada criador
for i, creator in enumerate(creators_data):
    col1, col2 = st.columns([1, 5]) # Ajustada a proporção da coluna da imagem para acomodar o aumento

    current_image_url = creator["image_url"]
    display_image_src = current_image_url

    # Verifica se a URL é um caminho local (não começa com http/https)
    is_local_path = not (current_image_url.startswith("http://") or current_image_url.startswith("https://"))

    if is_local_path:
        # Tenta carregar como base64
        base64_image_data = get_image_as_base64(current_image_url)
        if base64_image_data:
            display_image_src = base64_image_data
        else:
            # Fallback se o carregamento da imagem local falhar
            display_image_src = f"https://via.placeholder.com/150/CCCCCC/000000?Text=Erro:{creator['name'].split(' ')[0]}"
            st.warning(f"Não foi possível carregar a imagem local: {current_image_url}. Usando placeholder.")

    with col1:
        # Imagem alinhada à esquerda por padrão dentro da sua coluna
        st.markdown(f'<img src="{display_image_src}" class="profile-pic" alt="Foto de {creator["name"]}">', unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="creator-text-column">
            <div class="creator-info">
                <h3>{creator['name']}</h3>
                <p><strong>Função:</strong> {creator.get('funcao','Cientista')}</p>
                <p><strong>Email:</strong> <a href="mailto:{creator['email']}">{creator['email']}</a></p>
                <p><strong>LinkedIn:</strong> <a href="{creator['linkedin']}" target="_blank">Perfil no LinkedIn</a></p>
            </div>
        </div>
        """, unsafe_allow_html=True)


    # Adiciona um separador horizontal entre os criadores, exceto após o último
    if i < len(creators_data) - 1:
        st.markdown("---")
