
import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np 
import seaborn as sns
import matplotlib.ticker as ticker 
import matplotlib.cm as cm 
from IPython.display import display
from warnings import filterwarnings
filterwarnings('ignore')

#setting professional color themes 
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")

viridis_color = cm.viridis(np.linspace(0, 1, 10))
primary_color = viridis_color[0]
secondary_color = viridis_color[1]
accent_color = viridis_color[2]
danger_color = '#800000'
neutral_color = viridis_color[4]
custom_palette = viridis_color

# Load the dataset
df = pd.read_csv("DataCoSupplyChainDataset (3).csv", encoding="latin1")
df.columns = df.columns.str.lower().str.replace(' ','_')

# print(df.columns.to_list())
# print(f"Dublicate values are :{df.duplicated().sum()}")
# print( df.isna().sum().sort_values(ascending=False).head(20))


#data cleaing
columns_to_drop = [
    'product_description',
    'product_image',
    'customer_email',
    'customer_password',
    'customer_lname',
    'customer_fname',
    'customer_street',
    'customer_zipcode',
    'order_zipcode',
    'latitude',
    'longitude',
    'order_item_cardprod_id',
    'order_item_id',
    'order_item_discount',
    'order_item_discount_rate',
    'order_item_product_price',
    'order_item_quantity',
    'order_item_total',
    'category_id',
    'department_id',
    'order_id',
    'order_customer_id',
    'customer_id',
    'product_card_id',
    'product_category_id',
    'benefit_per_order',
    'product_status',
    'customer_city',
    'order_city',
    'order_country',
    'order_state',
    'customer_state',
    'market',
]
df= df.drop(columns=columns_to_drop)

#removing canceled orders 
df = df[df['order_status'] != 'shipping_canceled']

#standerd date conversation
for c in ['order_date_(dateorders)',
          'shipping_date_(dateorders)']:
    df[c] = pd.to_datetime(df[c], errors='coerce', dayfirst=False)

#checking the data 
# print(df.shape)
# print(df.isna().sum().sort_values(ascending=False).head(5))


# values counts for categorical columns with low cardinality
# for col in df.columns:
#     if df[col].nunique()< 10:
#         print(f"\n {col} value counts:")
#         print(df[col].value_counts())

#order processing time

df['order_processing_time'] = (df['shipping_date_(dateorders)'] - df['order_date_(dateorders)']).dt.days
df['delay']= df['order_processing_time']- df['days_for_shipment_(scheduled)']
df['is_delayed'] = df['delay']>0
df['order_month'] = df['order_date_(dateorders)'].dt.month
df['order_day'] = df['order_date_(dateorders)'].dt.day_name()

df['order_hour'] = df['order_date_(dateorders)'].dt.hour
# i want full columns to be visible
pd.set_option('display.max_columns', None)
print(df.describe())



#profitability flag based on order profit per order

df['profitability_flag'] = np.where(df['order_profit_per_order'] > 0 , 
'profit', np.where(df['order_profit_per_order'] < 0 ,
 'loss' , 'break_even'))

print(df['profitability_flag'].value_counts())


# #visualization of profitability flag

profit_counts = df['profitability_flag'].value_counts(normalize=True)*100
profit_counts.plot(kind='pie',
                   autopct= '%1.1f%%',  
                   color=[accent_color, danger_color, secondary_color])
plt.title('profitability flag distribution (%)')
plt.savefig('profitability_flag_distribution.png', dpi=300, bbox_inches='tight')
#plt.show()

# business KPIs
def format_func(value):
    if value >= 1e6:
        return f'{value/1e6:.1f}M $'
    elif value >= 1e3:
        return f'{value/1e3:.1f}K $'
    else:
        return f'{value:.0f} $'
    
delayed_df = df[df['delay']>0]
metrics = {}
metrics ['Total orders'] = len(df)
metrics ['Late Deliveries'] = len(delayed_df)
metrics['90% delay (days)'] = delayed_df['delay'].quantile(0.90)
metrics['On Time Deliveries %'] = (1 - float(metrics['Late Deliveries'])/ metrics['Total orders'])*100
metrics['Late Deliveries %'] = float(metrics['Late Deliveries'])/ metrics['Total orders'] * 100
metrics['Total profit']= format_func(df.loc[df['order_profit_per_order']>0 , 'order_profit_per_order'].sum())
metrics['Total loss Due To delays']= format_func(df.loc[df['delay']>0 , 'order_profit_per_order'].sum())

