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
To export files out of the Docker image,
files that are in the `/data` directory inside the image are available on the host system in the current working directory.

## Installation Procedure

Users of an artifact/Docker container can skip this step.

- Install Storm and Stormpy from source [as usual](https://moves-rwth.github.io/stormpy/installation.html).
    - but using [this repository for Storm](https://github.com/sjunges/storm/tree/prismlang-sim)
    - and [this repository for Stormpy](https://github.com/sjunges/stormpy/tree/prismlang-sim)
    (Note: These branches are in the process of being merged back into Storm(py) version 1.7.0)
- Install Dice from source [from this branch](https://github.com/SHoltzen/dice/tree/symbolic)

## Experiments
To reproduce the experiments from [1], we provide some convenience scripts. 
We first go through the steps of reproducing data, then give some general usage rules.
Throughout, we assume you use the Docker container.


First, inside the Docker container, 
set up the environment by executing:

```
eval $(opam env)
```

### Recreating the Figures and Tables in the Paper
The following commands each generate a CSV file that contains the data that is used to generate each figure. All experiments are run with a default timeout of 1000 seconds; if the time to run the experiment exceeds this amount then the time and final result will both be reported as `-1`.

To generate a CSV file for **Figure 1c**, please run:

```
python rubicon/regression.py --export-csv "fig1c.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add factory -H 10 -N 5 -N 9 -N 12 -N 13 -N 15 -N 17 -N 19
```
This will create a series of benchmark evaluations with horizon 10 (`-H 10`) and 8, 10, 13, 15, 17, and 19 parallel factories. This generates a file `fig1c.csv` which has the following contents (note that precise numbers may vary due to differences in the running environment, but the important thing is that the relative trend of rubicon scaling to more states holds):
```
family, instance, dice-time, dice-result, storm-time, storm-result
factory,N=5;horizon=10,0.01,0.04459,0.02,0.04459
factory,N=9;horizon=10,0.04,0.00054,0.19,0.00054
factory,N=12;horizon=10,0.54,0.00003,12.84,0.00003
...
```

**Figure 9a**: 
```
python rubicon/regression.py --export-csv "fig9a.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add weatherfactory -H 10 -N 9 -N 12 -N 15 -N 17
```

**Figure 9b**:
```
python rubicon/regression.py --export-csv "fig9b.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add herman -N 13 -H 10 -H 20 -H 30 -H 40
```

**Figure 9c**:
```
python rubicon/regression.py --export-csv "fig9c.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add herman -N 13 -H 10 -H 20 -H 30 -H 40 --asym
```

**Figure 9d**:
```
python rubicon/regression.py --export-csv "fig9d.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add herman -N 17 -H 10 -H 20 -H 30 -H 40
```

**Figure 9e**:
```
python rubicon/regression.py --export-csv "fig9e.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add herman -N 17 -H 10 -H 20 -H 30 -H 40 --asym
```

**Figure 9f**:
```
python rubicon/regression.py --export-csv "fig9f.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add herman -N 19 -H 10 -H 20 -H 30 -H 40
```

**Figure 9g**:
```
python rubicon/regression.py --export-csv "fig9g.csv" include-dice --cwd "/opt/rubicon" --cmd "dice" -TO 1800 include-storm --cmd "storm" -TO 1800 include-storm --cmd "storm" -TO 1800 --add herman -N 19 -H 10 -H 20 -H 30 -H 40 --asym
```

**Table 1 (left column)**:

**Table 1 (middle column)**:

**Table 1 (right column)**:

### More examples

You can use our regression suite to generate many more tests.

```
python rubicon/regression.py brp -H 5 -H 15 -N 8 -N 10 
```

If things ever break, be sure to check out the logfile `rubicon-regression.log`.

#### Invoking Dice directly

We can configure the script to run Dice (from commandline) directly:
```
python rubicon/regression.py include-dice --cwd "/opt/rubicon" --cmd "dice" --only-parse weatherfactory -H 10 -H 15 -N 8 -N 10 
```


## Creating a Docker Container

The docker container is built using the included Dockerfile. 
The container is based on an container for the probabilistic model checker as provided by the storm developers, 
see [this documentation](https://www.stormchecker.org/documentation/obtain-storm/docker.html)
The container can be built by executing a command in the `rubicon` directory like:

```
docker build --tag rubicon:1.0 .
```

## References
- [2] https://www.stormchecker.org
- [3] https://github.com/SHoltzen/dice/


# FAQ

* Q: I got a `FileNotFoundError: [Errno 2] No such file or directory: 'dice'` error!
  
  A: Please run `eval $(opam env)` and then try again.
* Q: How can I install things in the docker image?
   
   A: Use `apt-get`, for instance `apt-get install vim`

* Q: Help I got `docker: Got permission denied while trying to connect to the Docker daemon socket`

  A: Run docker using administrative rights (`sudo`)
