from flask import  Flask,render_template, request, Blueprint, redirect, url_for, Response, send_file
# from application import app, mongo
from flask import render_template, request, jsonify, redirect, url_for, send_file
# from flask_pymongo import PyMongo
from functools import wraps
import pymongo

import numpy as np
import math
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('agg')

from io import BytesIO, StringIO
import base64
import ast
from bson.objectid import ObjectId

from bokeh.io import output_file, show
from bokeh.models import BoxZoomTool, Circle, HoverTool, TapTool, BoxSelectTool, MultiLine, Plot, LabelSet, ResetTool, NodesAndLinkedEdges, EdgesAndLinkedNodes, ColumnDataSource
from bokeh.palettes import Spectral4
from bokeh.plotting import from_networkx, figure
from bokeh.embed import components
from bokeh.resources import CDN, INLINE

import time
import application.utils as utils


app = Flask(__name__)

mongolab_uri = 'mongodb://SciSci_user:MPrEHActItDo@gaanam4.mse.gatech.edu:8161/SciSci?authSource=SciSci'
connection = pymongo.MongoClient(host=mongolab_uri)        
db = connection['SciSci']
collection = db.authors

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'coauth_network' and password == 'lENVaNtUeste'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/process_search')
def gen_search_json():
    query = request.args.get("q", '')
    query = utils.process_term(query)
    results = utils.get_results(query.strip())
    print(results)
    resp = jsonify(results=results[:10])  # top 10 results
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/", methods = ['GET'])
def index():
    return render_template('index2.html')

@app.route("/", methods= ['POST'])
def main():
    query = str.title(request.form.get('input'))
    nodes, edges = graph_elements(query)
    G = graph(nodes, edges)
    script, div = components(interactive_plot(G,query))
    # pipeline = [ {"$unwind": "$name" },{ "$group": { '_id': "$name" } }]
    # list1 = collection.aggregate( pipeline )
    # authors = [list(i.values())[0] for i in list(list1)]
    return render_template("index2.html",  script=script, div=div, bokeh_cdn=CDN.render())
    # return render_template('index2.html', script=script, div=div, bokeh_cdn=CDN.render())
 

# @app.route('/graph/<nodes>/<edges>')
def graph(nodes, edges):
    # nodes = ast.literal_eval(nodes)
    # edges = ast.literal_eval(edges)

    G = nx.Graph()
    G.add_nodes_from(list(nodes.keys()))
    nx.set_node_attributes(G,  nodes)
    G.add_edges_from(edges)
    
    multi_orcid = [list(collection.find({'$and': [{'_id': ObjectId(ID)},{'multi_orcidID': { '$exists': True}}]}, {'_id':0, 'multi_orcidID':1})) for ID in list(nx.get_node_attributes(G, 'obj_id').values())]
    color = [Spectral4[0] if len(i)==0 else 'Red' for i in multi_orcid]
    # color[0] = 'Yellow' #changing the color for query node
    colors = dict(zip(G.nodes, color))
    nx.set_node_attributes(G, {k:v for k,v in colors.items()},'colors' )

    border= ['Black']*len(color)
    if color[0]=='Red':
        border[0]='Red'
    else:
        border[0]='Black'
    border_colors = dict(zip(G.nodes, border))
    nx.set_node_attributes(G, {k:v for k,v in border_colors.items()},'border' )

    border_width = [3 if i==0 else 1 for i in range(len(border))]
    border_width = dict(zip(G.nodes, border_width))
    nx.set_node_attributes(G, {k:v for k,v in border_width.items()},'border_width' )

    cits = nx.get_node_attributes(G,'citations')
    # max_cit = max(cits.values())
    p = np.percentile(list(cits.values()), 90)
    node_size = {}
    for i,j in cits.items():
        if (j/p <= 1):
            node_size.update({i : j*30/p})
        else:
            node_size.update({i : j*15/p})
    for i,j in node_size.items():
        if j < 10:
            node_size[i] = 10
        
    # for k,v in node_size.items():
    #     if v<10:
    #         node_size[k]= 10

    # cits = nx.get_node_attributes(G,'citations')
    # max_cit = max(cits.values())
    # min_cit = min(cits.values())
    # def rescale(x,a,b,c,d):
    #     return c + (x-a)/(b-a)*(d-c)
    # node_size = {}
    # for i,j in cits.items():
    #     # node_size.update({i : rescale(j,min_cit,max_cit,20,40)})
    #     if j!=1:
    #         node_size.update({i : np.log(j)*3})
    #     else:
    #         node_size.update({i : 3})
    nx.set_node_attributes(G, node_size, 'node_size')   

    # nx.draw(G)
    # img = BytesIO() # file-like object for the image
    # matplotlib.pyplot.savefig(img ) # save the image to the stream
    # img.seek(0) # writing moved the cursor to the end of the file, reset
    # matplotlib.pyplot.clf() # clear pyplot
    # network = base64.b64encode(img.getvalue()).decode('utf8')
    # # return network
    return G



