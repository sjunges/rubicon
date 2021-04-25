# Rubicon

Rubicon is based on 

- [1] Model Checking Finite-Horizon Markov Chains with Probabilistic Inference. Steven Holtzen, Sebastian Junges, Marcell Vazquez-Chanlatte, Todd Millstein, Sanjit A. Seshia and Guy Van den Broeck, CAV 2020

This prototype uses (the python bindings of) Storm [2] to model check finite horizon properties of DTMCs. It does so by translating DTMCs in the PRISM-language into Dice [3] and running inference with Dice.

## Running Rubicon inside a Docker container

We provide a docker container

```
docker pull sjunges/rubicon:cav21
```

The container is based on an container for the probabilistic model checker as provided by the storm developers, 
see [this documentation](https://www.stormchecker.org/documentation/obtain-storm/docker.html).

The following command will run the docker container (for Windows platforms, please see the documentation from the storm website).
```
docker run --mount type=bind,source="$(pwd)",target=/data -w /opt/rubicon --rm -it --name rubicon sjunges/rubicon:cav21
```
Files that one copies into `/data` are available on the host system in the current working directory. 

## Installation Procedure

Users of an artefact/Docker container can skip this step.

- Install Storm and Stormpy from source [as usual](https://moves-rwth.github.io/stormpy/installation.html).
    - but using [this repository for Storm](https://github.com/sjunges/storm/tree/prismlang-sim)
    - and [this repository for Stormpy](https://github.com/sjunges/stormpy/tree/prismlang-sim)
    (Note: These branches are in the process of being merged back into Storm(py) version 1.7.0)
- Install Dice from source [from this branch](https://github.com/SHoltzen/dice/blob/master/README.md)

## Experiments
To reproduce the experiments from [1], we provide some convenience scripts.

### Transpilation process
In particular, please run 
```
python rubicon/regression.py factory -H 10 -H 15 -N 8 -N 10 
```
to create four Dice programs for the factory benchmark into `dice-examples/factory`
(the programs will correspond to the combinations of having a 8 or 10 factories and a horizon of 10 or 15 steps).

Similar options are available for other benchmarks, e.g.:
```
python rubicon/regression.py weatherfactory -H 10 -H 15 -N 8 -N 10 
```
to create the weather factories with the same parameters, or 
```
python rubicon/regression.py herman --asym -H 10 -H 15 -N 13 
```
to create the asymetric version of Herman protocol

### Invoking Dice directly

We can configure the script to run Dice (from commandline) directly:
```
python rubicon/regression.py include-dice --cwd "/opt/rubicon" --cmd "dice" weatherfactory -H 10 -H 15 -N 8 -N 10 
```


## How to run Rubicon on own files?



## Creating a Docker Container

The docker container is built using the included Dockerfile. 
The container is based on an container for the probabilistic model checker as provided by the storm developers, 
see [this documentation](https://www.stormchecker.org/documentation/obtain-storm/docker.html)

## Sources

## References
- [2] https://www.stormchecker.org
- [3] https://github.com/SHoltzen/dice/
