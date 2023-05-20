#! python 3
import pandas as pd

# adjust what is display from the CSV file.

desired_width=320
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Read the file from file path, used full filepath, first column is index column

matches = pd.read_csv('C:\\Users\\makor\\mypythonscripts\\predict_football_matches\\myMatches.csv', index_col=0)

# Checks the first 5 lines in the CSV file.

matches.head()

matches.shape

# Counts how many matches for each team.

matches['team'].value_counts()

# Matches just from Liverpool

matches[matches['team'] == 'Liverpool']

# Counts the number of matches per week

matches['round'].value_counts()

# Checks the data times in file.

matches.dtypes

# Changes date object in match file to pandas datetime

matches['date'] = pd.to_datetime(matches['date'])

matches.dtypes

# Converts string into categories and then converts categories into numbers.
# 0 for when team is away from home and 1 for when team is at home.

matches['venue_code'] = matches['venue'].astype('category').cat.codes

# Converts string into categories and then converts categories into numbers.
# Create a unique code for each team.

matches['opp_code'] = matches['opponent'].astype('category').cat.codes

# Replaces the colon inbetween the hour and minutes in the time column with 'blank' using regex.
# Convert the hour into an integer.
# Can only use integers and floats for machine learning.

matches['hour'] = matches['time'].str.replace(':.+', '', regex=True).astype('int')

# A code for each day of the week.
# Gets the day and week property from the column

matches['day_code'] = matches['date'].dt.dayofweek

# New column for if the team won. Return boolean True or False . 1 for a win, 0 for draw or loss.

matches['target'] = (matches['result'] == 'W').astype('int')

from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

# Training data, all matches before 2022, cannot use date from the future only the past.

train = matches[matches['date'] < '2022-01-01']

# Test data all matches after 2022.

test = matches[matches['date'] > '2022-01-01']

predictors = ['venue_code', 'opp_code', 'hour', 'day_code']

# Train random forest model with predictors

rf.fit(train[predictors], train['target'])

RandomForestClassifier(min_samples_split=10, n_estimators=50, random_state=1)

preds = rf.predict(test[predictors])

from sklearn.metrics import accuracy_score

acc = accuracy_score(test['target'], preds)

acc

# combine actual value and prediction value

combined = pd.DataFrame(dict(actual=test['target'], prediction=preds))

# Two way table which shows if a 1 or 0 was predicted.

pd.crosstab(index=combined['actual'], columns=combined['prediction'])

from sklearn.metrics import precision_score

precision_score(test['target'], preds)

# matches grouped by team.

grouped_matches = matches.groupby('team')

group = grouped_matches.get_group('Manchester City')

group

def rolling_averages(group, cols, new_cols):
    # Takes a group, columns and creates new column to be assigned rolling averages.

    # Sorted by last 3 matches that team played.

    group = group.sort_values('date')

    # Compute rolling averages for a column. 'closed='left'' ignores the current week.

    rolling_stats = group[cols].rolling(3, closed='left').mean()

     # Return group with new columns

    group[new_cols] = rolling_stats

    # Ignore the missing values.
    group = group.dropna(subset=new_cols)

    return group

# New columns.

cols = ['gf', 'ga', 'sh', 'sot', 'dist', 'fk', 'pk', 'pkatt']

# For loop to create new columns.

new_cols = [f'{c}_rolling' for c in cols]

new_cols

rolling_averages(group, cols, new_cols)

matches_rolling = matches.groupby('team').apply(lambda x: rolling_averages(x, cols, new_cols))

matches_rolling = matches_rolling.droplevel('team')

matches_rolling.index = range(matches_rolling.shape[0])

def make_predictions(data, predictors):
    train = data[data['date'] < '2022-01-01']
    test = data[data['date'] > '2022-01-01']
    rf.fit(train[predictors], train['target'])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test['target'], predicted=preds), index=test.index)
    precision = precision_score(test['target'], preds)
    return combined, precision

matches_rolling

combined, precision = make_predictions(matches_rolling, predictors + new_cols)

precision

combined = combined.merge(matches_rolling[['date', 'team', 'opponent', 'result']], left_index=True, right_index=True)

combined


class MissingDict(dict):
    __missing__ = lambda self, key: key

map_values = {
    'Brighton and Hove Albion': 'Brighton',
    'Manchester United': 'Manchester Utd',
    'Newcastle United': 'Newcastle Utd',
    'Tottenham Hotspurs': 'Tottenham',
    'West Ham United': 'West Ham',
    'Wolverhampton Wanderers': 'Wolves'
}
mapping = MissingDict(**map_values)

combined['new_team'] = combined['team'].map(mapping)

merged = combined.merge(combined, left_on=['date', 'new_team'], right_on=['date', 'opponent'])

merged[(merged['predicted_x'] == 1) & (merged['predicted_y'] == 0)]['actual_x'].value_counts()

merged

merged.to_csv('my_predicted_matches.csv')


