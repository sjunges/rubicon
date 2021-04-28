echo 'Making symbolic dice files'

python rubicon/rubicon.py --prism examples/factory/factory15-par.prism --prop 'P=? [F<=10 "allStrike"]' --output "factory-15-sym.dice"

python rubicon/rubicon.py --prism examples/factory/factory12-par.prism --prop 'P=? [F<=10 "allStrike"]' --output "factory-12-sym.dice"


echo 'Done making dice files, running benchmarks'


echo '================================================================================'
echo '12 Factory Compilation time'

dice factory-12-sym.dice -inline-functions -time -skip-table


echo '================================================================================'
echo '12 Factory Total WMC time'

dice factory-12-sym.dice -inline-functions -time -param examples/factory-params/factory-par-12-H\=5.dice.0.eval -param examples/factory-params/factory-par-12-H\=5.dice.1.eval -param examples/factory-params/factory-par-12-H\=5.dice.2.eval -param examples/factory-params/factory-par-12-H\=5.dice.3.eval -param examples/factory-params/factory-par-12-H\=5.dice.4.eval


echo '================================================================================'
echo '15 Factory Compilation Time'

dice factory-15-sym.dice -inline-functions -time

echo '================================================================================'
echo '15 Factory Total WMC'

dice factory-15-sym.dice -inline-functions -time -param examples/factory-params/factory-par-15-H\=5.dice.0.eval -param examples/factory-params/factory-par-15-H\=5.dice.1.eval -param examples/factory-params/factory-par-15-H\=5.dice.2.eval -param examples/factory-params/factory-par-15-H\=5.dice.3.eval -param examples/factory-params/factory-par-15-H\=5.dice.4.eval
