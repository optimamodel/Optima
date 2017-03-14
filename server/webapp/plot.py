import re

import mpld3

from matplotlib.transforms import Bbox
from numpy import array

import optima as op

from .parse import normalize_obj


def extract_graph_selector(graph_key):
    s = repr(str(graph_key))
    base = "".join(re.findall("[a-zA-Z]+", s.split(",")[0]))
    if "'t'" in s:
        suffix = "-tot"
    elif "'p'" in s:
        suffix = "-pop"
    elif "'s'" in s:
        suffix = "-sta"
    else:
        suffix = ""
    return base + suffix


def convert_to_mpld3(figure):
    plugin = mpld3.plugins.MousePosition(fontsize=8, fmt='.4r')
    mpld3.plugins.connect(figure, plugin)

    figure.set_size_inches(5.5, 2)

    # is_stack_plot = False

    if len(figure.axes) == 1:
        ax = figure.axes[0]
        legend = ax.get_legend()
        if legend is not None:
            labels = [t.get_text() for t in legend.get_texts()]
            if len(labels) == 1:
                if labels[0] == "Model":
                    legend.remove()
                    legend = None
        if legend is not None:
            # Put a legend to the right of the current axis
            legend._loc = 2
            legend.set_bbox_to_anchor((1, 1.1))
            ax.set_position(Bbox(array([[0.19, 0.3], [0.65, 0.9]])))
        else:
            ax.set_position(Bbox(array([[0.19, 0.3], [0.85, 0.9]])))

        # if is_stack_plot:
        #     figure.set_size_inches(5, 4)

        # for ax in figure.axes:
        #     ax.yaxis.label.set_size(14)
        #     ax.xaxis.label.set_size(14)
        #     ax.title.set_size(14)
        #
        #     ticklabels = ax.get_xticklabels() + ax.get_yticklabels()
        #     for ticklabel in ticklabels:
        #         ticklabel.set_size(10)
        #     legend = ax.get_legend()
        #     if legend is not None:
        #         texts = legend.get_texts()
        #         for text in texts:
        #             text.set_size(10)

    mpld3_dict = mpld3.fig_to_dict(figure)
    return normalize_obj(mpld3_dict)


def convert_to_selectors(graph_selectors):
    keys = graph_selectors['keys']
    names = graph_selectors['names']
    defaults = graph_selectors['defaults']
    print ">> make_mpld3_graph_dict keys", keys

    selectors = [
        {'key': key, 'name': name, 'checked': checked}
         for (key, name, checked) in zip(keys, names, defaults)]
    return selectors

def make_mpld3_graph_dict(result, which=None):
    """
    Converts an Optima sim Result into a dictionary containing
    mpld3 graph dictionaries and associated keys for display,
    which can be exported as JSON.

    Args:
        result: the Optima simulation Result object
        which: a list of keys to determine which plots to generate

    Returns:
        A dictionary of the form:
            { "graphs":
                "mpld3_graphs": [<mpld3 graph dictioanry>...],
                "graph_selectors": ["key of a selector",...],
                "selectors": [<selector dictionary>]
            }
            - mpld3_graphs is the same length as graph_selectors
            - selectors are shown on screen and graph_selectors refer to selectors
            - selector: {
                "key": "unique name",
                "name": "Long description",
                "checked": boolean
              }
        }
    """
    print ">> make_mpld3_graph_dict input which:", which

    if which is None:
        print ">> make_mpld3_graph_dict has cache:", hasattr(result, 'which')
        advanced = False
        if hasattr(result, 'which'):
            which = result.which
            print ">> make_mpld3_graph_dict cached options"
            if 'advanced' in result.which:
                advanced = True
                which.remove("advanced")
        else:
            which = ["default"]
    else:
        advanced = False
        if 'advanced' in which:
            advanced = True
            which.remove('advanced')

    print ">> make_mpld3_graph_dict advanced:", advanced

    graph_selectors = op.getplotselections(result, advanced=advanced) # BOSCO MODIFY
    if advanced:
        normal_graph_selectors = op.getplotselections(result)
        n = len(normal_graph_selectors['keys'])
        normal_default_keys = []
        for i in range(n):
            if normal_graph_selectors["defaults"][i]:
                normal_default_keys.append(normal_graph_selectors["keys"][i])
        normal_default_keys = tuple(normal_default_keys)
        # rough and dirty defaults for missing defaults in advanced
        n = len(graph_selectors['keys'])
        for i in range(n):
            key = graph_selectors['keys'][i]
            if key.startswith(normal_default_keys) and "-total" in key:
                graph_selectors['defaults'][i] = True
    selectors = convert_to_selectors(graph_selectors)

    if 'default' in which:
        which = [s["key"] for s in selectors if s["checked"]]
    else:
        which = [w for w in which if w in graph_selectors["keys"]]
        for selector in selectors:
            selector['checked'] = selector['key'] in which

    print ">> make_mpld3_graph_dict which:", which

    graphs = op.plotting.makeplots(result, toplot=which, figsize=(4, 3), die=False)

    graph_selectors = []
    mpld3_graphs = []
    for graph_key in graphs:
        graph_selectors.append(extract_graph_selector(graph_key))
        graph_dict = convert_to_mpld3(graphs[graph_key])
        if graph_key == "budget":
            graph = graphs[graph_key]
            ylabels = [l.get_text() for l in graph.axes[0].get_yticklabels()]
            graph_dict['ylabels'] = ylabels
        mpld3_graphs.append(graph_dict)

    return {
        'graphs': {
            "advanced": advanced,
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors,
            'resultId': str(result.uid),
        }
    }
