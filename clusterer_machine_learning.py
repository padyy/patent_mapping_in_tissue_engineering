import pymongo
import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import MiniBatchKMeans
# from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.datasets import load_files
from sklearn.metrics import silhouette_score
  
if __name__ == "__main__":
    # Connect to MongoDB
    client = pymongo.MongoClient('localhost', 27017)
    db = client.ptixiaki
    collection = db.patents_full
    
    # Request data from MongoDB
    patents = collection.aggregate([
        {'$match':{'$or':[{'title':{'$exists':True,'$ne':None}},{'abstract':{'$exists':True,'$ne':None}}]}},
        {'$project':{'_id':0,'doc-number':1,'title':1,'abstract':1,'country':1,'url':1,'year':{
                '$year':{
                    '$dateFromString': {
                        'dateString': '$date',
                        'format': '%Y%m%d'
                    }
                }
            }
        }},
        {'$sort':{'year':-1}},
        {'$project':{'_id':0,'doc-number':1,'title':1,'abstract':1,'year':1,'country':1,'url':1}}
    ])
    
    # Prepare data for formating in DataFrame format
    articles = []
    years = []
    countries = []
    docnumbers = []
    titles = []
    abstracts = []
    urls = []
    for patent in patents:
        title=patent.get('title','')
        abstract=patent.get('abstract','')
        if title is None: title=''
        if abstract is None: abstract=''
        articles.append( title  +' '+ abstract)
        years.append(patent['year'])
        countries.append(patent['country'])
        docnumbers.append(patent['doc-number'])
        titles.append(title)
        abstracts.append(abstract)
        urls.append(patent['url'])
    
    # Set random seed
    random_state = 0 
    
    # Transform data in DataFrame format
    df = pd.DataFrame(list(zip(articles, titles, abstracts, years, countries, docnumbers, urls)), columns=['text', 'title', 'abstract', 'year', 'country', 'docnumber', 'urls'])
    
    # Retrieve vectors from data
    vec = TfidfVectorizer(stop_words="english")
    vec.fit(df.text.values)
    
    # Extract Features from Vectors
    features = vec.transform(df.text.values)
    
    # Initialize clustering Algorythm
    cls = MiniBatchKMeans(n_clusters=7, random_state=random_state)
    # cls =  KMeans(n_clusters=9, random_state=random_state)
   
    # Create Clusters
    cls.fit(features)
    cls.predict(features)
    
    # Write predictions to CSV
    cluster_map = pd.DataFrame()
    cluster_map['title'] = df.title.values
    cluster_map['abstract'] = df.abstract.values
    cluster_map['cluster'] = cls.labels_
    cluster_map['year'] = df.year.values
    cluster_map['country'] = df.country.values
    cluster_map['doc-number'] = df.docnumber.values
    cluster_map['urls'] = df.urls.values
    cluster_map.to_csv('clusters.csv')
    
    
    # Evaluation using the silhouette score method
    print({'silousilhouette_score':silhouette_score(features, labels=cls.predict(features))})
    
    
    #Visualize

    pca = PCA(n_components=3, random_state=random_state)
    reduced_features = pca.fit_transform(features.toarray())
    reduced_cluster_centers = pca.transform(cls.cluster_centers_)
    fig = plt.figure(num=1, figsize=(30, 30), dpi=80)
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(reduced_features[:,0], reduced_features[:,1], reduced_features[:,2], c=cls.predict(features))
    ax.scatter(reduced_cluster_centers[:, 0], reduced_cluster_centers[:,1], reduced_cluster_centers[:,2], marker='x', s=150, c='b')
    fig.savefig('3dFigure.png')

    plt.clf()

    pca = PCA(n_components=2, random_state=random_state)
    reduced_features = pca.fit_transform(features.toarray())
    reduced_cluster_centers = pca.transform(cls.cluster_centers_)
    fig = plt.figure(num=1, figsize=(30, 30), dpi=80)
    plt.scatter(reduced_features[:,0], reduced_features[:,1], c=cls.predict(features))
    plt.scatter(reduced_cluster_centers[:, 0], reduced_cluster_centers[:,1], marker='x', s=150, c='b')
    fig.savefig('2dFigure.png')