# Import required libraries
import pandas as pd
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the airline data into pandas dataframe
spacex_df = pd.read_csv("spacex_launch_dash.csv")
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Create a dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[html.H1('SpaceX Launch Records Dashboard',
                                        style={'textAlign': 'center', 'color': '#503D36',
                                               'font-size': 40}),
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                dcc.Dropdown(
                                    id='site-dropdown',
                                    options=[{'label': 'All Sites', 'value': 'ALL'}] +
                                            [{'label': site, 'value': site} for site in spacex_df['Launch Site'].unique()],
                                    value='ALL',
                                    placeholder="Select a Launch Site here",
                                    searchable=True
                                ),
                                html.Br(),

                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
                                html.Div(dcc.Graph(id='success-pie-chart')),
                                html.Br(),

                                # Slider de payload
                                html.P("Payload range (Kg):"),
                                dcc.RangeSlider(
                                    id='payload-slider',
                                    min=0,
                                    max=10000,
                                    step=1000,
                                    value=[min_payload, max_payload],
                                    marks={0: '0', 2500: '2500', 5000: '5000', 7500: '7500', 10000: '10000'}
                                ),
                                html.Br(),

                                # Scatter chart: correlación entre payload y éxito del lanzamiento
                                html.Div(dcc.Graph(id='success-payload-scatter-chart')),
])


@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def update_pie_chart(selected_site):
    if selected_site == 'ALL':
        # Para "ALL": muestro el total successful launches por sitio (sumo la columna 'class')
        pie_df = spacex_df.groupby('Launch Site')['class'].sum().reset_index()
        fig = px.pie(pie_df,
                    names='Launch Site',
                    values='class',
                    title='Total Successful Launches by Site')
    else:
        # Para un sitio específico: muestro Success vs Failure
        site_df = spacex_df[spacex_df['Launch Site'] == selected_site]
        # Contar éxitos (1) y fracasos (0)
        counts = site_df['class'].value_counts().rename(index={1: 'Success', 0: 'Failure'})
        # Asegurar que existan ambas categorías (para evitar errores si falta alguna)
        counts = counts.reindex(['Success', 'Failure'], fill_value=0)
        pie_df = counts.reset_index()
        pie_df.columns = ['result', 'count']
        fig = px.pie(pie_df,
                    names='result',
                    values='count',
                    title=f'Success vs. Failure for site: {selected_site}')

    fig.update_traces(textinfo='percent+label')
    fig.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    return fig

@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value'),
    Input(component_id='payload-slider', component_property='value')
)
def update_scatter_chart(selected_site, payload_range):
    # Desempacar rango
    low, high = payload_range if isinstance(payload_range, (list, tuple)) else (min_payload, max_payload)
    # Filtrar por rango de payload
    mask = (spacex_df['Payload Mass (kg)'] >= low) & (spacex_df['Payload Mass (kg)'] <= high)
    filtered_df = spacex_df[mask]

    # Determinar columna de color para boosters
    if 'Booster Version Category' in spacex_df.columns:
        color_col = 'Booster Version Category'
    elif 'Booster Version' in spacex_df.columns:
        color_col = 'Booster Version'
    else:
        color_col = None  # si no existe, no coloreamos por booster

    # If-Else: ALL sites vs specific site
    if selected_site == 'ALL':
        scatter_df = filtered_df
        title = 'Payload vs Outcome for all sites'
    else:
        scatter_df = filtered_df[filtered_df['Launch Site'] == selected_site]
        title = f'Payload vs Outcome for {selected_site}'

    # Crear scatter plot: x = Payload Mass (kg), y = class (0/1)
    if color_col:
        fig = px.scatter(
            scatter_df,
            x='Payload Mass (kg)',
            y='class',
            color=color_col,
            hover_data=['Launch Site', 'Payload Mass (kg)'],
            title=title,
            labels={'class': 'Launch Outcome (1=Success, 0=Failure)'}
        )
    else:
        fig = px.scatter(
            scatter_df,
            x='Payload Mass (kg)',
            y='class',
            hover_data=['Launch Site', 'Payload Mass (kg)'],
            title=title,
            labels={'class': 'Launch Outcome (1=Success, 0=Failure)'}
        )

    # Ajustes estéticos mínimos
    fig.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    fig.update_yaxes(tickvals=[0, 1], title_text='Launch Outcome (class)')
    fig.update_xaxes(title_text='Payload Mass (kg)')
    return fig


# Run the app
if __name__ == '__main__':
    app.run()
