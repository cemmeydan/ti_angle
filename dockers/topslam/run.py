# force matplotlib backend, to avoid tkinter problems (through GPy)
import matplotlib
matplotlib.use('PS')

# import topslam and others
import os
import sys
import json
import pandas as pd
import topslam
from topslam.optimization import run_methods, create_model, optimize_model
from topslam import ManifoldCorrectionTree

# load data
expression = pd.read_csv("/input/expression.csv", index_col=[0])
p = json.load(open("/input/params.json", "r"))
start_cells = json.load(open("/input/start_cells.json"))

# run topslam
from sklearn.manifold import TSNE, LocallyLinearEmbedding, SpectralEmbedding, Isomap
from sklearn.decomposition import FastICA, PCA

n_components = p["n_components"]

methods = {
  't-SNE':TSNE(n_components=n_components),
  'PCA':PCA(n_components=n_components),
  'Spectral': SpectralEmbedding(n_components=n_components, n_neighbors=p["n_neighbors"]),
  'Isomap': Isomap(n_components=n_components, n_neighbors=p["n_neighbors"]),
  'ICA': FastICA(n_components=n_components)
}
method_names = sorted(methods.keys())
method_names_selected = [method_names[i] for i, selected in enumerate(p["dimreds"]) if selected]
methods = {method_name:method for method_name, method in methods.iteritems() if method_name in method_names_selected}

print("Dimensionality reduction")

X_init, dims = run_methods(expression, methods)

print("Modelling")
m = create_model(expression, X_init, linear_dims=p["linear_dims"])
m.optimize(messages=1, max_iters=p["max_iters"])

print("Manifold correction")

m_topslam = ManifoldCorrectionTree(m)
start_cell_ix = expression.index.tolist().index(start_cells[0])
pt_topslam = m_topslam.get_pseudo_time(start=start_cell_ix, estimate_direction=True)

# also export landscape for plotting later

print("Calculating landscape")
landscape = topslam.landscape.waddington_landscape(m, resolution=100, xmargin=(0.5, 0.5), ymargin=(0.5, 0.5))

print("Saving")
pseudotime = pd.DataFrame({
  "cell_id": expression.index,
  "pseudotime": pt_topslam
})
pseudotime.to_csv("/output/pseudotime.csv", index=False)
pd.DataFrame(landscape[0], columns=["x", "y"]).to_csv("/output/wad_grid.csv", index=False)
pd.DataFrame(landscape[1], columns=["energy"]).to_csv("/output/wad_energy.csv", index=False)
dimred = pd.DataFrame(landscape[2], columns=["comp_" + str(i+1) for i in range(landscape[2].shape[1])])
dimred["cell_id"] = expression.index
dimred.to_csv("/output/dimred.csv", index=False)
