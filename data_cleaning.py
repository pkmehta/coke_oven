# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 21:29:07 2020

@author: 1048168
"""

# import os
import pandas as pd
import numpy as np
import sqlite3

import base64
import datetime
import io

# importing dash Modules
import dash_html_components as html

# importing for email
import smtplib
from email.message import EmailMessage

# import win10toast
#from win10toast import ToastNotifier

criticality_message =''


def clean_data(file):
    df = pd.read_excel(file,sheet_name='AMPERAGE',index_col=1,header =1)
    
    # cleaning the data
    df1 =df.iloc[:72]
    df1.drop(df1.columns[0], axis=1, inplace=True)
    df2 = df1[df1.columns[:31]]
    df3 = df2.T
    df3.index.name ='record_date'
    #changing the column names to string
    col_list = df3.columns.astype(str)
    col_list = "oven_"+col_list
    df3.columns = col_list    
    df3.dropna(axis=0,how='all',inplace=True)
#    df3['record_date'] = pd.to_datetime(df3['record_date'], format='%Y-%m-%d %H:%M:%S').dt.strftime("%d-%m-%Y")
    return df3

def clean_dataframe(df):
    # cleaning the data
    df1 =df.iloc[:72]
    df1.drop(df1.columns[0], axis=1, inplace=True)
    df2 = df1[df1.columns[:31]]
    df3 = df2.T
    df3.index.name ='record_date'
    #changing the column names to string
    col_list = df3.columns.astype(str)
    col_list = "oven_"+col_list
    df3.columns = col_list    
    df3.dropna(axis=0,how='all',inplace=True)
#    df3['record_date'] = pd.to_datetime(df3['record_date'], format='%Y-%m-%d %H:%M:%S').dt.strftime("%d-%m-%Y")
    return df3


# Finding the Battery above thresold for Consecuteive two days
def critical_ovens_check(dfc):
    df_twoday = dfc.iloc[:2].T
    df_twoday.drop(df_twoday.index[0], axis=0, inplace=True)
    df_twoday=df_twoday.astype(float)
    df_twoday['diff'] = (df_twoday[df_twoday.columns[0]] >=160) & (df_twoday[df_twoday.columns[1]] >= 160)
    critical_ovens = df_twoday[df_twoday['diff'] == True].index.tolist()
    return critical_ovens
    

# =============================================================================
# def bar_color(oven_list):
#     y=np.array(oven_list)
#     color=np.array(['rgb(255,255,255)']*y.shape[0])
#     color[y<160]='rgb(204,204,205)'
#     color[y>=160]='rgb(130,0,0)'
#     return color
# =============================================================================

def bar_color(df):
    global criticality_message
    df.drop(df.index[0], axis=0, inplace=True)
    #df=df.astype(float)
    df['day1']  = (df[df.columns[0]] >= 160).astype(float)
    df['day2']  = ((df[df.columns[0]] >=160) & (df[df.columns[1]] >= 160)).astype(float)
    df['day3']  = ((df[df.columns[0]] >=160) & (df[df.columns[1]] >= 160) & (df[df.columns[2]] >= 160)).astype(float)
    df['critical_value'] = df['day1'] + df['day2'] + df['day3']
    y=np.array(df['critical_value'])
    color=np.array(['rgb(255,255,255)']*y.shape[0])
    color[y==0]='rgb(204,204,205)'
    color[y==1]='rgb(255,204,204)'
    color[y==2]='rgb(255,77,77)'
    color[y==3]='rgb(130,0,0)'
    
    con_3day = (df[df['critical_value']==3].index).tolist()
    if len(con_3day)>0:
        criticality_message += f"Consecutive 3 Days: {con_3day}\n"
        
    con_2day = (df[df['critical_value']==2].index).tolist()
    if len(con_2day)>0:
        criticality_message += f"Consecutive 2 Days: {con_2day}\n"
        
    con_1day = (df[df['critical_value']==1].index).tolist()
    if len(con_1day)>0:
        criticality_message += f"Only Last Day: {con_1day}\n"
        
    print (criticality_message)
    
    return color
    

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'xls' in filename:
            df = clean_dataframe(pd.read_excel(io.BytesIO(decoded),sheet_name='AMPERAGE',index_col=1,header =1))
            #df['record_date'] = pd.to_datetime(df['record_date'], format='%Y-%m-%d %H:%M:%S')
            df.index = pd.to_datetime(df.index)
            
        else:
            return html.Div([
                'Please Upload .XLSX, .XLS or .XLSM files only'
                ])
            
    except Exception as e:
        print(e)
        return html.Div([
            'Error while processing the file'
        ])
    
    #Making a connection with our SQLite DB
    conn = sqlite3.connect('coke_oven.db')
    df_new =pd.DataFrame()
    x_timestamp = pd.read_sql_query('select record_date from bat6_amperage order by record_date desc limit 1;', conn)
    x_timestamp= pd.to_datetime(x_timestamp['record_date'][0], format='%Y-%m-%d %H:%M:%S')
    df_new = df[df.index > x_timestamp]
    
    if df_new.empty:
        return html.Div([
            'No new records'])
    else:
        df_new.to_sql(name='bat6_amperage', con=conn, if_exists = 'append')
    conn.close()
    return html.Div([
            'New records Added'])


def status_email():
    global criticality_message
    if len(criticality_message)>1:
        content = f"Hi Team,\n\n{criticality_message}\n\nRegards,\nTeam Coke Oven"
        content = content.replace('[','').replace(']','').replace("'",'')
        
        msg = EmailMessage()
        msg['Subject'] = "Critical Ovens Report"
        msg['From'] = 'prashant.mehta@jsw.in'
        #msg['To']= ['prashant.mehta@jsw.in','puneet.narayan@jsw.in','abhi.kinlekar@jsw.in']
        msg['To']= ['prashant.mehta@jsw.in','puneet.narayan@jsw.in']
        msg.set_content(content)
        
    # =============================================================================
    #     now = datetime.now()
    #     date_time = now.strftime("%m%d%Y%H%M%S")
    # =============================================================================
        
    # =============================================================================
    #     with open(f"{attachment_filename}.xlsx",'rb') as f:
    #         file_data =f.read()
    #         file_name = f.name
    #     
    #     msg.add_attachment(file_data,maintype = 'application', subtype='octet-stream',filename=file_name)
    # =============================================================================
        
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("username", "password")
        
        s.send_message(msg)
        s.quit()    
    return

'''

#Commented due to library not getting installed in Linux

def win_notification():
        
    # create an object to ToastNotifier class
    n = ToastNotifier()   
    n.show_toast("From Coke Oven Program", "No data is DB", duration = 10)    
    return

'''
