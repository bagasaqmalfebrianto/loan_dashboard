import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd

# Set page layout
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    h1, h2, h3, h4, h5, h6, p {
        color: #01314A !important;
    }
    [data-testid="stSidebar"] {
        background-color: #01314A;
        color: #FFFFFF;
    }
    .title {
        text-align: center;
        font-size: 69px;
        color: #01314A;
        padding:20px;
        font-weight: bold;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)


# Judul halaman
st.markdown('<div class="title">Loan Dashboard</div>', unsafe_allow_html=True)

# Read Data
all_df = pd.read_csv("filtered_data.csv")

# Konfigurasi DateTime
datetime_col = ['earliest_cr_line']
all_df.sort_values(by="earliest_cr_line", inplace=True)

for column in datetime_col:
    all_df[column] = pd.to_datetime(all_df[column])

all_df['year'] = all_df['earliest_cr_line'].dt.year

min_date = all_df['earliest_cr_line'].min()
max_date = all_df['earliest_cr_line'].max()

with st.sidebar:
    st.image("show.jpeg")
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["earliest_cr_line"] >= str(start_date)) & 
                 (all_df["earliest_cr_line"] <= str(end_date))]

# FUNCTION AMBIL DATA
def sum_loan(df):
    sum_loan = df.groupby(by="year").agg({
        "loan_amnt": ["sum", 'min', 'max', 'mean'],
        "member_id": "nunique"
    }).reset_index()
    sum_loan.columns = ["year", "loan_sum", "loan_min", "loan_max", "loan_mean", "unique_members"]
    return sum_loan

def good_bad_loan_sum(df):
    loan_counts = df.groupby(by=['year', 'loan_status']).agg({
        'member_id': 'nunique'
    }).reset_index()
    return loan_counts

def get_monthly_trend(df):
    # Membuat kolom `year` dan `month`
    df["year"] = df["earliest_cr_line"].dt.year
    df["month"] = df["earliest_cr_line"].dt.strftime('%B')

    # Mengurutkan bulan sesuai dengan urutan kalender
    order_of_months = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]

    # Mengelompokkan data berdasarkan bulan dan tahun
    monthly_data = df.groupby(["year", "month"]).agg({
        "member_id": "nunique",
    }).reset_index()

    # Mengubah data menjadi pivot untuk memudahkan plotting
    pivot_data = monthly_data.pivot(index="month", columns="year", values="member_id")
    pivot_data = pivot_data.reindex(order_of_months)  # Mengurutkan berdasarkan bulan
    return pivot_data

def get_interest_rate_trend(df):
    # Mengelompokkan data berdasarkan tahun dan menghitung rata-rata suku bunga
    mean_interest_rate_by_year = df.groupby("year")["int_rate"].mean().reset_index()
    return mean_interest_rate_by_year

def get_geo_data(df):
    # Membaca file shapefile untuk data peta
    world_data = gpd.read_file('ne_110m_admin_0_countries.shp')

    # Membuat GeoDataFrame dari data pinjaman
    df_geo = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    return world_data, df_geo

def get_state_aggregated_data(df):
    state_name_to_code = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA',
        'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
        'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
        'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
        'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
        'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
        'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
    }
    df['state_code'] = df['addr_state'].map(state_name_to_code)

    # Hitung jumlah member, jumlah pinjaman tertinggi, dan terendah
    state_agg_data = df.groupby(['addr_state', 'state_code']).agg({
        'member_id': 'nunique',
        'loan_amnt': ['max', 'min', 'mean']
    }).reset_index()

    # Rename kolom agg
    state_agg_data.columns = ['addr_state', 'state_code', 'member_count', 'max_loan', 'min_loan', 'mean']
    return state_agg_data

def prepare_emp_length_data(df):
    # Mengelompokkan data berdasarkan masa kerja dan status pinjaman
    group_masa_kerja = df.groupby(by=["emp_length", "loan_status"]).agg({
        "member_id": "nunique"
    }).reset_index()

    # Membuat pivot table untuk mempersiapkan data visualisasi
    data_to_plot = group_masa_kerja.pivot_table(
        index='emp_length',
        columns='loan_status',
        values='member_id',
        aggfunc='sum',
        fill_value=0
    )

    # Menambahkan kolom total untuk pengurutan
    data_to_plot['Total'] = data_to_plot.sum(axis=1)

    # Mengurutkan data berdasarkan kolom 'Total' secara descending
    data_to_plot = data_to_plot.sort_values(by='Total', ascending=False)

    # Menghapus kolom 'Total' sebelum pengembalian data
    data_to_plot = data_to_plot.drop(columns='Total')

    return data_to_plot

