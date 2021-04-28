import os.path
import json
import logging
import rubicon
import dice_wrapper
import storm_wrapper
import click
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
chformatter = logging.Formatter('%(message)s')

# add formatter to ch
ch.setFormatter(chformatter)
fhformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler("rubicon-regression.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(fhformatter)

# add ch to logger
root.addHandler(ch)
root.addHandler(fh)

def get_examples_path(family, filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", family, filename)

def get_output_path(family, filename):
    dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dice-examples", family)
    Path(dirpath).mkdir(parents=False, exist_ok=True)
    return os.path.join(dirpath, filename)


class RubiconContext:
    def __init__(self, stats_path, csv_path):
        self.stats_path = stats_path
        self.csv_path = csv_path
        self.dice_wrapper = None
        self.storm_wrappers = []
        self._all_stats = []

    def store_stats(self, stats_dict):
        self._all_stats.append(stats_dict)
        with open(self.stats_path, 'w') as file:
            json.dump(self._all_stats, file)

    def _tool_ids(self):
        ids = []
        if self.dice_wrapper is not None:
            ids.append("dice")
        for wrapper in self.storm_wrappers:
            ids.append(wrapper.id)
        return ids

    def finalize(self):
        if self.csv_path is not None:
            logger.info(f"Export stats to {self.csv_path}")
            with open(self.csv_path, 'w') as file:
                file.write("family, instance")
                if self.dice_wrapper is not None:
                    file.write(",dice-time,dice-result")
                for wrapper in self.storm_wrappers:
                    file.write(f",{wrapper.id}-time,{wrapper.id}-result")
                file.write("\n")

                for stats in self._all_stats:
                    row = [stats["family"], ";".join([f"{k}={v}" for k,v in stats["identifiers"].items()])]
                    for tool in self._tool_ids():
                        if tool in stats:
                            row.append("{:.2f}".format(float(stats[tool]["total_time"])))
                            row.append("{:.5f}".format(float(stats[tool]["result"])))
                        else:
                            row.append("")
                            row.append("")
                    file.write(",".join(row))

                    file.write("\n")

@click.group(chain=True)
@click.option("--stats-file", default="stats.json")
@click.option("--export-csv", help="path for csv output")
@click.pass_context
def cli(ctx, stats_file, export_csv):
    ctx.obj = RubiconContext(stats_file, export_csv)
    return ctx

@cli.command()
@click.option("--cwd", default=".")
@click.option("--cmd", default="dice")
@click.option("--extra-arguments", default="")
@click.option("--only-parse", is_flag=True)
@click.option("--timeout", "-TO", type=int, help="Time out", default="900")
@click.pass_context
def include_dice(ctx, cwd, cmd, extra_arguments, only_parse, timeout):
    if extra_arguments == "":
        arguments = []
    else:
        arguments = extra_arguments.strip().split(" ")
    if only_parse:
        arguments += ["-skip-table"]
    dice = dice_wrapper.Dice(cwd, cmd, arguments, timeout)
    ctx.obj.dice_wrapper = dice
    return ctx

@cli.command()
@click.option("--cwd", default=".")
@click.option("--cmd", default="dice")
@click.option("--extra-arguments", default="")
@click.option("--add", is_flag=True)
@click.option("--timeout", "-TO", type=int, help="Time out", default="900")
@click.pass_context
def include_storm(ctx, cwd, cmd, extra_arguments, add, timeout):
    if extra_arguments == "":
        arguments = []
    else:
        arguments = extra_arguments.strip().split(" ")
    storm = storm_wrapper.Storm(cwd, cmd, arguments, symbolic=add, timeout=timeout)
    ctx.obj.storm_wrappers.append(storm)
    return ctx

def _sample():
    res = 0.0
    while res == 0.0:
        res = np.random.random_sample()
    return res

def _run(rubicon_context, family_name, instance, prism_path, prop, consts, dice_path, parameter_instantiations = dict(), **kwargs):
    rubicon.translate(prism_path, prop, consts, dice_path, parameter_instantiations=parameter_instantiations, **kwargs)
    stats = dict()
    stats["family"] = family_name
    stats["identifiers"] = instance
    stats["prism_path"] = prism_path
    stats["prop"] = prop
    stats["constants"] = consts
    if rubicon_context.dice_wrapper is not None:
        stats["dice"] = rubicon_context.dice_wrapper.run(dice_path)
    if len(parameter_instantiations) > 0 and len(rubicon_context.storm_wrappers):
        print("Warning, this script does not support parametric capabilities of storm.")
    for wrapper in rubicon_context.storm_wrappers:
        stats[wrapper.id] = wrapper.run(prism_path, prop, consts)
    rubicon_context.store_stats(stats)


@cli.command()
@click.option("--nr_factories", "-N", type=click.Choice(['10', '12', '15']), multiple=True, default=['10'])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def factory_parametric(ctx, nr_factories, horizon):
    for N in nr_factories:
        pvals = [{**{f"p{n}": _sample() for n in range(1, N + 1)}, **{f"q{n}": _sample() for n in range(1, N + 1)}} for _
                 in range(5)]

        for H in horizon:
            rubicon.translate(get_examples_path(f"factory{N}-par.prism"), f"P=? [ F<={H} \"allStrike\"]", "", get_output_path(f"factory-{N}-H={H}.dice"), parameter_instantiations=pvals)
    return ctx


@cli.command()
@click.option("--nr_factories", "-N", type=click.IntRange(8,25), multiple=True, default=[10])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def factory(ctx, nr_factories, horizon):
    for N in nr_factories:
        for H in horizon:
            _run(ctx.obj, "factory", {"N": N, "horizon": H}, get_examples_path("factory", f"factory{N}.prism"), f"P=? [ F<={H} \"allStrike\"]", "",
                 get_output_path("factory", f"factory{N}-H={H}.dice"))
    return ctx


@cli.command()
@click.option("--nr_factories", "-N", type=click.IntRange(7,20), multiple=True, default=[10])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def weatherfactory(ctx, nr_factories, horizon):
    for N in nr_factories:
        for H in horizon:
            _run(ctx.obj, "weatherfactory", {"N": N, "horizon": H}, get_examples_path("weatherfactory", f"weatherfactory{N}.prism"), f"P=? [ F<={H} \"allStrike\"]", "",
                 get_output_path("weatherfactory", f"weatherfactory{N}-H={H}.dice"))
    return ctx


@cli.command()
@click.option("--nr-queues", "-Q", type=click.Choice(['8', '9', '10']), multiple=True, default=['8'])
@click.option("--nr-elements", "-N", type=click.IntRange(2,None), multiple=True, default=[3])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def parqueues(ctx, nr_queues, nr_elements, horizon):
    for K in nr_queues:
        K = int(K)
        for N in nr_elements:
             for H in horizon:
                 _run(ctx.obj,  "parqueues", {"K": K, "N": N, "horizon": H}, get_examples_path("parqueues", f"queue-{K}.nm"), f"P=? [ F<={H} \"target\" ]", f"N={N}", get_output_path("parqueues", f"queues-{K}-{N}-H={H}.dice"), force_bounded=True)
    return ctx


@cli.command()
@click.option("--nr-stations", "-N", type=click.Choice(['13', '15', '17', '19']), multiple=True, default=['13'])
@click.option("--asym", is_flag=True, help="Are the station probabilities asymmetric?")
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def herman(ctx, nr_stations, asym, horizon):
    for N in nr_stations:
        N = int(N)
        for H in horizon:
            if asym:
                _run(ctx.obj, "herman", {"asym": True, "N": N, "horizon": H}, get_examples_path("herman", f"herman-{N}-random-input.prism"), f"P=? [ F<={H} \"stable\" ]", f"",
                     get_output_path("herman", f"herman-ri-{N}-H={H}.dice"), overlapping_guards=True)
            else:
                _run(ctx.obj, "herman", {"asym": False, "N": N, "horizon": H}, get_examples_path("herman", f"herman-{N}.prism"), f"P=? [ F<={H} \"stable\" ]", f"", get_output_path("herman", f"herman-{N}-H={H}.dice"), overlapping_guards=True)
    return ctx


@cli.command()
@click.option("--nr-stations", "-N", type=click.Choice(['13', '15', '17', '19']), multiple=True, default=['13'])
@click.option("--asym", is_flag=True, help="Are the station probabilities asymmetric?")
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def herman_parametric(ctx, nr_stations, asym, horizon):
    if not asym:
        raise RuntimeError("We currently only integrated an asymetric version of parametric herman")
    for N in nr_stations:
        N = int(N)
        pvals = [{**{f"p{n}": _sample() for n in range(1, N + 1)}} for
                 _
                 in range(5)]
        for H in horizon:
            if asym:
                _run(ctx.obj, "herman", {"asym": True, "N": N, "horizon": H}, get_examples_path("herman", f"herman-{N}-random-parametric.prism"), f"P=? [ F<={H} \"stable\" ]", f"",
                     get_output_path("herman", f"herman-ri-par-{N}-H={H}.dice"), overlapping_guards=True,parameter_instantiations=pvals)
            else:
                assert False, "Check is before"
    return ctx


@cli.command()
@click.option("--chunks", "-N", type=click.IntRange(2, None), multiple=True, default=[8])
@click.option("--retries", "-MAX", type=click.IntRange(2,10), multiple=True, default=[3])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def brp(ctx, chunks, retries, horizon):
    for N in chunks:
        for MAX in retries:
             for H in horizon:
                 _run(ctx.obj,  "brp", {"retries": MAX, "chunks": N, "horizon": H}, get_examples_path("brp", "brp.v1.prism"), f"P=? [ F<={H} s=5 ]", f"N={N},MAX={MAX}", get_output_path("brp", f"brp-{N}-{MAX}-H={H}.dice"), make_flat=False)
    return ctx


@cli.command()
@click.option("--n-values", "-N", type=click.IntRange(2, None), multiple=True, default=[10])
@click.option("--k-values", "-K", type=click.IntRange(2,6), multiple=True, default=[2])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def nand(ctx, n_values, k_values, horizon):
    for N in n_values:
        for K in k_values:
            for H in horizon:
                _run(ctx.obj, "nand", {"N": N, "K": K, "horizon": H}, get_examples_path("nand", "nand.v1.prism"), f"P=? [ F<={H} s=4 & 10*z<N ]", f"N={N},K={K}", get_output_path("nand", f"nand-{N}-{K}-H={H}.dice"))
    return ctx


@cli.command()
@click.option("--N-values", "-N", type=click.IntRange(2,None), multiple=True, default=[5])
@click.option("--L-values", "-L", type=click.IntRange(2,None), multiple=True, default=[2])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def egl(ctx, n_values, l_values, horizon):
    for N in n_values:
        for L in l_values:
            for H in horizon:
                _run(ctx.obj, "egl", {"N": N, "L": L, "horizon": H}, get_examples_path("egl","egl.v1.prism"), f"P=? [ F<={H} !\"knowA\" & \"knowB\" ]", f"N={N},L={L}", get_output_path("egl", f"egl-{N}-{L}-H={H}.dice"), force_max_int_val=20)
    return ctx


@cli.command()
@click.option("--runs", "-R", type=click.IntRange(1,None), multiple=True, default=[3])
@click.option("--crowdsize", "-S", type=click.IntRange(2,20), multiple=True, default=[3])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[1])
@click.pass_context
def crowds(ctx, runs, crowdsize, horizon):
    for R in runs:
        for S in crowdsize:
            for H in horizon:
                _run(ctx.obj, "crowds", {"Runs": R, "Size": S, "horizon": H}, get_examples_path("crowds", "crowds.v1.prism"), f"P=? [ F<={H} observe0>1]", f"TotalRuns={R},CrowdSize={S},PF=0.8,badC=0.2", get_output_path("crowds", f"crowds-{R}-{S}-H={H}.dice"), overlapping_guards=True)
    return ctx


@cli.command()
@click.option("--n-values", "-N", type=click.Choice(['4','6']), multiple=True, default=['4'])
@click.option("--k-values", "-K", type=click.Choice(['2','8']), multiple=True, default=['2'])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def leader(ctx, n_values, k_values, horizon):
    for N in n_values:
        N = int(N)
        for K in k_values:
            K = int(K)
            for H in horizon:
                _run(ctx.obj, "leader", {"N": N, "K": K, "horizon": H}, get_examples_path("leader_sync", f"leader_synch_{N}_{K}.prism"), f"P=? [ F<={H} \"elected\" ]", "", get_output_path("leader_sync",  f"leader_sync_{N}_{K}-H={H}.dice"), make_flat=False, force_bounded=True)
    return ctx


if __name__ == "__main__":
    state = cli(standalone_mode=False)
    if state is not None and type(state) is not int:
        ctx = state[0].obj
        ctx.finalize()
