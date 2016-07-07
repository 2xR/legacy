try:
    import networkx
    from matplotlib import pyplot
except ImportError:
    networkx = None
    pyplot = None


def default_edge_weight(a, b):
    """Default edge weight function used in build()."""
    return 1.0


def build(root, get_children, get_edge_weight=default_edge_weight):
    """Create a networkx DiGraph object equivalent to the tree rooted at 'root'. The children
    of a node 'n' are obtained by 'get_children(n)'. Edge weights are obtained through
    'get_edge_weight(a, b)'."""
    graph = networkx.DiGraph()
    stack = [root]
    while len(stack) > 0:
        node = stack.pop()
        for child in get_children(node):
            graph.add_edge(node, child, weight=get_edge_weight(node, child))
            stack.append(child)
    return graph


def find_root(tree):
    """Given a DiGraph representing a tree, find its root node."""
    potential_roots = []
    for node, in_degree in tree.in_degree():
        if in_degree == 0:
            potential_roots.append(node)
    if len(potential_roots) != 1:
        raise ValueError("argument graph is not a tree")
    return potential_roots[0]


def height(tree, root=None):
    """Computes the height of the tree rooted at 'root'. 'tree' is a networkx DiGraph object."""
    if root is None:
        root = find_root(tree)
    children = tree[root]
    if len(children) == 0:
        return 1
    else:
        return 1 + max(height(tree, child) for child in children)


def draw(tree, root=None, get_children=None, highlight_paths=(),
         colormap="jet", axes=None, show=True):
    """Display a tree using draw_networkx_edges()."""
    if root is None:
        root = find_root(tree)
    if axes is None:
        pyplot.figure(1)
        axes = pyplot.subplot(1, 1, 1)
    # compute the colors of the edges of the tree according to the argument 'colormap'
    if colormap is not None:
        weights = [d["weight"] for _, _, d in tree.edges_iter(data=True)]
        num_weights = [w for w in weights if w is not None]
        max_weight = None
        delta_weight = 0.0
        if len(num_weights) > 0:
            max_weight = max(num_weights)
            min_weight = min(num_weights)
            delta_weight = float(max_weight - min_weight)
        if delta_weight == 0.0:
            edge_color = "black"
        else:
            black = (0.0, 0.0, 0.0, 1.0)
            cmap = pyplot.get_cmap(colormap)
            edge_color = [black if w is None else cmap((max_weight - w) / delta_weight)
                          for w in weights]
    else:
        edge_color = "black"
    # compute the layout of the nodes in the tree and draw the tree's edges
    coords = layout(tree, root, get_children)
    networkx.draw_networkx_edges(tree, coords, ax=axes, arrows=False, edge_color=edge_color)
    # add highlights to the paths in 'highlight_paths'
    for path in highlight_paths:
        XYs = [coords[v] for v in path]
        Xs = [xy[0] for xy in XYs]
        Ys = [xy[1] for xy in XYs]
        axes.plot(Xs, Ys, color="black", linewidth=5, dashes=[5, 15], marker="o",
                  markersize=5, markerfacecolor="black", markeredgewidth=0, zorder=1)
    # configure the axes to show the [0, 1] x [0, 1] region and display no ticks
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)
    axes.set_xticks([])
    axes.set_yticks([])
    if show:
        pyplot.interactive(True)
        pyplot.show()
    return axes


def layout(tree, root=None, get_children=None):
    """Create a layout (a {node: (x, y)} dictionary) of the tree rooted at 'root' in the square
    region [0, 1]x[0, 1]."""
    if root is None:
        root = find_root(tree)
    coords = {}
    h = height(tree, root)
    dy = 1.0 / (h + 1.0)
    ys = [dy * i for i in xrange(h, 0, -1)]
    _layout(tree, root, get_children, depth=0, x_min=0.0, x_max=1.0, ys=ys, coords=coords)
    return coords


def _layout(tree, root, get_children, depth, x_min, x_max, ys, coords):
    """Private function called by layout()."""
    # place the root of this subtree at the center of the argument x interval
    x = (x_min + x_max) * 0.5
    y = ys[depth]
    coords[root] = (x, y)
    # recursively lay out children (each with its own x interval)
    children = tree[root] if get_children is None else get_children(root)
    if len(children) > 0:
        depth += 1
        x_spacing = float(x_max - x_min) / len(children)
        x_max = x_min + x_spacing
        for child in children:
            _layout(tree, child, get_children, depth, x_min, x_max, ys, coords)
            x_min = x_max
            x_max += x_spacing