# Fungsi untuk memproses data
def prepare_loan_purpose_data(df):
    # Mengelompokkan data berdasarkan 'purpose' dan 'loan_status'
    loan_counts = df.groupby(['purpose', 'loan_status']).size().unstack(fill_value=0)

    # Menambahkan kolom total peminjam
    loan_counts['total'] = loan_counts.sum(axis=1)

    # Mengurutkan berdasarkan jumlah total peminjam
    loan_counts = loan_counts.sort_values(by='total', ascending=False)

    # Mengambil 5 purpose teratas
    loan_counts_top5 = loan_counts.head(5)

    # Mengonversi DataFrame ke format panjang (long format)
    loan_counts_long = loan_counts_top5.drop(columns='total').reset_index().melt(
        id_vars='purpose',
        value_vars=loan_counts_top5.columns[:-1],
        var_name='loan_status',
        value_name='count'
    )

    return loan_counts_long


def prepare_home_ownership_data(df):
    home_own = df.groupby(by="home_ownership").agg({
        "member_id": "nunique",
    }).reset_index()
    home_own.rename(columns={"member_id": "count"}, inplace=True)
    return home_own


def get_grade_loan_data(df):
    # Mengelompokkan data berdasarkan grade dan status pinjaman
    grade_data = df.groupby(by=["grade", "loan_status"]).agg({
        "member_id": "nunique"
    }).reset_index()
    return grade_data


# AMBIL DATA DARI FUNCTION
sum_loan_df = sum_loan(main_df)
good_bad_loan_sum_df = good_bad_loan_sum(main_df)
trend_data = get_monthly_trend(main_df)
interest_rate_trend_df = get_interest_rate_trend(main_df)
state_agg_data = get_state_aggregated_data(main_df)
data_to_plot = prepare_emp_length_data(main_df)
loan_purpose_data = prepare_loan_purpose_data(main_df)
home_ownership_data = prepare_home_ownership_data(main_df)
grade_data = get_grade_loan_data(main_df)

# # Layout of the dashboard
# with st.container():
#     col1, col2, col3 = st.columns([2, 4, 2])

#     # Left Section - Pie chart
#     with col1:
#         st.subheader("JUDUL")
       

#     # Middle Section - Data Exchange
#     with col2:
    #     # Trend Section

    # # Right Section - Catalog Status
    # with col3:
    #     st.subheader("Catalog Status")

# Baris 1

row1_col1, row1_col2, row1_col3, row1_col4 = st.columns([1, 1, 1, 1])

# Menggunakan container untuk mengelompokkan elemen-elemen
with row1_col1:
    with st.container(border=True):
            total_member = sum_loan_df["unique_members"].sum()
            st.metric(label="Total Member Pinjaman", value=total_member)

       
with row1_col2:
     with st.container(border=True):
           # with row1_col2:
            total_loan = sum_loan_df["loan_sum"].sum()
            st.metric(label="Total Pinjaman", value=total_loan)

with row1_col3:
     with st.container(border=True):
        # Ambil hanya data Good Loan
        good_loan_data = good_bad_loan_sum_df[good_bad_loan_sum_df['loan_status'] == 'Good Loan']
        good_loan_count = good_loan_data['member_id'].sum()
        good_loan_percentage = (good_loan_count / good_bad_loan_sum_df['member_id'].sum()) * 100

        st.metric(label="Distribusi Good Loan", value=f"{good_loan_percentage:.2f}%")

with row1_col4:
     with st.container(border=True):
          bad_loan_data = good_bad_loan_sum_df[good_bad_loan_sum_df['loan_status'] == 'Bad Load']
          bad_loan_count = bad_loan_data['member_id'].sum()
          bad_loan_percentage = (bad_loan_count / good_bad_loan_sum_df['member_id'].sum()) * 100

          st.metric(label="Distribusi Bad Loan",  value=f"{bad_loan_percentage:.2f}%")

# Lower Section