def interactive_plot(G,query):

    plot = figure(plot_width=1000, plot_height=600)

    plot.title.text = "Co-authorship network for " + query
    
    plot.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    plot.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    plot.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    plot.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    plot.xaxis.major_label_text_color = None   
    plot.yaxis.major_label_text_color = None
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = None
    plot.axis.visible = False

    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
    
    hover = HoverTool( tooltips= [("Name: ", "@name")])
    plot.add_tools( hover, TapTool(), BoxSelectTool())

    graph_renderer.node_renderer.data_source.data['name'] = list(G.nodes())
    graph_renderer.node_renderer.glyph = Circle(size= 'node_size', fill_color= 'colors', line_color= 'border', line_width = 'border_width')
    graph_renderer.node_renderer.selection_glyph = Circle(size='node_size', fill_color=Spectral4[2])
    graph_renderer.node_renderer.hover_glyph = Circle(size='node_size', fill_color= Spectral4[1])

    # graph_renderer.edge_renderer.data_source.data["cofreq"] = [G.get_edge_data(a,b)['cofreq'] for a, b in G.edges()]
    graph_renderer.edge_renderer.data_source.data['name_edge'] = list(G.edges())
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width={'field':'cofreq'})
    graph_renderer.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width={'field':'cofreq'})
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width={'field':'cofreq'})

    graph_renderer.selection_policy = NodesAndLinkedEdges()
    graph_renderer.inspection_policy = NodesAndLinkedEdges()
    
    plot.renderers.append(graph_renderer)

    #adding names for nodes with citations in the 90th percentile or more
    node_names = list(G.nodes())
    val = list(nx.get_node_attributes(G, 'node_size').values())
    label_names = [k for k,v in nx.get_node_attributes(G,'node_size').items() if v >= math.floor(np.percentile(val, 90))]
    label_index = [node_names.index(name) for name in label_names]

    pos = graph_renderer.layout_provider.graph_layout
    x,y=zip(*pos.values())
    x_reqd = tuple((x[index] for index in label_index ))
    y_reqd = tuple((y[index] for index in label_index ))
    source = ColumnDataSource({'x': x_reqd, 'y': y_reqd,
                           'name': [label_names[i] for i in range(len(x_reqd))]})
    labels = LabelSet(x='x', y='y', text='name', source=source, x_offset= -5, y_offset = -5, background_fill_color='white')
    plot.renderers.append(labels)

    # show(plot)
    return plot


def graph_elements(query):
    
    col = collection.find({'name': query}, {'_id':0, 'co-authors':1})
    coauth1 = list(col)[0]['co-authors']
    if len(coauth1) >= 50:
        coauth1 = list(sorted(coauth1, key=lambda k: k['cofreq'], reverse=True))[:40]

    #adding citations for first level coauth
    cits_deg1 = [list(collection.find({'_id': item['obj_id']},{'_id':0, 'citations':1}))[0] for item in coauth1]
    for i in range(len(coauth1)):
        coauth1[i].update(cits_deg1[i])
    
    #finding co-authors of co-authors
    list1 = [list(collection.find({'_id': item['obj_id']},{'_id':0})) for item in coauth1]
    list2_ = [i[0]['co-authors'] for i in list1]
    list2 = [[i for i in item if not (i['name'] == 'query') ] for item in list2_]  #removing the given query as co-author

    #adding citations for second level coauth
    cits = [[list(collection.find({'_id': item['obj_id']},{'_id':0, 'citations':1}))[0] for item in sublist] for sublist in list2]
    for i in range(len(list2)):
        for j in range(len(list2[i])):
            list2[i][j].update(cits[i][j])

    coauth2 = [sorted(i, key=lambda k: (k['cofreq'], k['citations']), reverse = True)[:5] for i in list2]  #choosing top 5 co-authors

    nodes = Nodes(query, coauth1, coauth2)
    edges = Edges(query, coauth1, coauth2)
    
    return nodes, edges



def Nodes(query, coauth1, coauth2):

    query_info = list(collection.find({'name': query},{'_id':1, 'citations':1}))[0]
    nodes_info = {query: {'citations': query_info['citations'] , 'obj_id': str(query_info['_id'])}}

    for item in coauth1:
        nodes_info.update({item['name']: {'citations': item['citations'], 'obj_id': str(item['obj_id'])}})
    for sublist in coauth2:
        for val in sublist:
            nodes_info.update({val['name']:{'citations':val['citations'], 'obj_id': str(val['obj_id'])}})

    return nodes_info
    


def Edges(query, coauth1, coauth2):

    edges= []
    deg1_name= [item['name'] for item in coauth1]
    deg1_cofreq = [{'cofreq':item['cofreq']} for item in coauth1]
    edges_deg1 = list(zip([query] * len(deg1_name), deg1_name))
    for n in range(len(edges_deg1)):
        i,j = edges_deg1[n]
        edges.append((i,j,deg1_cofreq[n]))

    deg2_cofreq = [{'cofreq':val['cofreq']} for sublist in coauth2 for val in sublist]
    temp1 = [[i['name'] for i in item] for item in coauth2]
    temp2 = list(zip(deg1_name, temp1))
    edges_deg2 = [(i,val) for i,item in temp2 for val in item]  
    for n in range(len(edges_deg2)):
        i,j = edges_deg2[n]
        edges.append((i,j,deg2_cofreq[n]))
    return edges


if __name__ == "__main__":
    app.run(debug= True)