print( '\n ---- Business KPIs ---- \n')
for k , v  in metrics.items():
    if isinstance(v,float):
        print(f"{k}: {v:.2f}")
    else:
        print(f"{k}: {v}")




#profitibility vs delivery time analysis

profit_metrics =(
    df.groupby('delay') ['order_profit_per_order']
    .agg(
        mean_profit= 'mean',
        total_profit = 'sum',
        order_count= 'count'
    ).reset_index()
)
#delay distribution
delay_distribution = (
    df['delay'] .value_counts(normalize=True)
    .sort_index()*100
).reset_index()

delay_distribution.columns= ['delay_days', 'percentage']
print('\n profit metrics by delay days :')
display(profit_counts.round(1))

print('\n Delay distribution (%) :')
display(delay_distribution)

fig , (ax1 , ax2 )= plt.subplots(1,2,figsize=(16,6 ))

#subplot 1 : delay distribution 
sns.barplot(x='delay_days', y='percentage', data=delay_distribution,color=accent_color,ax=ax1)
ax1.set_title('Delay Distribution (%)')
ax1.set_xlabel('Delay (days)')
ax1.set_ylabel('Percenatage of orders (%)')

# percentage text on bars 
for bar in ax1.patches: 
    height = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width()/2, 
        height + 0.5,
        f'{height:.1f}%',
        ha='center',
        va='bottom',
    )


#second subplot: profit analysis by delay days
ax2.set_ylabel('Total profit', color=primary_color)
ax2.bar(profit_metrics['delay'], profit_metrics['total_profit'], color=primary_color, label= 'Total profit')
ax2.tick_params(axis='y',labelcolor=primary_color)

ax3 = ax2.twinx()

ax3.set_xlabel("Delay days")
ax3.set_ylabel("Mean profit", color=accent_color)
ax3.plot(profit_metrics['delay'], profit_metrics['mean_profit'], marker= 'o',label='mean profit',color=accent_color)
ax3.tick_params(axis='y', labelcolor=accent_color)

#format total profit axis to K $ , M $
def format_func(value, tick_number):
    if value >= 1e6:
        return f'{value/1e6:.1f}M $' 
    elif value >= 1e3:
        return f'{value/1e3:.1f}k $'
    else:
        return f'{value:.0f} $'
    
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))

ax3.set_title('Profitability Analysis by Delay Days')

lines, labels = ax3.get_legend_handles_labels()
lines2 , labels2 = ax2.get_legend_handles_labels()
ax3.legend(lines + lines2, labels + labels2 , loc='upper right')
ax3.grid(True, linestyle= ':', alpha=0.5)
plt.tight_layout()
#plt.show()


#Bottleneck detection :

def compute_delay_pct_by_category(category):
    cat_df = df.groupby(category).agg(
        total_orders = ('delay', 'count')
        , late_orders = ('is_delayed', 'sum')
    ).reset_index()
    cat_df['delay_pct']= cat_df['late_orders']/cat_df['total_orders']*100
    cat_df = cat_df.sort_values('delay_pct', ascending=False).head(10)
    return cat_df

categories = ['order_region', 'customer_segment', 'shipping_mode', 'order_status', 'type','department_name']

fig, axes = plt.subplots(2,3, figsize= (10,5), constrained_layout=True)
axes = axes.flatten()

for ax , category in zip(axes, categories):
    cat_df = compute_delay_pct_by_category(category)
    sns.barplot(
        data=cat_df,
        x='delay_pct',
        y=category,
        ax=ax,
        palette='viridis'
    )
    ax.set_title(f'delay % by {category}')
    ax.set_xlabel('')
    ax.set_ylabel(category)
    for i, row in cat_df.reset_index().iterrows():
        ax.text(row['delay_pct']- 15 , i, f"{row['delay_pct']:.1f}%", va='center', fontsize=10,color='white')

#plt.show()      


#Root cause analysis 

