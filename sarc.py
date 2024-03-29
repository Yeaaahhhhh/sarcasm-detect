import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
import seaborn as sns
from matplotlib import pyplot as plt
import warnings

warnings.filterwarnings('ignore')
train_df = pd.read_csv('train-balanced-sarcasm.csv')
train_df.head()
train_df.info()
train_df.dropna(subset=['comment'], inplace=True)
train_texts, valid_texts, y_train, y_valid = \
  train_test_split(train_df['comment'], train_df['label'], random_state=17)
train_df.loc[train_df['label'] == 1, 'comment'].str.len().apply(
  np.log1p).hist(label='sarcastic', alpha=.5)
train_df.loc[train_df['label'] == 0, 'comment'].str.len().apply(
  np.log1p).hist(label='normal', alpha=.5)
plt.legend()


from wordcloud import WordCloud, STOPWORDS
wordcloud = WordCloud(background_color='black', stopwords=STOPWORDS,
                    max_words=200, max_font_size=100,
                    random_state=17, width=800, height=400)
plt.figure(figsize=(16, 12))
wordcloud.generate(str(train_df.loc[train_df['label'] == 1, 'comment']))
plt.imshow(wordcloud)
plt.figure(figsize=(16, 12))
wordcloud.generate(str(train_df.loc[train_df['label'] == 0, 'comment']))
plt.imshow(wordcloud)

sub_df = train_df.groupby('subreddit')['label'].agg([np.size, np.mean, np.sum])
sub_df.sort_values(by='sum', ascending=False).head(10)
sub_df[sub_df['size'] > 1000].sort_values(by='mean', ascending=False).head(10)
sub_df = train_df.groupby('author')['label'].agg([np.size, np.mean, np.sum])
sub_df[sub_df['size'] > 300].sort_values(by='mean', ascending=False).head(10)

tf_idf = TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2)
logit = LogisticRegression(C=1, n_jobs=4, solver='lbfgs',
                         random_state=17, verbose=1)
tfidf_logit_pipeline = Pipeline([('tf_idf', tf_idf),
                               ('logit', logit)])
tfidf_logit_pipeline.fit(train_texts, y_train)
valid_pred = tfidf_logit_pipeline.predict(valid_texts)
accuracy_score(y_valid, valid_pred)
def plot_confusion_matrix(actual, predicted, classes,
                        normalize=False,
                        title='Confusion matrix', figsize=(7, 7),
                        cmap=plt.cm.Blues, path_to_save_fig=None):
  """
  This function prints and plots the confusion matrix.
  Normalization can be applied by setting `normalize=True`.
  """
  import itertools
  from sklearn.metrics import confusion_matrix
  cm = confusion_matrix(actual, predicted).T
  if normalize:
      cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

  plt.figure(figsize=figsize)
  plt.imshow(cm, interpolation='nearest', cmap=cmap)
  plt.title(title)
  plt.colorbar()
  tick_marks = np.arange(len(classes))
  plt.xticks(tick_marks, classes, rotation=90)
  plt.yticks(tick_marks, classes)

  fmt = '.2f' if normalize else 'd'
  thresh = cm.max() / 2.
  for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
      plt.text(j, i, format(cm[i, j], fmt),
               horizontalalignment="center",
               color="white" if cm[i, j] > thresh else "black")

  plt.tight_layout()
  plt.ylabel('Predicted label')
  plt.xlabel('True label')

  if path_to_save_fig:
      plt.savefig(path_to_save_fig, dpi=300, bbox_inches='tight')
plot_confusion_matrix(y_valid, valid_pred,
                    tfidf_logit_pipeline.named_steps['logit'].classes_, figsize=(8, 8))


import eli5
eli5.show_weights(estimator=tfidf_logit_pipeline.named_steps['logit'],
                vec=tfidf_logit_pipeline.named_steps['tf_idf'])

subreddits = train_df['subreddit']
train_subreddits, valid_subreddits = train_test_split(
  subreddits, random_state=17)

tf_idf_texts = TfidfVectorizer(
  ngram_range=(1, 2), max_features=50000, min_df=2)
tf_idf_subreddits = TfidfVectorizer(ngram_range=(1, 1))

X_train_texts = tf_idf_texts.fit_transform(train_texts)
X_valid_texts = tf_idf_texts.transform(valid_texts)
X_train_texts.shape, X_valid_texts.shape
X_train_subreddits = tf_idf_subreddits.fit_transform(train_subreddits)
X_valid_subreddits = tf_idf_subreddits.transform(valid_subreddits)
X_train_subreddits.shape, X_valid_subreddits.shape

from scipy.sparse import hstack
X_train = hstack([X_train_texts, X_train_subreddits])
X_valid = hstack([X_valid_texts, X_valid_subreddits])
X_train.shape, X_valid.shape
logit.fit(X_train, y_train)
valid_pred = logit.predict(X_valid)
accuracy_score(y_valid, valid_pred)