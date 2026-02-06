import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from streamlit_folium import st_folium
import folium

sns.set(style='dark')

# Load data dengan cache agar data original tidak berubah
@st.cache_data
def load_data():
    monthly_orders_df = pd.read_csv('dashboard/monthly_orders_df.csv')
    monthly_revenue_order_df = pd.read_csv('dashboard/monthly_revenue_order_df.csv')
    customers_orders_and_payment = pd.read_csv('dashboard/customers_orders_and_payment.csv')
    orders_customers_geolocation_df = pd.read_csv('dashboard/orders_customers_geolocation_df.csv')
    
    # Ubah type data
    customers_orders_and_payment["order_delivered_customer_date"] = pd.to_datetime(
        customers_orders_and_payment["order_delivered_customer_date"],
    )
    monthly_orders_df["order_delivered_customer_date"] = pd.to_datetime(
        monthly_orders_df["order_delivered_customer_date"], format='%B - %Y'
    )
    monthly_revenue_order_df["order_delivered_customer_date"] = pd.to_datetime(
        monthly_revenue_order_df["order_delivered_customer_date"], format='%B - %Y'
    )
    orders_customers_geolocation_df["order_delivered_customer_date"] = pd.to_datetime(
        orders_customers_geolocation_df["order_delivered_customer_date"]
    )
    
    return monthly_orders_df, monthly_revenue_order_df, customers_orders_and_payment, orders_customers_geolocation_df

# Load data original
monthly_orders_df_orig, monthly_revenue_order_df_orig, customers_orders_and_payment_orig, orders_customers_geolocation_df_orig = load_data()

st.header('E-Commerce Public Dashboard :sparkles:')

min_date = monthly_orders_df_orig['order_delivered_customer_date'].min()
max_date = monthly_orders_df_orig['order_delivered_customer_date'].max()

# Interaktif dengan rentang waktu
with st.sidebar:
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter data berdasarkan tanggal tanpa mengubah data original
monthly_orders_df = monthly_orders_df_orig[(monthly_orders_df_orig['order_delivered_customer_date'] >= start_date) & 
                                            (monthly_orders_df_orig['order_delivered_customer_date'] <= end_date)].copy()

monthly_revenue_order_df = monthly_revenue_order_df_orig[(monthly_revenue_order_df_orig['order_delivered_customer_date'] >= start_date) & 
                                            (monthly_revenue_order_df_orig['order_delivered_customer_date'] <= end_date)].copy()

orders_customers_geolocation_df = orders_customers_geolocation_df_orig[(orders_customers_geolocation_df_orig['order_delivered_customer_date'] >= start_date) & 
                                            (orders_customers_geolocation_df_orig['order_delivered_customer_date'] <= end_date)].copy()

customers_orders_and_payment = customers_orders_and_payment_orig[(customers_orders_and_payment_orig['order_delivered_customer_date'] >= start_date) & 
                                            (customers_orders_and_payment_orig['order_delivered_customer_date'] <= end_date)].copy()

# Pertanyaan 1, Tren jumlah pesanan dan pendapatan e-commerce
st.subheader('Tren Jumlah Pesanan dan Pendapatan E-Commerce')
fig, ax =  plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

# Tren jumlah pesanan
ax[0].plot(
    monthly_orders_df['order_delivered_customer_date'],
    monthly_orders_df['total_orders'],
    marker='o',
    linewidth=2,
    color='#72BCD4'
)
ax[0].set_title("Number of Orders per Month", loc="center", fontsize=15) 
ax[0].set_xlabel("Month", fontsize=10)
ax[0].set_ylabel("Number of Orders", fontsize=10)
ax[0].tick_params(axis='x', labelsize=10, rotation=45)
ax[0].tick_params(axis='y', labelsize=10)

# Tren pendapatan e-commerce
ax[1].plot(
    monthly_revenue_order_df['order_delivered_customer_date'],
    monthly_revenue_order_df['total_revenue'],
    marker='o',
    linewidth=2,
    color='#72BCD4'
)
ax[1].set_title("Total Revenue per Month", loc="center", fontsize=15) 
ax[1].set_xlabel("Month", fontsize=10)
ax[1].set_ylabel("Total Revenue", fontsize=10)
ax[1].tick_params(axis='x', labelsize=10, rotation=45)
ax[1].tick_params(axis='y', labelsize=10)
ax[1].ticklabel_format(style='plain', axis='y')

st.pyplot(fig)

# Pertanyaan 3
# Urutkan
orders_customers_geolocation = orders_customers_geolocation_df.groupby(
    'customer_state',
    as_index=False
).agg({
    'order_id': 'count'
})
orders_customers_geolocation.columns = ['customer_state', 'total_orders']

# Urutkan
orders_customers_geolocation = orders_customers_geolocation.sort_values(
    'total_orders',
    ascending=False
)
# ambil top 5
top5 = orders_customers_geolocation.head(5)

# gabungkan sisanya jadi "Others"
others = orders_customers_geolocation.iloc[5:]['total_orders'].sum()

top5_with_others = pd.concat([
    top5,
    pd.DataFrame({
        'customer_state': ['Others'],
        'total_orders': [others]
    })
])

