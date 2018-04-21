import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
#from surprise import Reader, Dataset, SVD, evaluate
import warnings; warnings.simplefilter('ignore')

import sys

print("into main.py")

print(sys.argv[1])

print('type of argument ', type(sys.argv[1]))

movie_name = ""

for i in range(1, len(sys.argv)):
	movie_name += sys.argv[i]
	if i != (len(sys.argv) - 1):
		movie_name += " "
	print('movie: ', movie_name)
print('movie_name: ', movie_name)


md = pd.read_csv('./Dataset/movies_metadata.csv', low_memory=False)
links_small = pd.read_csv('./Dataset/links_small.csv')
links_small = links_small[links_small['tmdbId'].notnull()]['tmdbId'].astype('int')

md = md.drop([19730, 29503, 35587])
md['id'] = md['id'].astype('int')
smd = md[md['id'].isin(links_small)]

smd['tagline'] = smd['tagline'].fillna('')
smd['description'] = smd['overview'] + smd['tagline']
smd['description'] = smd['description'].fillna('')

tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0, stop_words='english')
tfidf_matrix = tf.fit_transform(smd['description'])

cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

smd = smd.reset_index()
titles = smd['title']
indices = pd.Series(smd.index, index=smd['title'])

def get_recommendations(title):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:31]
    movie_indices = [i[0] for i in sim_scores]
    return titles.iloc[movie_indices]


bot0= list(get_recommendations(movie_name))  #sys.argv[1]).head(10)

print(bot0)

file_name = open('movies.txt', 'w')
print('created the file movies.txt')
for i in range(len(bot0)):
	file_name.write(bot0[i])
	file_name.write(",")

file_name.close()