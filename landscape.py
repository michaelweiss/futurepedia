import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math
import textwrap

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import PCA

from scipy.spatial.distance import pdist, squareform

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
import streamlit.components.v1 as components
from pyvis.network import Network

@st.cache_data()
def load_corpus(file_name):
    # Load the corpus
    corpus = pd.read_csv(file_name)
    return corpus

st.title('Futurepedia')
st.write("""
Load a file with the tool descriptions for the desired category.
""")

selected_attribute = st.sidebar.selectbox(
    'Select an attribute',
    ('Description', 'Features', 'Use Cases')
)

file_name = st.sidebar.file_uploader("Upload CSV", type="csv")
if file_name is not None:
    corpus = load_corpus(file_name)
    corpus['name'] = corpus['Tool']
    corpus['content'] = corpus[selected_attribute]
    # Drop rows with missing content
    corpus = corpus.dropna(subset=['content'])
    st.write(f"Data loaded successfully.")

    if st.sidebar.checkbox('Show data'):
        st.subheader('Data')
        st.write("""
            This is a database of AI tools for HR from Futurepedia.
            Here, we will focus on the tool descriptions and use them as the basis
            for clustering the companies.
            """)
        st.dataframe(corpus)

    # Tokenize the corpus and create a document-term matrix
    # Remove common English stop words and words that appear only once (that will also exclude company names)
    vectorizer = CountVectorizer(stop_words='english', min_df=2)
    X = vectorizer.fit_transform(corpus['content'])
    # Compute the IDF values (what words are most unique to each document)
    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(X)

    # Create a dataframe with the words as columns and the documents as rows
    # DONE: replace get_feature_names with get_feature_names_out
    vocab = vectorizer.get_feature_names_out()
    dtm = pd.DataFrame(tfidf.toarray(), columns=vocab)
    if st.sidebar.checkbox('Show document-term matrix'):
        st.subheader('Document-term matrix')
        st.write('The rows are documents and the columns are terms.')
        st.dataframe(dtm)

    # Compute pairwise cosine similarity between documents from the document-term matrix
    d_sim = pdist(tfidf.toarray(), metric='cosine')
    d_sim = pd.DataFrame(1 - squareform(d_sim), columns=corpus['name'], index=corpus['name'])
    if st.sidebar.checkbox('Show pairwise cosine similarity (documents)'):
        st.subheader('Pairwise cosine similarity (documents)')
        st.write('The rows and columns are documents. The values are the cosine similarity between documents.')
        st.dataframe(d_sim)

    def create_network(sim, labels, link_filter=0.15, degree_filter=1):
        # Create an undirected network graph
        G = nx.Graph()

        # Include all row indices as nodes
        G.add_nodes_from(labels)

        # Remove negligible edges based on a filter
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                if sim.iloc[i, j] >= link_filter:                    
                    # G.add_edge(labels[i], labels[j], value=sim.iloc[i, j], smooth=True)
                    G.add_edge(labels[i], labels[j], smooth=True)

        if len(G.edges) == 0:
            return G

        # Remove nodes based on degree
        degrees = dict(G.degree)
        for node, degree in degrees.items():
            if degree < degree_filter:
                G.remove_node(node)

        # Remove isolates (nodes without any neighbors)
        isolates = set(nx.isolates(G))
        G.remove_nodes_from(isolates)

        # Detect communities
        c_best = greedy_modularity_communities(G)
        k = 0
        for cluster in c_best:
            for i in cluster:
                G.nodes[i]["group"] = k
            k = k + 1

        # Use the content as the title of each node
        for node in G.nodes():
            G.nodes[node]["title"] = multi_line_text(
                corpus[corpus['name'] == node]['content'].values[0], 
                max_width=40, max_lines=10, is_html=True)

        return G
    
    def multi_line_text(txt, max_width=12, max_lines=2, is_html=False):
        """
        Create a multi-line text
        
        Parameters:
        txt - the text to wrap
        max_width - the maximum width of a line
        max_lines - the maximum number of lines
        """
        lines = textwrap.wrap(txt, width=max_width, break_long_words=False, max_lines=max_lines)
        if is_html:
            return '<br>'.join(lines)
        return '\n'.join(lines)

    # Create a network graph from the pairwise cosine similarity
    min_sim = st.sidebar.slider("Minimum similarity", 0.0, 1.0, 0.30, 0.05)
    min_deg = st.sidebar.slider("Minimum degree", 0, 20, 1, 1)
    if st.sidebar.checkbox('Show network graph (documents)'):
        st.subheader('Network graph')
        network = Network('1600px', '1600px')
        G = create_network(d_sim, list(corpus['name']), link_filter = min_sim, degree_filter = min_deg)
        if (len(G.nodes) == 0):
            st.write('No network to show.')
        else:
            network.from_nx(G)
            network.show("network.html")
            with st.container():
                components.html(open("network.html", 'r', encoding='utf-8').read(), height=1625, width=1625)
            # Save network graph to file for use in Gephi
            nx.write_gexf(G, "network.gexf")

            # Show table of communitie
            st.subheader('Communities')
            st.write('The table below shows the companies in each community.')
            groups = {}
            for node in G.nodes:
                group = G.nodes[node]['group']
                if group not in groups:
                    groups[group] = []
                groups[group].append(node)
            # Create dataframe with communities as rows and companies as columns
            communities = pd.DataFrame(columns=['companies'])
            for group in groups:
                communities.loc[group, 'companies'] = ', '.join(groups[group])
            communities.sort_index(inplace=True);
            st.dataframe(communities)

    # Compute pairwise cosine similarity between words from the document-term matrix
    w_sim = pdist(tfidf.T.toarray(), metric='cosine')
    w_sim = pd.DataFrame(1- squareform(w_sim), columns=vocab, index=vocab)
    if st.sidebar.checkbox('Show pairwise cosine similarity (words)'):
        st.subheader('Pairwise cosine similarity (words)')
        st.write('The rows and columns are words. The values are the cosine similarity between words.')
        st.dataframe(w_sim)

    if st.sidebar.checkbox('Show network graph (words)'):
        st.subheader('Network graph (words)')
        # Change the size of the network graph to make more space for the graph
        network = Network('1200px', '1200px')
        G = create_network(w_sim, list(vocab), link_filter = min_sim, degree_filter = min_deg)
        network.from_nx(G)
        network.show("word_network.html")
        with st.container():
            components.html(open("word_network.html", 'r', encoding='utf-8').read(), height=1225, width=1225)
        # Save network graph to file for use in Gephi
        nx.write_gexf(G, "word_network.gexf")

    if st.sidebar.checkbox('Show documents for each cluster'):
        st.subheader('Documents for each cluster')
        if not 'groups' in globals():
            st.write('Need to generate network first.')
        else:
            st.write('The table below shows the documents in each cluster.')
            # Create dataframe with clusters as rows and documents as columns
            clusters = pd.DataFrame(columns=['documents'])
            for group in groups:
                # For all documents in the cluster, get the content of the document
                # and join them together with a newline character
                cluster_content = []
                for name in groups[group]:
                    # Select the rows from the corpus where the 'name' column matches name
                    document = corpus['name'] == name
                    # Get the content of the document
                    cluster_content.append(corpus[document]['content'].values[0])
                clusters.loc[group, 'documents'] = '\n'.join(cluster_content)
            clusters.sort_index(inplace=True);
            st.dataframe(clusters)

            # Download the table as a CSV file using a download button
            csv = clusters.to_csv(index=False)
            st.download_button("Download clusters", data=csv, file_name='clusters.csv', mime='text/csv')
