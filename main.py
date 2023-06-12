import pandas as pd
import streamlit as st
import json
from datetime import datetime
from pandas.io.formats.style import Styler

# Assuming your dataframe is named 'df'
# Replace 'df' with the actual name of your dataframe
df = pd.read_csv(r'C:\Users\DELL\Downloads\final.csv')
df = df[0:2000]

# Function to convert JSON data into a DataFrame
def convert_json_to_dataframe(json_data, institution):
    def decode_json_string(json_str):
        json_str = json_str.replace("'", '"')
        return json.loads(json_str)

    data = decode_json_string(json_data)
    df = pd.DataFrame.from_records(data)

    # Add Institution column
    df['Institution'] = institution

    return df

# Function to classify the dataframes based on the institution
def classify_dataframes(group):
    if 'Monexo Fintech Private Limited' in group['Institution'].values:
        return 'Monexo Fintech Pvt. Ltd'
    else:
        return 'Other Institutions'

# Group the data by customer_id and classify into two dataframes
grouped_data = df.groupby('customer_id').apply(classify_dataframes).reset_index(name='Classification')

# Separate the dataframes based on the classification
monexo_data = df[df['customer_id'].isin(grouped_data[grouped_data['Classification'] == 'Monexo Fintech Pvt. Ltd']['customer_id'])]
other_institutions_data = df[df['customer_id'].isin(grouped_data[grouped_data['Classification'] == 'Other Institutions']['customer_id'])]

# Create a Streamlit app
st.title('Customer Data Dashboard')

# Display the Monexo Fintech Pvt. Ltd data
st.write('Monexo Fintech Pvt. Ltd Data:')
st.dataframe(monexo_data)
monexo_customer_count = monexo_data['customer_id'].nunique()
st.write(f"Unique Customer IDs in Monexo Fintech Pvt. Ltd Data: {monexo_customer_count}")

# Group by customer_id and iterate over the groups
for customer_id, group_df in monexo_data.groupby('customer_id'):
    st.write(f"Customer ID: {customer_id}")
    st.dataframe(group_df)
    st.write("---")
    
    # Classify into two dataframes based on AccountStatus
    closed_account_df = group_df[group_df['AccountStatus'] == 'Closed Account']
    other_status_df = group_df[group_df['AccountStatus'] != 'Closed Account']
    
    st.write("Closed Account Data:")
    st.dataframe(closed_account_df)
    
    st.write("Other Status Data:")
    st.dataframe(other_status_df)

    st.write("===")
    
    # Create a separate history_data_dataframe for each customer_id
    history_dataframes = []
    
    # Iterate over each dataframe in other_status_df
    for index, row in other_status_df.iterrows():
        history_json = row['History48Months']
        
        # Convert the JSON data to a dataframe
        history_df = convert_json_to_dataframe(history_json, row['Institution'])
        
        # Add additional columns
        history_df['customer_id'] = customer_id
        history_df['LastPaymentDate'] = row['LastPaymentDate']
        history_df['LastPayment'] = row['LastPayment']
        
        # Append the dataframe to the list
        history_dataframes.append(history_df)
    
    # Concatenate the history dataframes into a single dataframe for the current customer_id
    history_data_dataframe = pd.concat(history_dataframes)
    
    # Split the history_data_dataframe into history_monexo_dataframe and history_others_dataframe
    history_monexo_dataframe = history_data_dataframe[history_data_dataframe['Institution'] == 'Monexo Fintech Private Limited']
    history_others_dataframe = history_data_dataframe[history_data_dataframe['Institution'] != 'Monexo Fintech Private Limited']
    
    st.write(f"History Data for Customer ID: {customer_id}")
    st.write("Monexo Fintech Pvt. Ltd History Data:")
    st.dataframe(history_monexo_dataframe)
    
    st.write("Other Institutions History Data:")
    st.dataframe(history_others_dataframe)

    st.write("===")
    
    # Find the data in PaymentStatus column for each dataframe
    delinquency_monexo_dataframe = history_monexo_dataframe[history_monexo_dataframe['PaymentStatus'].isin(['60+', '30+', 'SUB', 'DBT', 'LOSS', '120+', '90+'])]
    delinquency_others_dataframe = history_others_dataframe[history_others_dataframe['PaymentStatus'].isin(['60+', '30+', 'SUB', 'DBT', 'LOSS', '120+', '90+'])]
    
    # Create a separate dataframe for delinquency records
    delinquency_records = pd.concat([delinquency_monexo_dataframe, delinquency_others_dataframe])
    
    # Add a column to monexo_data dataframe and set default value
    monexo_data.loc[monexo_data['customer_id'] == customer_id, 'Category'] = 'GMGO'
    
    # Check conditions and update Category
    if not delinquency_monexo_dataframe.empty and not delinquency_others_dataframe.empty:
        monexo_data.loc[monexo_data['customer_id'] == customer_id, 'Category'] = 'BMBO'
    elif not delinquency_monexo_dataframe.empty and delinquency_others_dataframe.empty:
        monexo_data.loc[monexo_data['customer_id'] == customer_id, 'Category'] = 'BMGO'
    elif delinquency_monexo_dataframe.empty and not delinquency_others_dataframe.empty:
        monexo_data.loc[monexo_data['customer_id'] == customer_id, 'Category'] = 'GMBO'


# use this - Create a copy of monexo_data dataframe for styling
styled_monexo_data = monexo_data.copy()

# Apply formatting to the Category column
styled_monexo_data['Category'] = styled_monexo_data['Category'].apply(lambda x: f"<b><font color='red'>{x}</font></b>" if x == 'BMBO' else x)
styled_monexo_data['Category'] = styled_monexo_data['Category'].apply(lambda x: f"<b><font color='green'>{x}</font></b>" if x == 'GMGO' else x)
styled_monexo_data['Category'] = styled_monexo_data['Category'].apply(lambda x: f"<b><font color='amber'>{x}</font></b>" if x == 'GMBO' or x == 'BMGO' else x)

# Display the updated monexo_data dataframe with formatting
st.write("Monexo Fintech Pvt. Ltd Data with Category:")
st.write(styled_monexo_data.to_html(escape=False), unsafe_allow_html=True)


# Count the number of unique customer_id in each category
category_counts = monexo_data['Category'].value_counts()

st.write(category_counts)

# Create a dataframe with unique customer_id and Category
unique_category_df = monexo_data[['customer_id', 'Category']].drop_duplicates()

# Display the dataframe
st.write("Unique Customer IDs and Categories:")
st.dataframe(unique_category_df)