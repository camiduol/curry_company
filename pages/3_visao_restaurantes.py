# Importando as bibliotecas necessárias
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
from geopy.distance import distance
from geopy import Point


st.set_page_config(
    page_title='Visão Restaurantes',
    page_icon="🍝",
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

def dist_media(df,arg):
    """
    Esta função calcula a distância entre os restaurantes e os locais de entrega.
    Esta função pode retornar 2 valores diferentes:
        Input:
            - df: dataframe
            - arg: 'True' = retorna o valor do dataframe auxiliar; 'False' = retorna a distância média entre os pontos.
        Output:
            - aux: dataframe auxiliar contendo as colunas de distância para cada ponto
            - dist_media: distância média entre os pontos em km     
    Esta função calcula a distância média de cada entrega levando em consideração os pontos de latitude e longitude de cada restaurante e cada local de entrega. 
    Esta função também cria uma coluna de pontos usando as latitudes e longitudes dos Restaurantes e outra para os locais de entrega. 
    A partir desses pontos criados, a função calcula a distância entre os dois pontos (restaurantes e locais de entrega). 
    Ao final, a função retorna um valor médio de todas as distâncias ou o dataframe auxiliar.             
    """
    aux=df.loc[:,['ID',
                  'City',
                  'Restaurant_latitude',
                  'Restaurant_longitude',
                  'Delivery_location_latitude',
                  'Delivery_location_longitude']]
    #Pontos geográficos dos restaurantes
    aux['restaurant_location']=(aux.apply(lambda row:
                                          Point(latitude=row['Restaurant_latitude'],
                                                longitude=row['Restaurant_longitude']),
                                          axis=1))      
    #Pontos geográficos dos locais de entrega
    aux['delivery_location']=(aux.apply(lambda row: 
                                        Point(latitude=row['Delivery_location_latitude'],
                                              longitude=row['Delivery_location_longitude']),
                                        axis=1))
    #Cálculo da distância em km entre os pontos
    aux['distance_km']=aux.apply(lambda row: distance(row['restaurant_location'], row['delivery_location']).km, axis=1)
    
    if arg == 'False':
        #Cálculo da média das distâncias com arredondamento de 2 casas decimais
        dist_media=np.round(aux['distance_km'].mean(),2)
        return dist_media
    else:
        return aux
           
def distance_city(df):
    """ 
    Esta função cria um gráfico de pizza com uma parte destacada para representar a distância média por cidade.
    As cores representam as cidades e a porção da pizza representa os valores das distâncias em porcentagem, ou seja, quanto cada cidade influencia na média.
    Esta função utiliza a função dist_media para criar o dataframe aux.
    
    Input: dataframe
    Output: gráfico de pizza com destaque
    """
    cols=['distance_km','City']
    aux=dist_media(df,'True')
    aux2=aux.loc[:,cols].groupby(['City']).mean().reset_index()
    graph=go.Figure(data=[go.Pie(labels=aux2['City'],values=aux2['distance_km'],pull=[0,0.1,0])])
    return graph
    
def mean_time_city(df):
    """
    Esta função cria um gráfico de barras para representar o tempo médio por cidade.
    O eixo x representa as cidades e o eixo y o tempo médio da entrega.
    Além disso o erro (desvio padrão) também é representado no gráfico.
                
    Input:
        - df: dataframe 
    Output:
        - graph: gráfico de barras com barra de erro
                
    """
    cols = ['City','Time_taken(min)']
    time_city=df.loc[:,cols].groupby('City').agg({'Time_taken(min)':['mean','std']}).reset_index()
    time_city.columns=['City','mean_time','std_time']
    graph=px.bar(time_city,x='City',y='mean_time',error_y='std_time',color='City')
    return graph
                
def time_city_traffic (df):
    """
    Esta função cria um gráfico de Sunburst para representar o tempo médio de entrega para cada cidade e cada tipo de tráfego.
    A escala de cor representa o tempo médio; as porções internas do círculo representam as cidades; e as porções externas representam o tipo de tráfego.
            
    Input:
        - df: dataframe
    Output:
        - graph: gráfico de sunburst
    """
    time_city_traf=(df.loc[:,['City','Time_taken(min)','Road_traffic_density']]
                    .groupby(['City','Road_traffic_density'])
                    .agg({'Time_taken(min)':['mean','std']})
                    .reset_index())
    time_city_traf.columns=['City','Road_traffic_density','mean_time','std_time']
    graph=px.sunburst(time_city_traf,path=['City','Road_traffic_density'],values='mean_time',color='mean_time')
    return graph
            
# -------------------------------------- Inicio da Estrutura Logica do codigo --------------------------------------

# =====================================================
# Carregando o arquivo
# =====================================================
df_raw=pd.read_csv(r"C:\Users\kmila\Documents\repos\ftc\dataset\train.csv")

# =====================================================
# Limpando os dados
# =====================================================
df=clean_data(df_raw)


# VISÃO RESTAURANTES

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
st.header('Visão Restaurantes')
tab1,tab2,tab3=st.tabs(['Visão Gerencial','_','_'])

with tab1:
    with st.container():
        col1,col2,col3,col4,col5,col6=st.columns(6)
        with col1:
            entregador_unico=df['Delivery_person_ID'].nunique()
            col1.metric('Entregadores únicos',entregador_unico)
        with col2:
            distancia=dist_media(df,'False')
            col2.metric('Distância média',distancia)
        with col3:
            festival=df.loc[df['Festival']=='Yes']
            tempo_c_festival=np.round(festival['Time_taken(min)'].mean(),2)
            col3.metric('Tempo médio de entrega com Festival',tempo_c_festival)
        with col4:
            festival=df.loc[df['Festival']=='Yes']
            std_c_festival=np.round(festival['Time_taken(min)'].std(),2)
            col4.metric('Desvio padrão com Festival',std_c_festival)
        with col5:
            festival=df.loc[df['Festival']=='No']
            tempo_s_festival=np.round(festival['Time_taken(min)'].mean(),2)
            col5.metric('Tempo médio de entrega sem Festival',tempo_s_festival)
        with col6:
            festival=df.loc[df['Festival']=='No']
            std_s_festival=np.round(festival['Time_taken(min)'].std(),2)
            col6.metric('Desvio padrão do tempo de entrega sem Festival',std_s_festival)
    
    st.markdown("""---""")
    with st.container():
        st.markdown('Distância média por cidade')
        fig=distance_city(df)
        st.plotly_chart(fig,use_container_width=True)
    
    st.markdown("""---""")
    with st.container():
        col1,col2=st.columns(2)
        with col1:
            st.markdown('Tempo médio de entrega por cidade')
            fig=mean_time_city(df)
            st.plotly_chart(fig,use_container_width=True)
        with col2:
            st.markdown('Tempo médio de entrega por tipo de pedido')
            time_city_order=(df.loc[:,['City','Time_taken(min)','Type_of_order']]
                             .groupby(['City','Type_of_order'])
                             .agg({'Time_taken(min)':['mean','std']}))
            time_city_order.columns=['mean_time','std_time']
            
            st.dataframe(time_city_order.reset_index())
    
    st.markdown("""---""")
    with st.container():
        st.markdown('Tempo médio por cidade e por tráfego')
        fig=time_city_traffic(df)
        st.plotly_chart(fig,use_container_width=True,theme=None)