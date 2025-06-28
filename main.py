import streamlit as st
import pandas as pd
import PyPDF2
import io
import os
import google.generativeai as genai
from datetime import datetime

# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Health Report Assistant",
    page_icon="⚕️"
)

# CSS personalizado
st.markdown("""
<style>
    /* Fundo escuro para melhor contraste */
    html, body, .main, .block-container {
        background-color: #f0f2f6 !important;
    }
    
    /* Estilos para abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        flex-wrap: nowrap;
        padding-bottom: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
        white-space: nowrap;
        font-size: 14px;
        transition: all 0.2s;
        background-color: #e0e0e0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4a6fa5 !important;
        color: white !important;
    }
    
    /* Cards de informação */
    .info-card {
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .warning-card {
        border-left: 4px solid #ff6b6b;
    }
    
    .recommendation-card {
        border-left: 4px solid #51cf66;
    }
    
    /* Texto */
    .simplified-text {
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* Botões */
    .stButton button {
        background-color: #4a6fa5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar Gemini
gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo_texto = genai.GenerativeModel("gemini-1.5-flash")

# Carregar banco de dados de medicamentos (simulado)
@st.cache_data
def load_medications():
    # Em um app real, isso viria de um CSV ou banco de dados
    data = {
        "Nome": ["Paracetamol", "Ibuprofeno", "Omeprazol", "Amoxicilina", "Dipirona"],
        "Descrição": [
            "Analgésico e antitérmico para dor e febre",
            "Anti-inflamatório para dores e inflamações",
            "Protetor gástrico para azia e gastrite",
            "Antibiótico para infecções bacterianas",
            "Analgésico e antitérmico para dores moderadas"
        ],
        "Recomendações": [
            "Tomar 1 comprimido de 500mg a cada 6 horas, máximo 4g/dia",
            "Tomar 1 comprimido de 400mg a cada 8 horas com alimentos",
            "Tomar 1 cápsula de 20mg pela manhã em jejum",
            "Tomar conforme prescrição médica (geralmente a cada 8 ou 12 horas)",
            "Tomar 1 comprimido de 500mg a cada 6 horas se necessário"
        ],
        "Indicações": [
            "Dores leves a moderadas, febre",
            "Dores musculares, inflamações, cólicas",
            "Azia, gastrite, refluxo",
            "Infecções bacterianas (ouvido, garganta, etc.)",
            "Dores moderadas, febre"
        ]
    }
    return pd.DataFrame(data)

medications_db = load_medications()

# Função para extrair texto de PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Interface principal
st.title("⚕️ Health Report Assistant")
st.caption("Entenda seus exames médicos e cuide melhor da sua saúde")

uploaded_file = st.file_uploader("Carregue seu relatório médico (PDF)", type="pdf")

if uploaded_file is not None:
    # Extrair texto do PDF
    report_text = extract_text_from_pdf(uploaded_file)
    
    # Armazenar em session state para uso nas abas
    st.session_state.report_text = report_text
    
    # Criar abas
    tabs = st.tabs(["📋 Visão Geral", "💬 Chat com Relatório", "👩‍⚕️ Recomendações de Saúde", "💊 Medicamentos Indicados"])
    
    with tabs[0]:
        st.header("📋 Visão Simplificada do Relatório")
        
        if 'simplified_report' not in st.session_state:
            with st.spinner('Processando relatório...'):
                prompt = f"""
                Você é um assistente médico que ajuda pacientes a entenderem seus relatórios médicos. 
                Simplifique este relatório usando linguagem clara e acessível:

                **Relatório Original:**
                {report_text}

                **Instruções:**
                1. Identifique os exames realizados
                2. Destaque os resultados mais relevantes
                3. Explique os termos técnicos em linguagem simples
                4. Organize por seções (hemograma, colesterol, etc.)
                5. Mantenha todas as informações importantes

                **Formato:**
                - Títulos claros para cada seção
                - Listas com marcadores para facilitar
                - Destaque valores fora do normal
                - Evite jargões médicos
                """
                
                response = modelo_texto.generate_content(prompt)
                st.session_state.simplified_report = response.text
        
        st.markdown(f'<div class="info-card simplified-text">{st.session_state.simplified_report}</div>', unsafe_allow_html=True)
        
        # Botão para download do relatório simplificado
        st.download_button(
            "⬇️ Baixar Relatório Simplificado",
            st.session_state.simplified_report,
            file_name=f"relatorio_simplificado_{datetime.now().strftime('%Y%m%d')}.txt"
        )
    
    with tabs[1]:
        st.header("💬 Chat com seu Relatório")
        st.write("Faça perguntas sobre seu relatório médico")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("O que você gostaria de saber sobre seu relatório?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner('Analisando seu relatório...'):
                    chat_prompt = f"""
                    Você é um assistente médico ajudando um paciente a entender seu relatório. 
                    O relatório contém: {report_text[:10000]}...
                    
                    Pergunta do paciente: {prompt}
                    
                    Responda de forma:
                    - Clara e simples
                    - Empática e acolhedora
                    - Técnica quando necessário, mas explicando os termos
                    - Inclua recomendações práticas quando aplicável
                    - Se não souber, diga que não pode responder e sugira consultar o médico
                    """
                    
                    response = modelo_texto.generate_content(chat_prompt)
                    st.markdown(response.text)
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    with tabs[2]:
        st.header("👩‍⚕️ Pontos de Atenção à Saúde")
        
        if 'health_highlights' not in st.session_state:
            with st.spinner('Identificando pontos importantes...'):
                prompt = f"""
                Analise este relatório médico e identifique:

                **Relatório:**
                {report_text}

                **Itens a Identificar:**
                1. Valores fora da normalidade (destacar e explicar)
                2. Possíveis condições sugeridas pelos resultados
                3. Recomendações de estilo de vida
                4. Sinais que exigem acompanhamento médico
                5. Exames que podem precisar de repetição

                **Formato:**
                - Lista priorizada por importância
                - Linguagem simples e direta
                - Destaque urgências com ❗
                - Inclua valores de referência quando relevante
                """
                
                response = modelo_texto.generate_content(prompt)
                st.session_state.health_highlights = response.text
        
        st.markdown(f'<div class="info-card warning-card">{st.session_state.health_highlights}</div>', unsafe_allow_html=True)
        
        # Gerar recomendações adicionais
        if 'health_recommendations' not in st.session_state:
            with st.spinner('Gerando recomendações personalizadas...'):
                prompt = f"""
                Baseado nestes pontos de atenção:
                {st.session_state.health_highlights}
                
                Crie recomendações práticas de saúde:
                1. Hábitos alimentares
                2. Atividade física
                3. Monitoramento caseiro
                4. Sinais para procurar médico
                5. Periodicidade de novos exames
                
                Formato:
                - Lista com ações concretas
                - Prazo para cada recomendação
                - Nível de prioridade (alta/média/baixa)
                """
                
                response = modelo_texto.generate_content(prompt)
                st.session_state.health_recommendations = response.text
        
        st.subheader("Recomendações Personalizadas")
        st.markdown(f'<div class="info-card recommendation-card">{st.session_state.health_recommendations}</div>', unsafe_allow_html=True)
    
    with tabs[3]:
        st.header("💊 Medicamentos Potencialmente Indicados")
        st.write("Baseado em seu relatório, estes medicamentos podem ser relevantes")
        
        # Filtro de busca
        search_term = st.text_input("Buscar medicamento por nome ou condição")
        
        # Filtrar medicamentos
        if search_term:
            filtered_meds = medications_db[
                medications_db['Nome'].str.contains(search_term, case=False) | 
                medications_db['Indicações'].str.contains(search_term, case=False)
            ]
        else:
            filtered_meds = medications_db
        
        # Mostrar medicamentos
        for _, med in filtered_meds.iterrows():
            with st.expander(f"**{med['Nome']}** - {med['Descrição']}", expanded=False):
                st.write(f"**Indicações:** {med['Indicações']}")
                st.write(f"**Recomendações de uso:** {med['Recomendações']}")
                st.warning("⚠️ Consulte sempre um médico antes de usar qualquer medicamento")
        
        # Disclaimer importante
        st.error("""
        **Aviso Importante:** 
        Estas sugestões são baseadas em informações gerais e não substituem a avaliação médica. 
        Nunca tome medicamentos sem orientação profissional.
        """)

else:
    st.info("Por favor, carregue seu relatório médico em PDF para começar.")
    st.image("https://img.freepik.com/free-vector/medical-report-concept-illustration_114360-1503.jpg", width=400)
