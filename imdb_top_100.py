import os
import pandas as pd
import numpy as np
import requests
import seaborn as sns

#################
# Pandas section
#################

# Read in data from repo
imdb_df = pd.read_csv('https://raw.githubusercontent.com/whsky/imdb_100/master/data/imdb_100.csv')

# get the shape of the DF - (rows, columns)
dims = imdb_df.shape
print('Rows: {}'.format(dims[0]))
print('Columns: {}'.format(dims[1]))
# get the column names
print(imdb_df.columns)
# get the distinct genre types
print(imdb_df.genre.unique())
# clean up genres -- some have trailing whitespace (e.g. 'Drama            ')
imdb_df['genre'] = [x.strip() for x in imdb_df['genre']]
print(imdb_df.genre.unique())

# how many are there
print('Number of genres: {}'.format(len(imdb_df.genre.unique())))

# use 'groupby()' and 'count()' to get counts of titles by genre
print(imdb_df[['title', 'genre']].groupby('genre').count())

##############
# API section
##############

def format_title(title):
    t = title.lower()
    t = t.split(' ')
    return '+'.join(t)

def get_url(title):
    key = os.environ['OMDB_KEY']
    title = format_title(title)
    api_url = 'http://www.omdbapi.com/?apikey={key}&t={t}'.format(
                key=key,
                t=title)
    return api_url

def make_request(url):
    req = requests.get(url, timeout=5)
    data = req.json()
    return data

def get_rt_score(json):
    # check that the API returned valid response
    if json['Response'] == 'True':
        # pull out list of ratings from JSON
        rating_list = json['Ratings']
        # check that RT is in the Ratings section:
        sources = [r['Source'] for r in rating_list]
        if 'Rotten Tomatoes' in sources:
            # loop through ratings to find RT
            for rating in rating_list:
                if rating['Source'] == 'Rotten Tomatoes':
                    rt = rating['Value']
                else:
                    continue
        # otherwise if RT not in ratings, then set to NULL
        else:
            rt = np.nan
    # if the API did not find a match, set rating to NULL
    else:
        rt = np.nan

    return rt

def rt_to_dec(rt_score):
    if type(rt_score) in (str, unicode):
        # strip the percent sign from the string
        rt = rt_score.replace('%', '')
        # convert to decimal
        rt = int(rt)/100.
    else:
        rt = rt_score
    return rt

def imdb_to_dec(imdb_rating):
    return imdb_rating/10.

def five_num_summ(series):
    min = series.min()
    q1, q2, q3 = np.nanpercentile(series, [25, 50, 75])
    max = series.max()
    return min, q1, q2, q3, max



if __name__ == '__main__':
    rt_score = []
    for index, row in imdb_df.iterrows():
        url = get_url(row['title'])
        data = make_request(url)
        rt = get_rt_score(data)
        rt = rt_to_dec(rt)
        rt_score.append(rt)

    imdb_df['rt_score'] = rt_score

    # sort the DF by RT scores
    imdb_df.sort_values(by='rt_score', ascending=False, inplace=True)
    # Top 5 by RT score
    print(imdb_df.head(5)['title'])

    # Top 5 R rated movies
    print(imdb_df[imdb_df['content_rating']=='R'].head(5)['title'])
    # looks like some movies are mis-rated (e.g. Toy Story is not likely R rated)

    # Average RT score
    avg_rt = imdb_df['rt_score'].mean()
    print('Avg. Rotten Tomatoes Score: {}'.format(avg_rt))

    # 5 number summary (min, 1st q, 2nd q, 3rd q, max)
    min, q1, q2, q3, max = five_num_summ(imdb_df['rt_score'])
    print('''min: {min}\n
        1st Qrt: {q1}\n
        2nd Qrt: {q2}\n
        3rd Qrt: {q3}\n
        max: {max}'''.format(
        min=min, q1=q1, q2=q2, q3=q3, max=max)
    )

    star_dec = [imdb_to_dec(x) for x in imdb_df['star_rating']]
    imdb_df['star_decimal'] = star_dec

    ratio = imdb_df['star_decimal'] / imdb_df['rt_score']
    imdb_df['ratio'] = ratio

    max_ratio = imdb_df['ratio'].max()
    max_title = imdb_df[imdb_df['ratio'] == max_ratio]['title'].values[0]
    print('Highest IMDB / RT ratio: {0} ({1})'.format(max_title, max_ratio))

    min_ratio = imdb_df['ratio'].min()
    min_title = imdb_df[imdb_df['ratio'] == min_ratio]['title'].values[0]
    print('Lowest IMDB / RT ratio: {0} ({1})'.format(min_title, min_ratio))

    # regression plots
    #    RT score vs IMDB decimal rating
    x = imdb_df['rt_score']
    y = imdb_df['star_decimal']
    sns.regplot(x=x, y=y)
    plt.xlabel('Rotten Tomatoes Score')
    plt.ylabel('IMDB Rating')
    plt.show()

    #   movie duration vs IMDB decimal rating
    x = imdb_df['duration']
    sns.regplot(x=x, y=y)
    plt.xlabel('Movie Duration (mins)')
    plt.ylabel('IMDB Rating')
    plt.show()

    # bar graph of title counts by genre
    imdb_df[['title', 'genre']].groupby('genre').count().plot(
        kind='bar',
        title='Title Count by Genre',
        legend=Flase
        )
    plt.xlabel('Genre')
    plt.ylabel('Title Count')
    plt.show()

    # Distribution plot
    imdb_df['rt_score'].plot(
        kind='hist',
        title='Histogram of Rotten Tomatoes Scores'
        )
    plt.xlabel('Rotten Tomatoes Score')
    plt.show()