def top_drivers_for_the_region(region):
    df_region= df[df['order_region']== region].copy()

    drivers = ['shipping_mode', 
               'customer_segment',
               'department_name',
               'type',
               'order_status']
    
    all_factors = []
    for factor in drivers:
        temp = (
            df_region.groupby(factor)
            .agg(
                total_orders = ('delay', 'count'),
                late_orders = ('is_delayed', 'sum'),
                avg_delay = ('delay', 'mean')
            )
            .reset_index()
        )

        temp['delay_pct'] = temp['late_orders']/ temp['total_orders']*100
        temp['driver']= factor 
        temp['factor_level'] = factor + " :" + temp[factor].astype(str)



        all_factors.append(temp[['driver','factor_level', 'delay_pct','avg_delay', 'total_orders']])
    
    #combine all drivers
    final_df = pd.concat(all_factors)


        

    top_factors = final_df.sort_values('delay_pct', ascending=False).head(10)
    plt.figure()

    bars = plt.barh(top_factors['factor_level'], top_factors['delay_pct'])

    plt.xlabel('Delay Percentage (%)')
    plt.ylabel('driver_factors')
    plt.title(f'Top Delay Drivers in {region} Region')
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.gca().invert_yaxis()
    for bar in bars:
            width = bar.get_width()
            plt.text(width - 5, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', va='center', color='white', fontsize=10)
   # plt.show()


top_drivers_for_the_region('Central Africa')


#time based analysis for delay 

delay_by_month = (
    df.groupby('order_month')['is_delayed'].mean().reset_index()
)
delay_by_month['delay_pct'] =delay_by_month['is_delayed']*100


delay_by_day =(
    df.groupby('order_day')['is_delayed'].mean().reset_index()
)
delay_by_day['delay_pct'] = delay_by_day['is_delayed']*100

delay_by_hour = (
    df.groupby('order_hour')['is_delayed'].mean().reset_index()
)
delay_by_hour['delay_pct']= delay_by_hour['is_delayed']*100


print(delay_by_day)


fig, (ax1, ax2, ax3)= plt.subplots(1,3, figsize=(18,6))

#subplot 1: delay % Trend over month
ax1.plot(delay_by_month['order_month'], delay_by_month['delay_pct'], marker='o', color=primary_color)
ax1.set_xticks(range(1,13))
ax1.set_xticklabels(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], rotation=45)
ax1.set_xlabel("Month")
ax1.set_ylabel("Delay Percentage (%)")
ax1.set_title("Delay % Trend Over Month")
ax1.grid(True, linestyle=':', alpha=0.5)

#anotate top 3 highest
top3_months = delay_by_month.nlargest(3, 'delay_pct')
for _, row in top3_months.iterrows():
    ax1.annotate(f"{row['delay_pct']:.1f}%",(row['order_month'], row['delay_pct']), 
                 textcoords="offset points",xytext=(0,10), ha='center', fontsize=10 , color = danger_color)
    
#subplot 2 : delay % by day of week 
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
delay_by_day['order_day']= pd.Categorical(delay_by_day['order_day'], categories=day_order, ordered=True)
delay_by_day = delay_by_day.sort_values('order_day')

ax2.bar(delay_by_day['order_day'], delay_by_day['delay_pct'], color=primary_color)

ax2.set_xticklabels(delay_by_day['order_day'], rotation=45)
ax2.set_xlabel("Day of week")
ax2.set_ylabel("Delay percentage (%)")
ax2.set_title("Delay % by day of week")
ax2.grid(True, linestyle=':', alpha=0.5)

#annotate top 3 highest bars
top3_days = delay_by_day.nlargest(3, 'delay_pct')
for _, row in top3_days.iterrows():
    height = row['delay_pct']
    ax2.text(row['order_day'], height + 0.5, f'{height:.1f}%', ha='center', va='bottom', fontsize=10, color= danger_color)


#subplot 3 : dalay % by hour for hour 
ax3.plot(delay_by_hour['order_hour'], delay_by_hour['delay_pct'], marker= 'o', color= primary_color)
ax3.set_xlabel("Hour of day")
ax3.set_ylabel("Delay percentage (%)")
ax3.set_title("Delay % by hours")
ax3.grid(True, linestyle=':', alpha=0.5)

#Anotate top 3 highest 
top3_hours = delay_by_hour.nlargest(3, 'delay_pct')
for _, row in top3_hours.iterrows():
    ax3.annotate(f"{row['delay_pct']:.1f}%", (row['order_hour'], row['delay_pct']),textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, color=danger_color)

plt.tight_layout()
plt.show()