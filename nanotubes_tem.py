import streamlit as st
import requests
import pandas as pd
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
    per_page = 10
    page = st.slider('Страница:', 1, len(nanotubes_df) // per_page, 1)
    st.table(nanotubes_df.iloc[((page - 1) * per_page):(page * per_page), :18])


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


def show_group_line(nanotubes_df, param):
    st.subheader(f'Изменение скорости роста в зависимости от параметра - {param}')
    nanotubes_gb = nanotubes_df.groupby([param, 'Срез']).agg({
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

    show_group_line(nanotubes_df, 'Время синтеза, мин')
    show_group_line(nanotubes_df, 'Расход аргона, мл/мин')
