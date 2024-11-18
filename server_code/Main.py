import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime
import os.path
import requests
import csv
import io
import zipfile
from urllib.request import urlretrieve
import pandas as pd
from contextlib import closing
import json
import fnmatch
from ftplib import FTP


@anvil.server.callable
def dl_to_weather_stations(url):
    response = requests.get(url)
    if response.status_code == 200:
        lines = response.text.splitlines()
        #format_string = "%Y%m%d"
        wsid = []
        date_from = []
        date_to = []
        height = []
        lat = []
        lng = []
        station = []
        region = []
        abgabe = []
        for line in lines[2:]:    
          wsid.append(line[0:5])
          date_from.append(line[6:14])
          date_to.append(line[15:23])
          height.append(line[24:38])
          lat.append(line[39:50])
          lng.append(line[51:60])
          station.append(line[61:101].strip()) #.strip())
          region.append(line[102:142].strip()) #.strip())
          abgabe.append(line[143:].strip()) #.strip())
        # dictionary of lists 
        dict = {'wsid': wsid, 'date_from': date_from, 'date_to': date_to, 'height': height, # [m]
                'lat': lat, 'lng': lng, 'name': station, 'region': region, 'abgabe': abgabe}
        df = pd.DataFrame(dict) #.drop(index=[0,1])
        # Convert columns
        df['date_from'] = pd.to_datetime(df['date_from']).dt.date
        df['date_to'] = pd.to_datetime(df['date_to']).dt.date
        df['height'] = pd.to_numeric(df['height'], downcast="integer")
        df['lat'] = pd.to_numeric(df['lat'], downcast="float")
        df['lng'] = pd.to_numeric(df['lng'], downcast="float")
        # remove stations w/ missing latest observation
        df1 = df[df['date_to']==df['date_to'].max()]
        # remove stations where abgabe is not 'Frei'
        df2 = df1[df1['abgabe']=='Frei']
    return(df2.to_dict('list'))

def dict_to_dataframe(data_dict):
    """Converts a dictionary with a binary string value into a Pandas DataFrame.
  
    Args:
      data_dict: The input dictionary.
  
    Returns:
      A Pandas DataFrame.
    """
    value = next(iter(data_dict.values()))  # Extract the value
    decoded_value = value.decode('utf-8')  # Decode the byte string
    records = decoded_value.strip().split('eor\r\n')
    data = [record.split(';') for record in records]
    # Trim column names using strip()
    df = pd.DataFrame(data[1:], columns=(s.strip() for s in data[0]))
    df = df[df.columns[:-1]]
    # Remove leading and trailing spaces from all columns
    df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)  
    return(df)  
  
@anvil.server.callable
def dl_zip(wsid, date_from, date_to, recent, historical):
    """Downloads daily weather data from opendata.dwd.de for a given weather station id and two different periods; recent and historical.

    Args:
      wsid: The weather station identifier.
      date_from: The start date of observations.
      date_to: The end date of observations.
      recent: Observations w/ not yet completed quality check.
      historical: Observations w/ completed quality check.

    Returns:
      A dictionary containing the requested data.
    """
    if not recent and not historical:
        recent = True
    protocol = 'https://'
    domain_name = 'opendata.dwd.de'
    path = '/climate_environment/CDC/observations_germany/climate/daily/kl/'
    if recent:
        recent_path = path + 'recent/'
        filename = f'tageswerte_KL_{wsid}_akt.zip'

        # Extract file from archive
        url = protocol + domain_name + recent_path + filename
        r = requests.get(url)
        body = {}
        with closing(r), zipfile.ZipFile(io.BytesIO(r.content)) as archive:   
             body ={member.filename: archive.read(member) 
                  for member in archive.infolist() 
                  if (member.filename.startswith('produkt_klima_tag_'))
                  }
        dfr = dict_to_dataframe(body)
        if not historical:
            dfh = dfr[0:0]
    if historical:
        historical_path = path + 'historical/'

        # Extract filename from remote directory using wildcards
        ftp = FTP(domain_name)
        ftp.login('anonymous', 'guest')
        ftp.cwd(historical_path)
        # List files in directory
        files = ftp.nlst()
        # Filter files based on wildcard pattern
        pattern = f'tageswerte_KL_{wsid}_{pd.to_datetime(date_from).strftime("%Y%m%d")}_*_hist.zip'
        matching_files = fnmatch.filter(files, pattern) # TODO: check if more than one match.
        ftp.quit()
    
        # Extract file from archive
        url = protocol + domain_name + historical_path + matching_files.pop()
        h = requests.get(url)
        body = {}
        with closing(h), zipfile.ZipFile(io.BytesIO(h.content)) as archive:   
            body ={member.filename: archive.read(member) 
                  for member in archive.infolist() 
                  if (member.filename.startswith('produkt_klima_tag_'))
                  }
        dfh = dict_to_dataframe(body)
        if not recent:
          dfr = dfh[0:0]
    
    # Merge downloaded data frames w/ only recent data not in historical
    #df = pd.concat([dfr, dfh])
    df = pd.concat([
        dfh,
        dfr[dfr['MESS_DATUM'].isin(dfh['MESS_DATUM']) == False]
    ])

    df = df.drop('STATIONS_ID', axis=1) # already given as parameter
    dict_list = df.to_dict('list')
    return(dict_list)

#def send_feedback(name, email, feedback):
#@anvil.server.callable
#def send_feedback(email):
#    anvil.email.send(
#      from_name='name',
#      to=email,
#      subject=f"Feedback from {email}",
#      #html='The Anvil <a href="https://anvil.works/forum">Forum</a> is friendly and informative.',
#      text={" ***"},
#    )

@anvil.server.callable
def send_feedback(address, name, email, feedback):
    anvil.email.send(
      from_name=name,
      to=address,
      subject=f"Feedback from {email}",
      html='The Anvil <a href="https://anvil.works/forum">Forum</a> is friendly and informative.',
      text=f"{feedback}"
    )
