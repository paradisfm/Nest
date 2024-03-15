import numpy as np
import pandas as pd
from scipy.cluster.vq import whiten
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from matplotlib import pyplot as plt

def get_rgb(image):
    im = np.array(image, dtype="object")
    r = []
    g = []
    b = []
    for row in im:
        for r2, g2, b2 in row:
            r.append(r2)
            g.append(g2)
            b.append(b2)
    df = pd.DataFrame({'red': r,
                       'green': g,
                       'blue': b})
    df['scaled_red'] = whiten(df['red'])
    df['scaled_green'] = whiten(df['green'])
    df['scaled_blue'] = whiten(df['blue'])
    return df

#def rgb2hex(r, g, b):
#    return "#{:02x}{:02x}{:02x}".format(r, g, b)
#
#def get_hex(df):
#    df['hex'] = df.apply(lambda r:rgb2hex(*r), axis=1)
#    return df

def get_color_nums(df):
     #process the rgb values using k-means clustering to get a palette of X colors
    distortions = []
    inertias = []
    m1 = {}
    m2 = {}
    k_range = range(1,10)
    X = df[['scaled_red', 'scaled_green', 'scaled_blue']]

    for k in k_range:
        model = KMeans(n_clusters=k).fit(X)
        model.fit(X)
        
        distortions.append(sum(np.min(cdist(X, model.cluster_centers_, 'euclidean'), axis=1)) / X.shape[0])
        inertias.append(model.inertia_)

        m1[k]=sum(np.min(cdist(X, model.cluster_centers_, 'euclidean'), axis=1) / X.shape[0])
        m2[k] = model.inertia_

    #analyze dx over each k and compare every dy=k-[k-1] as well as k/k-1. the threshold for desired K is where k/k-1
    distortions = pd.DataFrame({'inertia': m2, 'dist': m1 })
    distortions_list = distortions['dist'].tolist()
    deltas = []
    proportions = []

    for k in k_range:
        if k < 9:
            proportion = distortions_list[k]/distortions_list[k-1]
            proportions.append(proportion)

        elif k == 9:
            proportions.append(0)
    distortions['proportions'] = proportions

    for i in range(len(distortions_list)):
        delta = proportions[i] - proportions[i-1]
        deltas.append(delta)
        if i > 8:
            deltas.append(0)
    distortions['delta'] = deltas
    #print(distortions[:]) 
    #when it becomes an 0.0x delta, that first 0.0x is the k 
    for i in range(len(deltas)):
         ds = str(deltas[i])
         first = ds[2]
         if first == "0":
             clusters = i + 1
             break
    return clusters

def get_colors(df, k):
    colors = []
    X = df[['scaled_red', 'scaled_green', 'scaled_blue']]
    red_std, green_std, blue_std = df[['red', 'green', 'blue']].std()
    
    model = KMeans(n_clusters=k).fit(X)
    model.fit(X)
    
    centers = model.cluster_centers_
    
    for center in centers:
        red_scaled, green_scaled, blue_scaled = center
        colors.append((
            red_scaled * red_std / 255,
            green_scaled * green_std / 255,
            blue_scaled * blue_std / 255
        ))
    
    plt.imshow([colors])
    plt.show()
    return colors