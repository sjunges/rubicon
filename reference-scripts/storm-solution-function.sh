#!/bin/bash

STORM_DIR=$1
echo "Storm directory set to $STORM_DIR"
echo "Expect storm-pars at $STORM_DIR/bin/storm-pars"
EXAMPLE_DIR=$2
echo "Example directory is $EXAMPLE_DIR"
TO=$3
echo "Timeout is $TO"

echo "Running small model to check everything is fine..."
timeout $3 $STORM_DIR/bin/storm-pars --prism $EXAMPLE_DIR/factory/factory5-par.prism --prop 'P=? [ F<=2 "allStrike"]'
echo "Running models from table..."
timeout $3 $STORM_DIR/bin/storm-pars --prism $EXAMPLE_DIR/herman/herman-13-random-parametric.prism --prop 'P=? [ F<=15 "stable"]'
timeout $3 $STORM_DIR/bin/storm-pars --prism $EXAMPLE_DIR/herman/herman-17-random-parametric.prism --prop 'P=? [ F<=15 "stable"]'
timeout $3 $STORM_DIR/bin/storm-pars --prism $EXAMPLE_DIR/factory/factory12-par.prism --prop 'P=? [ F<=10 "allStrike"]'
timeout $3 $STORM_DIR/bin/storm-pars --prism $EXAMPLE_DIR/factory/factory15-par.prism --prop 'P=? [ F<=10 "allStrike"]'