#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Streamlit Housing App Demo
    
Make sure to install Streamlit with `pip install streamlit`.

Run `streamlit hello` to get started!

To run this app:

1. cd into this directory
2. Run `streamlit run streamlit_app.py`
"""

import pandas as pd
import numpy as np
from haversine import haversine, Unit
from chart_studio import plotly as py
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
import requests
import streamlit as st


## PART 1 - Intro

st.write('''
# Let us help you find your next apartment!
Did you get a new job in the DC/VA/MD area? Are you considering moving closer to work? Will paying more for an apartment closer to work to reduce your commute time actually make sense financially? Let us help you answer that question!
In the fields below, please enter an address for new job and we will find you your next apartment! Be sure to spell everything correctly! Caps are optional.
Apartment listings will come from [apartments.com](https://www.apartments.com)
''')


# PART 2 - Get user's target location, speed, hourly wage

st.write(
'''
## Enter your workplace location in the fields below.

''')

with st.form(key='user_info'):
    street = st.text_input('Street', max_chars=100)
    city = st.text_input('City', max_chars=100)
    state = st.text_input('State', max_chars=100)
    zipcode = st.text_input('Zip', max_chars=100)

    address = street + ' ' + city + ' ' + state + ' ' + zipcode

    st.write(
    '''
    ## Enter your hourly wage ($ per hour). 
    This will let us determine how much your time spent commuting is worth to you which we will factor in to the rents.
    ''')

    hourly_income = st.number_input('Hourly wage', value=40)

    st.write('''
    ## Enter your anticipated average commuting speed. 
    The default is 40 mph.
    ''')

    speed = st.number_input('Speed', min_value=1, max_value=70, value=40)

    with open('mapbox_key.txt') as f:
        mapbox_access_token = f.read().rstrip()

    submit_button = st.form_submit_button(label='Submit')

if submit_button:
# PART 3 - Generate random apartment listings. This will be replaced with real listings in the actual deployment.    
    
    def generate_listings(st=1000, one=1000, two=1000): # creates a df of apartment listings and geocoords for studio, 1-br, and 2-br, each with a range of rents
        studio_low = 1500
        one_br_low = 1700
        two_br_low = 2200

        # The high end will be low end + $1000
        high = 1000
        
        # GPS limits
        
        NW = 39.10243088446053, -77.45517065148175
        NE = 39.10243088446053, -76.9218509753054
        SE = 38.79255073884452, -76.9218509753054
        SW = 38.79255073884452, -77.45517065148175
        
        lat_range = NW[0] - SW[0]
        long_range = NE[1] - NW[1]
        
        studios = []
        one_br = []
        two_br = []
        
        for i in range(st):
            rent = np.random.randint(studio_low, studio_low + high + 1)
            rand = np.random.random()
            lat =  SW[0] + rand*lat_range
            rand = np.random.random()
            long = SW[1] + rand*long_range
            studios += [[rent, lat, long, 'studio']]
        for i in range(one):
            rent = np.random.randint(one_br_low, one_br_low + high + 1)
            rand = np.random.random()
            lat =  SW[0] + rand*lat_range
            rand = np.random.random()
            long = SW[1] + rand*long_range
            one_br += [[rent, lat, long, '1_br']]
        for i in range(two):
            rent = np.random.randint(two_br_low, two_br_low + high + 1)
            rand = np.random.random()
            lat =  SW[0] + rand*lat_range
            rand = np.random.random()
            long = SW[1] + rand*long_range
            two_br += [[rent, lat, long, '2_br']]
                        
        results = pd.DataFrame(studios + one_br + two_br, columns = ['rent', 'lat', 'long', 'type'])
        results.to_pickle('listings')

        return results

    # Calculate the distances between each point in the df and the user's target location.

    def dist(point, df): # input [lat, long] and it will return the distance between 'point' and each row in the df
        df['distance'] = df.apply(lambda x: haversine((x.lat, x.long), (point[0], point[1]), unit='mi'), axis=1)
        return df

    def commute_adjusted_listings(hourly_income, work_loc, df, speed=40): # input $/hr, work location (lat, long), data, average speed
        df = dist(work_loc, df)
        df['commute_time_min'] = df['distance'] / speed * 60 # yields commute time in minutes 
        df['adjusted_rent'] = df['rent'] + df['commute_time_min'] / 60 * hourly_income * 2 * 20 # distance/speed = time * income = dollar value of commute * 2 because commuting is roundtrip * 20 for 20 workdays per month
        return df


    def get_geocoords(address=address):
        workplace = urllib.parse.quote(address)
        try: url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{workplace}.json?access_token={mapbox_access_token}'
        except IndexError:
            print('Check your address again for typos. The address must be within the immediate DC/MD/VA area.')
            return
        location = requests.get(url)
        return location.json()['features'][0]['center']

    workplace = get_geocoords(address)[::-1]
    results = commute_adjusted_listings(40, workplace, generate_listings())


    # PART 4 - Show graph of listings

    # There is a bug in plotly where if you set the marker style, the color defaults to gray.
    # https://github.com/plotly/plotly.py/issues/2485
    # https://github.com/plotly/plotly.js/issues/2813 ('Note that the array `marker.color` and `marker.size`', are only available for *circle* symbols.')

    px.set_mapbox_access_token(mapbox_access_token)
    fig = px.scatter_mapbox(results, lat="lat", lon="long", hover_name="type", hover_data=["rent"],
                            color="adjusted_rent", zoom=10, height=600)

    fig.update_layout(mapbox_style="light")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    fig.add_trace(go.Scattermapbox(
            # name='Set location',
            lat=[workplace[0]],
            lon=[workplace[1]],
            # mode='markers',
            # marker={'size': 25, 'color': 'white' },
            marker=go.scattermapbox.Marker(
            size=25,
            color='red',
            # symbol='square',
            
            ),
            marker_symbol = 'star',
            # marker_color = 'white',
            hoverinfo = 'none',
            showlegend = False
            )
        
        )
    # fig.update_traces(marker_color='red', selector=dict(type='scattermapbox'))
    fig.show()



    # st.write(
    # '''
    # ### Graphing and Buttons
    # Let's graph some of our data with matplotlib. We can also add buttons to add interactivity to our app.
    # '''
    # )

    # fig, ax = plt.subplots()

    # ax.hist(data['PRICE'])
    # ax.set_title('Distribution of House Prices in $100,000s')

    # show_graph = st.checkbox('Show Graph', value=True)

    # if show_graph:
    #     st.pyplot(fig)


    # # PART 5 - Mapping and Filtering Data

    # st.write(
    # '''
    # ## Mapping and Filtering Data
    # We can also use Streamlit's built in mapping functionality.
    # Furthermore, we can use a slider to filter for houses within a particular price range.
    # '''
    # )

    # price_input = st.slider('House Price Filter', int(data['PRICE'].min()), int(data['PRICE'].max()), 500000 )

    # price_filter = data['PRICE'] < price_input
    # st.map(data.loc[price_filter, ['lat', 'lon']])


    # # PART 6 - Linear Regression Model

    # st.write(
    # '''
    # ## Train a Linear Regression Model
    # Now let's create a model to predict a house's price from its square footage and number of bedrooms.
    # '''
    # ) 

    # from sklearn.linear_model import LinearRegression
    # from sklearn.model_selection import train_test_split

    # clean_data = data.dropna(subset=['PRICE', 'SQUARE FEET', 'BEDS'])

    # X = clean_data[['SQUARE FEET', 'BEDS']]
    # y = clean_data['PRICE']

    # X_train, X_test, y_train, y_test = train_test_split(X, y)

    # ## Warning: Using the above code, the R^2 value will continue changing in the app. Remember this file is run upon every update! Set the random_state if you want consistent R^2 results.
    # X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

    # lr = LinearRegression()
    # lr.fit(X_train, y_train)

    # st.write(f'Test R²: {lr.score(X_test, y_test):.3f}')


    # # PART 7 - Predictions from User Input

    # st.write(
    # '''
    # ## Model Predictions
    # And finally, we can make predictions with our trained model from user input.
    # '''
    # )

    # sqft = st.number_input('Square Footage of House', value=2000)
    # beds = st.number_input('Number of Bedrooms', value=3)

    # input_data = pd.DataFrame({'sqft': [sqft], 'beds': [beds]})
    # pred = lr.predict(input_data)[0]

    # st.write(
    # f'Predicted Sales Price of House: ${int(pred):,}'
    # )