st.subheader('Top 5 Negara dengan Kontribusi Pesanan Terbesar')
fig, ax = plt.subplots(figsize=(10, 5))
ax.pie(
    x=top5_with_others['total_orders'],
    labels=top5_with_others['customer_state'],
    autopct='%1.1f%%',
    textprops={'fontsize': 10},
)
ax.set_title('Top 5 Negara dengan Kontribusi Pesanan Terbesar + Others Combine', fontsize=15)
st.pyplot(fig)


# Pertanyaan 2, 4 ,5 akan dibuat rfm nya terlebih dahulu
def create_rfm(customers_orders_and_payment):
    rfm_df = customers_orders_and_payment.groupby('customer_unique_id', as_index=False).agg({
        'order_delivered_customer_date': 'max',
        'order_id': 'count',
        'payment_value': 'sum'
    })

    rfm_df.columns = ['customer_unique_id', 'max_order_timestamp', 'frequency', 'monetary']

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = customers_orders_and_payment["order_delivered_customer_date"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

# Kelompok atau segmen pelanggan
def segmen_pelanggan_tertinggi (customers_orders_and_payment):
    # Membuat clustering berdasarkan payment_type dan kelompok_payment_value
    clustering_df = customers_orders_and_payment.groupby(['payment_type', 'kelompok_payment_value']).agg({
        'order_id': 'count',
        'customer_unique_id': 'nunique',
        'customer_state': lambda x: x.mode()[0]
    }).rename(columns={
        'order_id': 'total_orders',
        'customer_unique_id': 'unique_customers',
        'customer_state': 'top_state'
    }).reset_index()

    # Membuat clustering berdasarkan kelompok payment_value sangat tinggi sebagai utamanya
    def top_5_states(x):
        return ', '.join(x.value_counts().head(5).index)

    clustering_payment_value_df = customers_orders_and_payment.groupby(['payment_type', 'kelompok_payment_value']).agg({
        'order_id': 'count',
        'customer_unique_id': 'nunique',
        'customer_state': top_5_states,
        'payment_value': 'mean'
    }).rename(columns={
        'order_id': 'total_orders',
        'customer_unique_id': 'unique_customers',
        'customer_state': 'top_state',
        'payment_value' : 'payment_value'
    }).reset_index()

    clustering_payment_value_df = clustering_payment_value_df[clustering_payment_value_df['kelompok_payment_value'] == 'Sangat tinggi']
    return clustering_payment_value_df

rfm_df = create_rfm(customers_orders_and_payment)
clustering_payment_value_df = segmen_pelanggan_tertinggi(customers_orders_and_payment)

st.subheader('Best Customer Based on RFM Parameters (customer_unique_id)')
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15, 5))
 
colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]
 
# By Recency
sns.barplot(
    x="recency",
    y="customer_unique_id",
    data=rfm_df.sort_values(by="recency", ascending=True).head(5),
    palette=colors,
    ax=ax[0]
)
ax[0].set_title("By Recency (days)", loc="center", fontsize=15)
ax[0].tick_params(axis='y', labelsize=10)
ax[0].set_xlim(left=0)

# By Frequency
sns.barplot(
    x="frequency",
    y="customer_unique_id",
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5),
    palette=colors,
    ax=ax[1]
)
ax[1].set_title("By Frequency", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=10)

plt.tight_layout()
st.pyplot(fig)

# By Monetary
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 5))
sns.barplot(
    x="monetary",
    y="customer_unique_id",
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5),
    palette=colors,
    ax=ax
)
ax.set_title("By Monetary", loc="center", fontsize=15)
ax.tick_params(axis='y', labelsize=10)

st.pyplot(fig)

st.dataframe(clustering_payment_value_df, width=1000, height=200)

# Mempersilahkan melihat detail customer
st.subheader('Customer Details and Location')
selected_customer = st.selectbox(
    "Pilih customer",
    rfm_df["customer_unique_id"].unique()
)

# Filter customer location berdasarkan selected_customer
customer_location_df = orders_customers_geolocation_df[
    orders_customers_geolocation_df["customer_unique_id"] == selected_customer
][["customer_zip_code_prefix",
    "customer_city",
    "customer_state",
    "geolocation_lat",
    "geolocation_lng",
    ]].drop_duplicates()

st.write("Informasi lokasi customer:")
st.dataframe(customer_location_df.head(1), width=1000, height=50)

# Tampilkan lokasi
st.subheader('Customer Location')
if not customer_location_df.empty:
    lat = customer_location_df.iloc[0]["geolocation_lat"]
    lng = customer_location_df.iloc[0]["geolocation_lng"]
    city = customer_location_df.iloc[0]["customer_city"]
    state = customer_location_df.iloc[0]["customer_state"]
    
    m = folium.Map(
        location=[lat, lng],
        zoom_start=12
    )

    folium.Marker(
        [lat, lng],
        popup=f"{city} - {state}"
    ).add_to(m)
    
    st.write('Lokasi Customer')
    st_folium(m, width=700, height=500, key=f"map_{selected_customer}")
else:
    st.warning("Tidak ada data lokasi untuk customer yang dipilih")
