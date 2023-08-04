# Importando as bibliotecas necessárias
import pandas as pd
import numpy as np
import plotly.express as px
import regex as re
import folium
import streamlit as st
from streamlit_folium import folium_static


st.set_page_config(
    page_title='Visão Empresa',
    page_icon="📈",
	layout='wide',
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

def order_day(df):
    """" Esta função cria um gráfico de barras para representar a quantidade de pedidos por dia.
    - O eixo x corresponde ao dia
    - e o eixo y ao número de pedidos naquele dia
    
    Input: dataframe
    Output: gráfico em barras (graph)
    """
    
    cols=['ID','Order_Date']
    order_per_day=df.loc[:,cols].groupby('Order_Date').count().reset_index()
    graph=px.bar(order_per_day, x='Order_Date',y='ID',title='Número de pedidos por dia')
    return graph

def order_traffic(df):
    """ Esta função retorna um gráfico de barras representando a quantidade de pedidos por tipo de tráfego.
    - o eixo x corresponde ao tipo de tráfego
    - o eixo y corresponde ao número de pedidos em cada tipo
    Input: dataframe
    Output: gráfico em barras
    """
    cols=['ID', 'Road_traffic_density']
    order_traffic=df.loc[:,cols].groupby('Road_traffic_density').count().reset_index()
    graph=px.bar(order_traffic,x='Road_traffic_density',y='ID',title='Pedidos por tráfego')
    return graph
            
def order_traf_city(df):
    """ Esta função retorna um gráfico de bolhas para representar o volume de pedidos em cada cidade por cada tipo de tráfego.
    - o eixo x corresponde ao tipo de tráfego
    - o eixo y corresponde à cidade
    - a cor e o tamanho da bolha são dependentes do número de pedidos
    
    Input: dataframe
    Output: gráfico de bolhas
    """
    cols=['ID','Road_traffic_density','City']
    pedidos_traf_city=df.loc[:,cols].groupby(['Road_traffic_density','City']).count().reset_index()
    graph=px.scatter(pedidos_traf_city,
                    x='Road_traffic_density',
                    y='City',
                    color='ID',
                    size='ID',
                    title='Volume de pedidos por cidade e tráfego')
    return graph

def order_week(df):
    """ Esta função retorna um gráfico de barras para representar o número de pedidos por semana
    - o eixo x corresponde ao número da semana
    - o eixo y corresponde ao número de pedidos daquela semana
    A função ainda adiciona uma coluna extra ao dataframe contendo o número da semana.
    
    Input: dataframe
    Output: gráfico de barras
    """
    df['week_of_year']=df.loc[:,'Order_Date'].dt.strftime('%U')
    cols=['week_of_year','ID']
    order_per_week=df.loc[:,cols].groupby('week_of_year').count().reset_index()
    graph=px.bar(order_per_week,x='week_of_year',y='ID',title='Número de pedidos por semana')
    return graph

def order_deliver_week(df):
    """ Esta função retorna um gráfico de linhas que representa o número de pedidos por entregador por semana.
    - o eixo x corresponde à semana do ano
    - o eixo y corresponde ao número de entregas feita por entregador na semana correspondente
        
    Input: dataframe
    Output: gráfico de linhas
    """
    
    pedidos1=df.loc[:,['ID','week_of_year']].groupby(['week_of_year']).count().reset_index()
    pedidos2=df.loc[:,['week_of_year','Delivery_person_ID']].groupby('week_of_year').nunique().reset_index()
    pedidos=pd.merge(pedidos1,pedidos2,how='inner')
    pedidos['order_delivery']=pedidos['ID']/pedidos['Delivery_person_ID']
    graph=px.line(pedidos,x='week_of_year',y='order_delivery',title='Pedidos por entregador por semana')
    return graph
        
def central_spot(df):
    """ Esta função retorna um mapa da localização central dos pedidos feitos em cada cidade por cada tipo de tráfego.
    A função agrupa o dataframe por cidade e tipo de tráfego e faz a mediana da latitude e da longitude dos restaurantes em cada condição. Esses dados são plotados e é criado um mapa com os pontos.
    Input: dataframe
    Output: mapa
    """
    df_aux1=(df
             .loc[:,['Restaurant_latitude','City','Road_traffic_density']]
             .groupby(['City','Road_traffic_density'])
             .median()
             .reset_index()) 
    df_aux2=(df
             .loc[:,['Restaurant_longitude','City','Road_traffic_density']]
             .groupby(['City','Road_traffic_density'])
             .median()
             .reset_index())
    df_aux=pd.merge(df_aux1,df_aux2,how='inner')
    map=folium.Map()
    for i in range(len(df_aux)):
             folium.Marker(
                 [df_aux.loc[i,'Restaurant_latitude'],df_aux.loc[i,'Restaurant_longitude']],
                 popup=df_aux.loc[i,['City','Road_traffic_density']]).add_to(map)
    return map
             
# -------------------------------------- Inicio da Estratura Logica do codigo --------------------------------------

# =====================================================
# Carregando o arquivo
# =====================================================
df_raw=pd.read_csv(r"C:\Users\kmila\Documents\repos\ftc\dataset\train.csv")

# =====================================================
# Limpando os dados
# =====================================================
df=clean_data(df_raw)


# VISÃO EMPRESA

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

st.header('Visão Empresa')
tab1,tab2,tab3=st.tabs(['Visão Gerencial','Visão Tática','Visão Geográfica'])

with tab1:
    with st.container():     
        graph=order_day(df)
        st.plotly_chart(graph,use_container_width=True)
        col1,col2=st.columns(2)
        with col1:
            graph=order_traffic(df)
            st.plotly_chart(graph,use_container_width=True)
        with col2:
            graph=order_traf_city(df)
            st.plotly_chart(graph,use_container_width=True)
            
with tab2:
    with st.container():
        graph=order_week(df)
        st.plotly_chart(graph,use_container_width=True)
        
        graph=order_deliver_week(df)
        st.plotly_chart(graph,use_container_width=True)

with tab3:
    with st.container():
        st.markdown('### Localização central dos pedidos por tráfego')        
        fig=central_spot(df)
        folium_static(fig)
    
