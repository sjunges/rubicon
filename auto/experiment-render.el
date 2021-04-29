(TeX-add-style-hook
 "experiment-render"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("inputenc" "utf8") ("enumitem" "inline")))
   (add-to-list 'LaTeX-verbatim-environments-local "lstlisting")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "lstinline")
   (add-to-list 'LaTeX-verbatim-macros-with-delims-local "lstinline")
   (TeX-run-style-hooks
    "latex2e"
    "article"
    "art10"
    "inputenc"
    "nicefrac"
    "microtype"
    "amsmath"
    "amssymb"
    "xcolor"
    "listings"
    "subfigure"
    "tikz"
    "mdframed"
    "wrapfig"
    "pgfplots"
    "graphicx"
    "tikz-cd"
    "paralist"
    "booktabs"
    "colonequals"
    "enumitem")
   (TeX-add-symbols
    '("program" ["argument"] 0)
    '("seteventuallybfrom" 3)
    '("seteventuallyb" 2)
    '("bddw" 3)
    '("bdd" 2)
    '("ct" 2)
    '("last" 1)
    '("eventuallyb" 1)
    '("semantics" 1)
    "prism"
    "modest"
    "jani"
    "rubicon"
    "storm"
    "epmc"
    "pgcl"
    "true"
    "false"
    "dice"
    "readcmd"
    "writecmd"
    "BB"
    "RR"
    "QQ"
    "RRnn"
    "fixdeadlock"
    "prog"
    "Cmd"
    "Vars"
    "valmap"
    "varmap"
    "weight"
    "globally"
    "eventually"
    "mc"
    "Distr"
    "Succ"
    "bisim"
    "reorder"
    "heads"
    "tails"
    "coinsweight"
    "coins"
    "coin"
    "coinsorder"
    "WMC"
    "Nat"
    "hPaths"
    "bool")
   (LaTeX-add-labels
    "plt:rubicon"
    "plt:stormexpl"
    "plt:stormsym"
    "plt:rubicon1"
    "plt:stormexp1"
    "plt:stormsymb1"
    "fig:expweather"
    "fig:expherman13"
    "fig:expherman13random"
    "fig:expherman17"
    "fig:expherman17random"
    "fig:expherman19"
    "fig:queues"
    "fig:scaling"))
 :latex)

