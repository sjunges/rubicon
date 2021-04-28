TO="100"
echo "Run with TO = $TO seconds"

eval $(opam env)

python rubicon/regression.py --graph-csv "fig1c.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO"  include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add factory -H 10 -N 5 -N 9 -N 12 -N 13 -N 15 -N 17 -N 19

python rubicon/regression.py --graph-csv "fig9a.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add weatherfactory -H 10 -N 9 -N 12 -N 15 -N 17


python rubicon/regression.py --graph-csv "fig9b.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add herman -N 13 -H 10 -H 20 -H 30 -H 40

python rubicon/regression.py --graph-csv "fig9c.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add herman -N 13 -H 10 -H 20 -H 30 -H 40 --asym

python rubicon/regression.py --graph-csv "fig9d.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add herman -N 17 -H 10 -H 20 -H 30 -H 40

python rubicon/regression.py --graph-csv "fig9e.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add herman -N 17 -H 10 -H 20 -H 30 -H 40 --asym

python rubicon/regression.py --graph-csv "fig9f.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add herman -N 19 -H 10 -H 20 -H 30 -H 40

python rubicon/regression.py --graph-csv "fig9g.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO "$TO" include-storm --cmd "storm" -TO "$TO" include-storm --cmd "storm" -TO "$TO" --add parqueues -N 8 -H 5 -H 10 -H 15

pdflatex experiment-render.tex
