#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
from chart_studio import plotly as py
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
import requests
import streamlit as st
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


## PART 1 - Intro

st.write('''
# Let us help you find your next apartment!
Did you get a new job in the DC/VA/MD area? Are you considering moving closer to work? Will paying more for an apartment closer to work to reduce your commute time actually make sense financially? Let us help you answer that question!
In the fields below, please enter an address for your new job location and we will help you find your next apartment! Be sure to spell everything correctly! Caps are optional.
In the final version, apartment listings will come from a real estate website like [apartments.com](https://www.apartments.com).
''')


# PART 2 - Get user's target location, speed, hourly wage

st.write(
'''
## Enter your workplace location in the fields below.

''')

with st.form(key='user_info'):
    street = st.text_input('Street', max_chars=100, value='932 N Kenmore St')
    city = st.text_input('City', max_chars=100, value='Arlington')
    state = st.text_input('State', max_chars=2, value='VA')
    zipcode = st.text_input('Zip', max_chars=5, value='22201')

    address = street + ' ' + city + ' ' + state + ' ' + zipcode

    st.write(
    '''
    ## Enter your hourly wage ($ per hour)
    This will let us determine how much your time spent commuting is worth to you. The more time spent commuting, the higher your effective rent will be.
    ''')

    hourly_income = st.number_input('Hourly wage', value=40)

    # st.write('''
    # ## Enter your anticipated average commuting speed
    # The default is 40 mph.
    # ''')

    # speed = st.number_input('Speed', min_value=1, max_value=70, value=40)

    mode = st.radio('How will you get to work?', ('Drive', 'Bike', 'Walk'))
    mode = mode.replace('Drive', 'driving').replace('Walk', 'walking').replace('Bike', 'cycling')

    st.write('''
    ## Select your desired range of rents
    ''')

    rental_range = st.slider('Range of rents', value=[1500, 3500], min_value=1400, max_value = 4000)

    apt_types = st.multiselect('Select the types of apartments to search for.', ['Studio', 'One bedroom', 'Two bedrooms'], ['Studio', 'One bedroom', 'Two bedrooms'])
    apt_types = [apt.replace('Studio', 'studio').replace('One bedroom', '1_br').replace('Two bedrooms', '2_br') for apt in apt_types]  
    
    st.write('''
        Note, you must click "Submit" to create/update the map if you make a change to the search parameters above.
    ''')

    with open('mapbox_key.txt') as f:
        mapbox_access_token = f.read().rstrip()

    submit_button = st.form_submit_button(label='Submit')

