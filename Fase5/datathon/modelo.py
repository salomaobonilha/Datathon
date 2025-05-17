import nltk
import tensorflow as tf
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize



class SistemaRecomendacao:
    def __init__(self):
        nltk.download('punkt_tab')
        nltk.download('stopwords')
        nltk.download('punkt')        

    def _carregar_modelo(self, df_candidatos, model_path):        
        self.df_candidatos = df_candidatos        
        self.model = tf.keras.models.load_model(model_path)
        self.vectorizer, self.embeddings_cv = self._preparar_dados()
    
    def _preprocessar_texto(self, text):
        stop_words = stopwords.words('portuguese')
        text = re.sub(r'\d+', '', str(text).lower())
        text = re.sub(r'[^\w\s]', '', text)
        tokens = word_tokenize(text)
        return ' '.join([t for t in tokens if t not in stop_words and len(t) > 2])
    
    def _preparar_dados(self):
        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1,2),
            preprocessor=self._preprocessar_texto
        )

        print(self.df_candidatos.columns)
        textos_cv = self.df_candidatos['curriculo'].apply(self._preprocessar_texto)
        embeddings = vectorizer.fit_transform(textos_cv)
        return vectorizer, embeddings
    
    def _processar_vaga(self, descricao_vaga):
        processed = self._preprocessar_texto(descricao_vaga)
        return self.vectorizer.transform([processed])
    
    def recomendar_candidatos(self, descricao_vaga, top_n=5):
        embedding_vaga = self._processar_vaga(descricao_vaga)
        similaridades = cosine_similarity(embedding_vaga, self.embeddings_cv).flatten()
        top_indices = similaridades.argsort()[-top_n:][::-1]
        
        resultados = self.df_candidatos.iloc[top_indices].copy()
        resultados['similaridade'] = similaridades[top_indices]
        return resultados.sort_values('similaridade', ascending=False)