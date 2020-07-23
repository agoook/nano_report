import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px


@st.cache
def get_xy_df():
    response = requests.post('https://www.agoook.ru/nano/analysis/xy',
                             json={'table': 'e2f77c4e1589aa599201c1eca6801731'})
    json = response.json()
    meta_df = pd.DataFrame(json['records'])
    return meta_df


@st.cache
def get_xy_dict():
    meta_df = get_xy_df()
    meta_dict = dict(zip(meta_df.id, meta_df.text))
    return meta_dict


@st.cache
def get_report():
    response = requests.get('https://www.agoook.ru/nano/analysis/report?report=e2f77c4e1589aa599201c1eca6801731')
    json = response.json()
    nanotubes_df = pd.DataFrame(json['records'])
    nanotubes_df[nanotubes_df.columns[2:18]] = nanotubes_df[nanotubes_df.columns[2:18]].astype(float)
    meta_dict = get_xy_dict()
    nanotubes_df.rename(columns=meta_dict, inplace=True)
    nanotubes_df = nanotubes_df.loc[nanotubes_df['Срез'].isin([0, .5])]

    return nanotubes_df


def show_table(nanotubes_df):
    st.subheader('Данные со снимков ПЭМ')
    sample_num = st.selectbox('Выберите образец', ['*'] + nanotubes_df['Номер образца'].unique().tolist())
    df = nanotubes_df.loc[nanotubes_df['Номер образца'] == sample_num] if sample_num != '*' else nanotubes_df
    per_page = 10
    page = st.slider('Страница:', 1, len(df) // per_page, 1)
    st.table(df.iloc[((page - 1) * per_page):(page * per_page), :18])


def show_group_table(nanotubes_df):
    st.subheader('Сводная таблица по образцам и срезам')
    nanotubes_gb = nanotubes_df.groupby(['Номер образца', 'Срез']).agg({
        'Температура синтеза, C': ['mean'], 'Расход аргона, мл/мин': ['mean'],
        'Время синтеза, мин': ['mean'], 'Расход смеси этанол/вода, мл/мин': ['mean'],
        'Толщина кольца, нм': ['mean', 'std'],
        'Скорость роста кольца, нм/мин': ['mean', 'std'],
    })
    nanotubes_gb.columns = ['Температура синтеза, C', 'Расход аргона, мл/мин', 'Время синтеза, мин',
                            'Расход смеси этанол/вода, мл/мин',
                            'Толщина кольца, нм', 'Толщина кольца, стандартное отклонение',
                            'Скорость роста кольца, нм/мин', 'Скорость роста кольца, нм/мин, стандартное отклонение']
    nanotubes_gb.reset_index(inplace=True)
    st.table(nanotubes_gb)


def show_group_line(nanotubes_df, param, filter={}):
    st.subheader(f'Изменение скорости роста в зависимости от параметра - {param}')
    df = nanotubes_df
    if filter.keys():
        filter_df = pd.Series(np.full((len(nanotubes_df)), True))
        filter_str = ''
        for col, val in filter.items():
            filter_df = filter_df & (nanotubes_df[col] == val)
            filter_str += f'{col}: {val}; '
        df = nanotubes_df.loc[filter_df]
        st.text(filter_str)
    if len(df):
        nanotubes_gb = df.groupby([param, 'Срез']).agg({
            'Толщина кольца, нм': ['mean', 'std'],
            'Скорость роста кольца, нм/мин': ['mean', 'std'],
        })
        nanotubes_gb.columns = [
            'Толщина кольца, нм', 'Толщина кольца, стандартное отклонение',
            'Скорость роста кольца, нм/мин', 'Скорость роста кольца, стандартное отклонение']
        nanotubes_gb.reset_index(inplace=True)

        fig = px.line(nanotubes_gb, x=param, y='Скорость роста кольца, нм/мин',
                      error_y='Скорость роста кольца, стандартное отклонение',
                      line_group='Срез', color='Срез',
                      line_shape="spline", render_mode="svg")
        st.plotly_chart(fig, use_container_width=True)
        st.table(nanotubes_gb)
    else:
        st.info('Данные удовлетворяющие фильтру отсутствуют')


def show_points_scatter(nanotubes_df):
    st.subheader('Скорость роста кольца в зависимости от образца')
    fig = px.scatter(nanotubes_df, x='Скорость роста кольца, нм/мин', y='Номер образца', hover_data=['Номер образца'],
                     color='Диаметр (внутренний), нм', size='Время синтеза, мин', symbol='Номер образца')
    fig.update_layout(
        # autosize=False,
        height=500,
        # width=1200,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ))
    st.plotly_chart(fig, use_container_width=True)


def show_points_parallel(nanotubes_df):
    st.subheader('Данные по нанотрубкам в параллельных координатах')
    fig = px.parallel_coordinates(
        nanotubes_df, color='Толщина кольца, нм',
        dimensions=['Диаметр (внутренний), нм', 'Температура синтеза, C',
                    'Расход аргона, мл/мин', 'Скорость роста кольца, нм/мин',
                    'Время синтеза, мин', 'Расход смеси этанол/вода, мл/мин'],
        color_continuous_scale=px.colors.diverging.Tealrose,
        color_continuous_midpoint=7)
    fig.update_layout(
        # autosize=False,
        height=700)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
    st.title('Отчёт по мембранам')
    # st.sidebar.title('Настройки')

    nanotubes_df = get_report()

    show_table(nanotubes_df)
    show_points_scatter(nanotubes_df)
    show_points_parallel(nanotubes_df)
    show_group_table(nanotubes_df)

    show_group_line(nanotubes_df, 'Температура синтеза, C',
                    {
                        'Расход аргона, мл/мин': 200,
                        'Расход смеси этанол/вода, мл/мин': 0.083,
                    })
    show_group_line(nanotubes_df, 'Расход аргона, мл/мин',
                    {
                        'Температура синтеза, C': 750,
                        'Расход смеси этанол/вода, мл/мин': 0.083,
                    })
    show_group_line(nanotubes_df, 'Расход смеси этанол/вода, мл/мин',
                    {
                        'Температура синтеза, C': 750,
                        'Расход аргона, мл/мин': 200,
                    })
    # show_group_line(nanotubes_df, 'Время синтеза, мин',
    #                 {
    #                     'Температура синтеза, C': 750,
    #                     'Расход смеси этанол/вода, мл/мин': 0.083,
    #                     'Расход аргона, мл/мин': 200
    #                 })
