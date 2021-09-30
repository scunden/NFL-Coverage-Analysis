#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sn
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.io as pio
from IPython.core.display import HTML
from matplotlib.pyplot import figure
from os import listdir
from os.path import isfile, join
import re


# In[5]:




# function that will generate a trace for each player at the first instance of the play (frame==1)
def generate_traces(df, color_map):
    traces=[]
    for player in df.displayName.unique():

        trace = go.Scatter(
            x=df[(df['displayName']==player)&(df['frameId']==1)].x,
            y=df[(df['displayName']==player)&(df['frameId']==1)].y,
            name=player,
            mode="markers",
            marker=dict(
                size=df[(df['displayName']==player)&(df['frameId']==1)].s+10,
                color=color_map[df[(df['displayName']==player)]['team'].unique()[0]]
            )
        )

        traces.append(trace)
    return traces

# function generates frame for each instance (and instance before that) for each player
def generate_frames(df, color_map, cummulative=True):
    if cummulative:
        frames = [go.Frame(
            data = [go.Scatter(
                x = df[(df['displayName']==player)&(df['frameId'].isin(range(2,k)))].x,
                y = df[(df['displayName']==player)&(df['frameId'].isin(range(2,k)))].y,
                name=player,
                mode="markers",
                marker=dict(
                    size=df[(df['displayName']==player)&(df['frameId'].isin(range(2,k)))].s+10,
                    color=color_map[df[(df['displayName']==player)]['team'].unique()[0]]
                )
            )
                    for player in df.displayName.unique()
                   ])
                  for k  in  range(2,df.frameId.unique().shape[0]+1)]
    else:
        frames = [go.Frame(
            data = [go.Scatter(
                x = df[(df['displayName']==player)&(df['frameId'].isin(range(k-1,k)))].x,
                y = df[(df['displayName']==player)&(df['frameId'].isin(range(k-1,k)))].y,
                name=player,
                mode="markers",
                marker=dict(
                    size=df[(df['displayName']==player)&(df['frameId'].isin(range(k-1,k)))].s+10,
                    color=color_map[df[(df['displayName']==player)]['team'].unique()[0]]
                )
            )
                    for player in df.displayName.unique()
                   ])
                  for k  in  range(2,df.frameId.unique().shape[0]+1)]
    
    return frames

# Generate an initial layout that has a play button
def generate_layout():
    layout = go.Layout(
        updatemenus=[
            dict(
                type='buttons', 
                showactive=False,
                y=0,
                x=0,
                xanchor='left',
                yanchor='top',
                pad=dict(t=0, r=10),
                buttons=[dict(
                    label='Play',
                    method='animate',
                    args=[None, 
                          dict(
                              frame=dict(duration=100, redraw=False),
                              transition=dict(duration=0),
                              fromcurrent=True,
                              mode='immediate')
                         ])])])
    return layout


# Generate a field layout - i.e., enhancing the graph to make it look like a football field
def generate_field_layout(fig, layout, color_map,df, playid, cummulative=True):
    home_color = color_map['home']
    layout.update(xaxis =dict(range=[0,120], autorange=False),
                  yaxis =dict(range=[0,54], autorange=False));


    # Add background color and remove x and y axis labels and ticks
    fig.update_layout(plot_bgcolor='#567d46')
    fig.update_yaxes(showgrid=False, showticklabels=False, visible=False)
    fig.update_xaxes(showgrid=False, showticklabels=False, visible=False)

    # Add Endzone Regions
    fig.add_vrect(x0=0, x1=10,fillcolor=home_color, opacity=1,layer="below", line_width=0,)
    fig.add_vrect(x0=110, x1=120,fillcolor=home_color, opacity=1,layer="above", line_width=0,)

    # Add annotations in the end zones
    fig.add_annotation(x=5, y=27,text="HOME END ZONE",showarrow=False,textangle=-90,font=dict(size=24, color="white"))
    fig.add_annotation(x=115, y=27,text="AWAY END ZONE",showarrow=False,textangle=90,font=dict(size=24, color="white"))

    mp = {10:"G",20:"10",30:"20",40:"30",50:"40",60:"50",70:"40",80:"30",90:"20",100:"10",110:"G"}

    for line in range(10,120,10):
        # Add field lines and labels at the 5 and 10 yard increment markers
        fig.add_annotation(x=line, y=2,text=mp[line],showarrow=False, font=dict(size=16, color="white"))
        fig.add_annotation(x=line, y=52,text=mp[line],showarrow=False, font=dict(size=16, color="white"),textangle=180)
        fig.add_vline(x=line, line_width=3, line_color="white", opacity=0.5)
        if line < 110:
            fig.add_vline(x=line+5, line_width=0.5, line_color="white", opacity=0.5)
    
    # Generate Title 
    if cummulative:
        cummulative=" Cummulative Tracking using Plotly"
    else:
        cummulative=" Non-Cummulative Tracking using Plotly"
        
    fig.update_layout(
        title_text='{} v {} - Play #{}{}'.format(
            df.homeTeamAbbr.unique()[0],
            df.visitorTeamAbbr.unique()[0],
            playid,
            cummulative
        ),
        
        font=dict(size=18),
        title_x=0.5
    )
    
    fig.update(layout_showlegend=False)

    return fig, layout

# Generate dataframe based on play id and generate home and away color themes
def generate_df(df, week, gameid, playid):
    # Defining color map for teams
    team_map = {
    'ARI':'#97233F',
    'ATL':'#A71930',
    'BAL':'#241773',
    'BUF':'#00338D',
    'CAR':'#0085CA',
    'CHI':'#0B162A',
    'CIN':'#FB4F14',
    'CLE':'#311D00',
    'DAL':'#003594',
    'DEN':'#FB4F14',
    'DET':'#0076B6',
    'GB':'#203731',
    'HOU':'#03202F',
    'IND':'#002C5F',
    'JAX':'#101820',
    'KC':'#E31837',
    'LA':'#003594',
    'LAC':'#002A5E',
    'MIA':'#008E97',
    'MIN':'#4F2683',
    'NE':'#002244',
    'NO':'#D3BC8D',
    'NYG':'#0B2265',
    'NYJ':'#125740',
    'OAK':'#000000',
    'PHI':'#004C54',
    'PIT':'#FFB612',
    'SEA':'#69BE28',
    'SF':'#AA0000',
    'TB':'#D50A0A',
    'TEN':'#0C2340',
    'WAS':'#773141',
    }
    
    df = df[(df['week']==week)&(df['playId']==playid)&(df['gameId']==gameid)]
    df = df.sort_values(by=['team','displayName','frameId'])
    
    color_map = {'football':'#8c564b'}
    color_map.update({'home':team_map[df.homeTeamAbbr.unique()[0]]})
    color_map.update({'away':team_map[df.visitorTeamAbbr.unique()[0]]})
    
    return df, color_map
    
def vis_play(weeklyData, week, gameid, playid, cummulative=False):
    play, color_map = generate_df(weeklyData, week, gameid, playid)

    layout=generate_layout()
    fig = go.Figure(data=generate_traces(play, color_map), 
                    frames=generate_frames(play, color_map, cummulative=cummulative),
                    layout=layout)
    fig, layout = generate_field_layout(fig, layout, color_map, play, playid, cummulative=cummulative)
    fig.show()


# In[6]:


# playid = 75
# week='1'
# gameid=2018090600
# vis_play(weeklyData, week, gameid, playid, cummulative=True)


# In[ ]:





# In[ ]:




