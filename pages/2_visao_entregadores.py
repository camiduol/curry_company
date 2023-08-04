# Importando as bibliotecas necessárias
import pandas as pd
import numpy as np
import plotly.express as px
import regex as re
import folium
import streamlit as st
from streamlit_folium import folium_static


st.set_page_config(
    page_title='Visão Entregadores',
    page_icon="🏍",
	layout='wide'
)


# =====================================================
# FUNÇÕES
# =====================================================

def clean_data(df):
    
    """ Esta função tem a responsabilidade de limpar o dataframe
    Os tipos de limpeza que ela faz:
    1. Exclui as linhas com valores nulos
    2. Exclui os espaços vazios do conjunto de dados, exemplo: 'CARRO ' -> 'CARRO'
    3. Converte os tipos das colunas para os formatos corretos
    4. Limpa e converte a coluna 'Time_taken(min)
    
    Input: dataframe
    Output: dataframe
    """
    
    # Excluindo as linhas que possuem valor nulo:
    cols=df.columns
    for col in cols:
        df=df.loc[df[col]!='NaN ']

    # Excluindo os espaços vazios do meu conjunto de dados:
    df['ID']=df.loc[:,'ID'].str.strip()
    df['Delivery_person_ID']=df.loc[:,'Delivery_person_ID'].str.strip()
    df['Road_traffic_density']=df.loc[:,'Road_traffic_density'].str.strip()
    df['Type_of_order']=df.loc[:,'Type_of_order'].str.strip()
    df['Type_of_vehicle']=df.loc[:,'Type_of_vehicle'].str.strip()
    df['Festival']=df.loc[:,'Festival'].str.strip()
    df['City']=df.loc[:,'City'].str.strip()

    # Convertendo as colunas para os seus formatos corretos
    df['Delivery_person_Age']=df['Delivery_person_Age'].astype(int)
    df['Delivery_person_Ratings']=df['Delivery_person_Ratings'].astype(float)
    df['Order_Date']=pd.to_datetime(df['Order_Date'],format='%d-%m-%Y')
    df['multiple_deliveries']=df['multiple_deliveries'].astype(int)

    # Limpando e convertendo a coluna 'Time_taken(min)'
    df['Time_taken(min)']=df['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1])
    df['Time_taken(min)']=df['Time_taken(min)'].astype(int)

    return df


def rating_by (df,col):
    """ Esta função tem como objetivo retornar a média e o desvio padrão das avaliações agrupadas por outro parâmetro (a ser escolhido pelo usuário).
    Portanto:
                
    Input: dataframe; coluna a ser agrupada
    Output: dataframe com média e desvio padrão
    """
    cols=['Delivery_person_Ratings',col]
    rating=(df
            .loc[:,cols]
            .groupby(col)
            .agg({'Delivery_person_Ratings':['mean','std']})
            .reset_index())
    rating.columns=[col,'Média da avaliação','Desvio Padrão da avaliação']
    return rating

def top_ten(df,arg):
    """ Essa função tem como objetivo retornar os 10 entregadores mais rápidos ou mais lentos.
    Input: dataframe; arg = 'maior' para mais rápido ou 'menor' para mais lento
    Output: dataframe com o top 10
    """
    aux1=df.sort_values(['Time_taken(min)','City'],ascending = True).reset_index()
    cols=['City','Time_taken(min)','Delivery_person_ID']
    if arg == 'maior':
        aux2=aux1.loc[:,cols].groupby(['City']).head(10).reset_index(drop=True)
    else:
        aux2=aux1.loc[:,cols].groupby(['City']).tail(10).reset_index(drop=True)
    return aux2


# -------------------------------------- Inicio da Estratura Logica do codigo --------------------------------------

# =====================================================
# Carregando o arquivo
# =====================================================
df_raw=pd.read_csv("dataset\train.csv")

# =====================================================
# Limpando os dados
# =====================================================
df=clean_data(df_raw)


# VISÃO ENTREGADORES

# =====================================================
# Barra lateral
# =====================================================
st.sidebar.markdown('# Cury Company')
st.sidebar.markdown('### Fastest Delivery in Town',)
st.sidebar.markdown('---')
data_slider=st.sidebar.slider(
    'Até a data:',
    min_value=pd.datetime(2022,2,11),
    max_value=pd.datetime(2022,4,6),
    value=pd.datetime(2022,4,10),
    format='DD-MM-YYYY')
linhas_selecionadas=df['Order_Date']<=data_slider
df=df.loc[linhas_selecionadas,:]

st.sidebar.markdown('---')
traffic_selected=st.sidebar.multiselect(
    'Selecione os tipos de trânsito desejados:',
    ['Jam','Medium','High','Low'],
    default=['Jam','Medium','High','Low'])
linhas_selecionadas=df['Road_traffic_density'].isin(traffic_selected)
df=df.loc[linhas_selecionadas,:]

st.sidebar.markdown('---')
st.sidebar.text('Powered by Camila Duarte',)

# =====================================================
# Layout Streamlit
# =====================================================

#st.markdown(#"""---""")
st.header('Visão Entregadores')
tab1,tab2,tab3=st.tabs(['Visão Gerencial','_','_'])

with tab1:
    with st.container():
        st.markdown('## Métricas gerais')
        col1,col2,col3,col4=st.columns(4)
        with col1:
            maior_idade=df.loc[:,'Delivery_person_Age'].max()
            col1.metric('Maior idade',maior_idade)            
        with col2:
            menor_idade=df.loc[:,'Delivery_person_Age'].min()
            col2.metric('Menor idade',menor_idade)
        with col3:
            melhor_condicao=df.loc[:,'Vehicle_condition'].max()
            col3.metric('Melhor condição',melhor_condicao)            
        with col4:
            pior_condicao=df.loc[:,'Vehicle_condition'].min()
            col4.metric('Pior condição',pior_condicao)   
            
    with st.container():
        st.markdown('## Avaliações')
        col1,col2=st.columns(2)
        with col1:
            st.markdown('#### Avaliação média por entregador')
            avaliacao_media=(df
                             .loc[:,['Delivery_person_ID','Delivery_person_Ratings']]
                             .groupby('Delivery_person_ID')
                             .mean()
                             .reset_index())
            avaliacao_media.columns=['ID do entregador','Avaliação média do entregador']
            st.dataframe(avaliacao_media)
        with col2:
            st.markdown('#### Avaliação média por tráfego')
            rating_traf=rating_by(df,'Road_traffic_density')
            st.dataframe(rating_traf)
            
            st.markdown('#### Avaliação média por condição climática') 
            rating_cond=rating_by(df,'Weatherconditions')
            st.dataframe(rating_cond)
                        
    with st.container():
        st.markdown('## Velocidade de entrega')
        col1,col2=st.columns(2)
        with col1:
            st.markdown('#### Top 10 entregadores mais rápidos')                 
            veloz=top_ten(df,'maior')
            st.dataframe(veloz)
        with col2:
            st.markdown('#### Top 10 entregadores mais lentos')
            lento=top_ten(df,'menor')
            st.dataframe(lento)
            
        