if submit_button:
# PART 3 - Generate random apartment listings. This will be replaced with real listings in the actual deployment.    
    # st.write(apt_types)
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

    def get_geocoords(address=address):
        workplace = urllib.parse.quote(address)
        try: url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{workplace}.json?access_token={mapbox_access_token}'
        except IndexError:
            st.write('Check your address again for typos. The address must be within the immediate DC/MD/VA area.')
            return
        session = requests.session()
        location = session.get(url)
        return location.json()['features'][0]['center']

    workplace = get_geocoords(address)[::-1]

    # PART 4 - Show graph of listings

    # There is a bug in plotly where if you set the marker style, the color defaults to gray.
    # https://github.com/plotly/plotly.py/issues/2485
    # https://github.com/plotly/plotly.js/issues/2813 ('Note that the array `marker.color` and `marker.size`', are only available for *circle* symbols.')

    results = generate_listings()

    def isochrone_layer(mode, minutes, workplace=workplace): # minutes = '10,20,30'
        profile = f'mapbox/{mode}'
        coordinates = str(workplace[1]) + ',' +  str(workplace[0])
        contours_minutes = f'contours_minutes={minutes}'
        r = requests.get(f'https://api.mapbox.com/isochrone/v1/{profile}/{coordinates}?{contours_minutes}&polygons=true&access_token={mapbox_access_token}').json()
        results = []
        if minutes == '10,20,30': colors = ['red', 'yellow', 'lime'] # colors go in most to least travel time
        else: colors = ['purple']
        length = len(minutes.split(','))
        for i in range(length):
            results += [
        {
                    'source': {
                        'type': "FeatureCollection",
                        'features': [{
                            'type': "Feature",
                            'geometry': {
                                'type': "MultiPolygon",
                                'coordinates': [r['features'][i]['geometry']['coordinates']]                               
            }
                        }]
                    },
                                'type': "fill", 'below': "traces", 'color': f"{colors[i]}", 'opacity': 0.15}]
        return results

    # Get the isochrone data
    ten_thirty_layer = isochrone_layer(mode, '10,20,30')
    forty_layer = isochrone_layer(mode, '40')

    # There is a bug in plotly where if you set the marker style, the color defaults to gray.
    # https://github.com/plotly/plotly.py/issues/2485
    # https://github.com/plotly/plotly.js/issues/2813 ('Note that the array `marker.color` and `marker.size`', are only available for *circle* symbols.')
  
    # create list of polygons
    polygons = [Polygon(ten_thirty_layer[i]['source']['features'][0]['geometry']['coordinates'][0][0]) for i in range(2, -1, -1)] + [Polygon(forty_layer[0]['source']['features'][0]['geometry']['coordinates'][0][0])]    
               
    def which_polygon(point, polygons): # returns bool if point in polygon. Will loop through polys from smallest to largest.
        point = Point(point) # create point
        point_found = False
        for i in range(4):
            if polygons[i].contains(point): # check if polygon contains point
                point_found = True
                break
        if not point_found: return 4
        else: return i    

    results['polygon'] = results.apply(lambda x: which_polygon([x.long, x.lat], polygons), axis=1)
    results['adjusted_rent'] = (results['rent'] + (results['polygon'] +1) * 10 * 2 * 20 /60 * 40).astype('int')
    results = results[(results.adjusted_rent <= rental_range[1]) & (results.adjusted_rent >= rental_range[0]) & (results.type.isin(apt_types))]
    results['commute time (minutes)'] = results.apply(lambda x: '<10' if x.polygon == 0 else '10-20' if x.polygon == 1 else '20-30' if x.polygon == 2 else '30-40' if x.polygon == 3 else '>40', axis=1)

    px.set_mapbox_access_token(mapbox_access_token)
    fig = px.scatter_mapbox(results, lat="lat", lon="long", hover_name="type", hover_data=["rent"],
                            color="adjusted_rent", zoom=12, height=600)

    fig.update_layout(mapbox_style="light")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    fig.add_trace(go.Scattermapbox(
            lat=[workplace[0]],
            lon=[workplace[1]],
            marker=go.scattermapbox.Marker(
            size=25,
            color='red',          
            ),
            marker_symbol = 'star',
            hoverinfo = 'none',
            showlegend = False
            )  
        )
    fig.update_layout(
        mapbox = {
            'style': "light",
            'center': { 'lon': workplace[1], 'lat': workplace[0]},
            'zoom': 12, 'layers': ten_thirty_layer + forty_layer
        },
        margin = {'l':0, 'r':0, 'b':0, 't':0})

    st.plotly_chart(fig) 

    st.write('''
    ## The cheapest apartments for each commute length
    ''')
    results = results.sort_values('adjusted_rent').groupby('commute time (minutes)').head(3)
    results.index = results.groupby('polygon').cumcount() + 1
    results.drop('polygon', axis=1, inplace=True)
    results = results.reset_index().rename(columns = {'index': 'rank', 'adjusted_rent': 'effective rent'})

    # Reorder columns to put rents next to one another
    results = results.reindex(columns=['rank', 'rent', 'effective rent', 'lat', 'long', 'type', 'commute time (minutes)'])
    

    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                tbody th {display:none}
                .blank {display:none}
                </style>
                """

    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    st.table(results)

    st.write('''
    ## Future work
    The final version will use data scraped from a real estate listings site such as [apartments.com](https://www.apartments.com). You will see addresses in the table above instead of latitude and longitude.
    '''
    )




