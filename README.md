# Rubicon

Rubicon is based on 

- [1] Model Checking Finite-Horizon Markov Chains with Probabilistic Inference. Steven Holtzen, Sebastian Junges, Marcell Vazquez-Chanlatte, Todd Millstein, Sanjit A. Seshia and Guy Van den Broeck, CAV 2020

This prototype uses (the python bindings of) Storm [2] to model check finite horizon properties of DTMCs. It does so by translating DTMCs in the PRISM-language into Dice [3] and running inference with Dice.


## Docker Container

## Installation Procedure

Users of an artefact/Docker container can skip this step.

- Install storm and stormpy from source as usual . 
  (but using the repository ) 

## Experiments
To reproduce the experiments from [1], we provide additional scripts.

## How to run?

## Sources

## References
- [2] https://www.stormchecker.org
- [3] https://github.com/SHoltzen/dice/
