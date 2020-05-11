import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error


def aggregate_df(df):
  df['cases'] = pd.to_numeric(df['cases'])
  df['deaths'] = pd.to_numeric(df['deaths'])
  aggregation_functions = {'cases':'sum', 'deaths':'sum', 'Date':'first'}
  df_new = df.groupby(df['date']).aggregate(aggregation_functions)
  df_new['new_cases'] = df_new['cases'].diff().fillna(0)
  df_new['new_deaths'] = df_new['deaths'].diff().fillna(0)
  return df_new

def get_state(df, state):
  df_new = df.loc[df['state'] == state]
  df_new['Date'] = df[['date']]

  return df_new

def get_rmse(df1, df2, var):
  df1_length = len(df1.index)
  truncated_df2 = df2.head(df1_length)
  rmse = np.sqrt(mean_squared_error(df1[[var]], truncated_df2[[var]]))
  return round(rmse,2)

def make_plot(var, df1, df2, df3, df1_name, df2_name, df3_name):
  rmse = get_rmse(df1, df2, var)
  plt.title(state)
  plt.xlabel(var)
  plt.ylabel('Date')
  plt.plot(df1['Date'], df1[var], color = 'blue', label = df1_name + ' NYT', markersize = 8, marker = '.', alpha = 0.5)
  plt.plot(df2['Date'], df2[var],  color = 'orange', label = df2_name + ' NYT: RMSE: ' + str(rmse), markersize = 8, marker = '.', alpha = 0.5)
  #plt.plot(df3['Date'], df3[var], alpha = 0.5, color = 'green', label = df3_name + ' NYT', markersize = 10, marker = '.')
  plt.xticks(rotation=30)
  plt.legend(loc = 'upper left')
  plt.grid(True)
  plt.savefig(var + 'compare.pdf', bbox_inches='tight')
  plt.close('all')


if __name__ == '__main__':
  state = 'Idaho'
  df1 = get_state(pd.read_csv("../us-counties-5-9.csv", parse_dates=['date']), state)
  df2 = get_state(pd.read_csv("../us-counties-5-11.csv", parse_dates=['date']), state)
  df3 = get_state(pd.read_csv("../us-counties-may11.csv", parse_dates=['date']), state)
  df1_name = 'May 9'
  df2_name = 'May 11'
  df3_name = 'May 11'
  #pd.set_option('display.max_rows', None)

  df1_ag = aggregate_df(df1)
  df2_ag = aggregate_df(df2)
  df3_ag = aggregate_df(df3)
  make_plot('new_cases', df1_ag, df2_ag, df3_ag, df1_name, df2_name, df3_name)
  make_plot('new_deaths', df1_ag, df2_ag, df3_ag, df1_name, df2_name, df3_name)