with st.container():
    # col1, col2 = st.columns([1,2])

    # with col1:
    #     st.image("show.jpeg", caption="Sunrise by the mountains")

    # with col2:
        st.subheader("Trend Jumlah Pinjaman Tahunan")
        # Membuat plot menggunakan Plotly untuk interaktif
        fig = go.Figure()

        # Memplot garis untuk setiap tahun
        for year in trend_data.columns:
            fig.add_trace(go.Scatter(x=trend_data.index, y=trend_data[year], mode='lines+markers', name=str(year)))

        # Menambahkan elemen visual lainnya
        fig.update_layout(
            # title="Tren Jumlah Pinjaman Bulanan Berdasarkan Tahun",
            xaxis_title='Bulan',
            yaxis_title='Total Jumlah Pinjaman',
            xaxis_tickangle=-45,
            template='plotly_white',
            legend_title="Tahun",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

with st.container():
    col1, col2, col3 = st.columns([2, 4, 2])

    # Left Section - Department Radar Chart
    with col1:
        st.subheader("Trend Suku Bunga Tahunan")

        # Membuat plot menggunakan Plotly untuk interaktif
        fig_interest = px.bar(
            interest_rate_trend_df,
            x='year',
            y='int_rate',
            labels={'year': 'Tahun', 'int_rate': 'Rata-rata Suku Bunga (%)'},
            template='plotly_white'
        )

        # Menambahkan garis tren
        fig_interest.add_scatter(
            x=interest_rate_trend_df['year'], 
            y=interest_rate_trend_df['int_rate'], 
            mode='lines+markers', 
            name='Trend', 
            line=dict(color='#ef553b', width=3)
        )

        # Mengubah warna bar menjadi #01314A
        fig_interest.update_traces(marker=dict(color='#636efa'))

        # Menyesuaikan layout
        fig_interest.update_layout(
            xaxis_title='Tahun',
            yaxis_title='Rata-rata Suku Bunga (%)',
            xaxis_tickangle=-45,
            hovermode='x unified'
        )

        # Menampilkan plot
        st.plotly_chart(fig_interest, use_container_width=True)

    # Middle Section - Success Rate
    with col2:
        # Visualisasi jumlah peminjam berdasarkan grade dan status pinjaman
        st.subheader('Distribusi Grade Pinjaman')
        grade_fig = px.scatter(
            grade_data,
            x='grade',
            y='member_id',
            color='loan_status',
            labels={'grade': 'Grade', 'member_id': 'Jumlah Peminjam', 'loan_status': 'Status Pinjaman'},
            # title='Jumlah Peminjam Berdasarkan Grade dan Status Pinjaman',
            template='plotly_white'
        )

        st.plotly_chart(grade_fig, use_container_width=True)

    # Right Section - Interface Rank
    with col3:
               # Map Section
        st.subheader("Demografi Pinjaman di Setiap Negara Bagian")

        # Membuat peta choropleth menggunakan Plotly
        fig_map = px.choropleth(
            state_agg_data,
            locations='state_code',
            locationmode="USA-states",
            color='member_count',
            hover_name='addr_state',
            hover_data={
                'member_count': True,
                'max_loan': True,
                'min_loan': True,
                'mean': True,
                'state_code': False
            },
            color_continuous_scale="Blues"
        )

        fig_map.update_layout(
            geo_scope='usa'
        )

        st.plotly_chart(fig_map, use_container_width=True)


with st.container():
    col1, col2, col3 = st.columns([2, 4, 2])

    with col1:
                # Bagian Visualisasi di Streamlit
        st.subheader("Status Kepemilikan Rumah Peminjam")

        # Membuat pie chart interaktif dengan Plotly
        fig_pie = px.pie(
            home_ownership_data,
            names='home_ownership',
            values='count',
            # title='Distribusi Status Kepemilikan Rumah',
            color_discrete_sequence=px.colors.qualitative.Set3,  # Changed to Set3
            hole=0.3  # Membuat donat chart, gunakan 0 untuk pie chart penuh
        )

        fig_pie.update_traces(
            textinfo='percent+label',  # Menampilkan persentase dan label
            pull=[0, 0.1, 0, 0.05],  # Menarik potongan pie tertentu (opsional)
        )

        # Menampilkan pie chart di Streamlit dengan key unik
        st.plotly_chart(fig_pie, use_container_width=True, key="home_ownership_pie_chart")

    with col2:

        st.subheader('Masa Kerja Untuk Setiap Peminjam')
        fig_stacked_bar = px.bar(
            data_to_plot,
            x=data_to_plot.index,
            y=data_to_plot.columns,
            # title='Jumlah Anggota per Masa Kerja dan Status Pinjaman',
            labels={'x': 'Masa Kerja (Emp Length)', 'value': 'Jumlah Anggota', 'variable': 'Status Pinjaman'},
            template='plotly_white',
            barmode='stack'
        )

        # Update layout to reverse x-axis
        fig_stacked_bar.update_layout(
            xaxis_tickangle=-45,
            hovermode='x unified',
            xaxis=dict(
                range=[len(data_to_plot.index)-1, 0],  # Reverses the x-axis range so the largest is on the right
            ),
        )

        # Plot the chart in Streamlit
        st.plotly_chart(fig_stacked_bar, use_container_width=True)

    with col3:
        # Bagian Visualisasi di Streamlit
        st.subheader('Tujuan Melakukan Pinjaman')

        # Membuat bar chart horizontal menggunakan Plotly Express
        fig_barh = px.bar(
            loan_purpose_data,
            y='purpose',  # Purpose berada di sumbu y
            x='count',    # Jumlah pinjaman berada di sumbu x
            color='loan_status',  # Pewarnaan berdasarkan loan_status
            labels={'count': 'Jumlah', 'purpose': 'Purpose', 'loan_status': 'Status Pinjaman'},
            template='plotly_white',
            orientation='h',  # Menyusun chart secara horizontal
            barmode='stack'  # Menggunakan barmode stack untuk status pinjaman
        )

        # Menyesuaikan layout agar lebih rapi
        fig_barh.update_layout(
            xaxis_title='Jumlah',
            yaxis_title='Purpose',
            legend_title_text='Loan Status',
            height=600,
            margin=dict(l=100, r=50, t=50, b=50)  # Mengatur margin untuk tampilan yang lebih baik
        )

        # Menampilkan chart di Streamlit
        st.plotly_chart(fig_barh, use_container_width=True)