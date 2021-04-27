import os.path
import rubicon
import dice_wrapper
import click
import numpy as np
from pathlib import Path


def get_examples_path(family, filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", family, filename)

def get_output_path(family, filename):
    dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dice-examples", family)
    Path(dirpath).mkdir(parents=False, exist_ok=True)
    return os.path.join(dirpath, filename)


class RubiconContext:
    def __init__(self, dice):
        self.dice_wrapper = dice

@click.group(chain=True)
@click.pass_context
def cli(ctx):
    dice = None
    ctx.obj = RubiconContext(dice)
    return ctx

@cli.command()
@click.option("--cwd", default=".")
@click.option("--cmd", default="dice")
@click.option("--extra-arguments", default="")
@click.option("--only-parse", is_flag=True)
@click.pass_context
def include_dice(ctx, cwd, cmd, extra_arguments, only_parse):
    if extra_arguments == "":
        arguments = []
    else:
        arguments = extra_arguments.strip().split(" ")
    if only_parse:
        arguments += ["-skip-table"]
    dice = dice_wrapper.Dice(cwd, cmd, arguments)
    ctx.obj.dice_wrapper = dice


#
# for N in [3,10,100,1000]:
#      for M in [3,10,100,1000]:
#          rubicon.translate(get_examples_path("adversarialexample.prism"), "P=? [ F \"goal\" ]", f"N={N},M={M}", f"adv-grid-{N}-{M}-tg.dice",force_bounded=True, track_goal = True)
#          rubicon.translate(get_examples_path("adversarialexample-c.prism"), "P=? [ F \"goal\" ]", f"N={N},M={M}",
#                            f"adv-grid-c-{N}-{M}-tg.dice", force_bounded=True, track_goal = True)
#
# pvals = { "p" : [i * 0.02 for i in range(1,50)] }
# for H in [1, 2, 3, 5, 10, 15, 20]:
#     rubicon.translate(get_examples_path("herman-19.prism"), f"P=? [ F<={H} \"stable\" ]", f"", get_output_path(f"herman-19-H={H}.dice"), overlapping_guards=True, make_flat=False)
#     rubicon.translate(get_examples_path("herman-19-random-input.prism"), f"P=? [ F<={H} \"stable\" ]", f"", get_output_path(f"herman-19-ri-H={H}.dice"), overlapping_guards=True, make_flat=False)

#rubicon.translate(get_examples_path("herman-13.prism"), "P=? [ F<=20 \"stable\" ]", f"p={0.5}", "herman-13-tg-0.5.dice", overlapping_guards=True, make_flat=False, track_goal = True)
#rubicon.translate(get_examples_path("herman-17.prism"), "P=? [ F<=20 \"stable\" ]", f"", "herman-17-tg.dice",parameter_instantiations=pvals, overlapping_guards=True, make_flat=False, track_goal = True)
# rubicon.translate(get_examples_path("herman-pass-13.prism"), "P=? [ F<=20 \"stable\" ]", f"", "herman-pass-13.dice",parameter_instantiations=pvals, overlapping_guards=True, make_flat=False)
# rubicon.translate(get_examples_path("herman-13.prism"), "P=? [ F<=5 \"stable\" ]", f"p=0.340", "herman-13-f.dice", overlapping_guards=True, make_flat=False)
#
#
# rubicon.translate(get_examples_path("herman-13-random-input.prism"), "P=? [ F<=5 \"stable\" ]", f"", "herman-13-ri.dice", overlapping_guards=True, make_flat=False)
#rubicon.translate(get_examples_path("herman-pass-13.prism"), "P=? [ F<=20 \"stable\" ]", f"", "herman-pass-13.dice", overlapping_guards=True, make_flat=False)
#
def _sample():
    res = 0.0
    while res == 0.0:
        res = np.random.random_sample()
    return res

def _run(rubicon_context, prism_path, prop, consts, dice_path, **kwargs):
    rubicon.translate(prism_path, prop, consts, dice_path, **kwargs)
    if rubicon_context.dice_wrapper is not None:
        rubicon_context.dice_wrapper.run(dice_path)

@cli.command()
@click.option("--nr_factories", "-N", type=click.Choice(['10', '12', '15']), multiple=True, default=[10])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def factory_parametric(nr_factories, horizon):
    for N in nr_factories:
        pvals = [{**{f"p{n}": _sample() for n in range(1, N + 1)}, **{f"q{n}": _sample() for n in range(1, N + 1)}} for _
                 in range(5)]

        for H in horizon:
            rubicon.translate(get_examples_path(f"factory{N}-par.prism"), f"P=? [ F<={H} \"allStrike\"]", "", get_output_path(f"factory-{N}-H={H}.dice"), parameter_instantiations=pvals)


@cli.command()
@click.option("--nr_factories", "-N", type=click.IntRange(8,25), multiple=True, default=[10])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def factory(ctx, nr_factories, horizon):
    for N in nr_factories:
        for H in horizon:
            _run(ctx.obj, get_examples_path("factory", f"factory{N}.prism"), f"P=? [ F<={H} \"allStrike\"]", "",
                 get_output_path("factory", f"factory{N}-H={H}.dice"))


@cli.command()
@click.option("--nr_factories", "-N", type=click.IntRange(7,20), multiple=True, default=[10])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def weatherfactory(ctx, nr_factories, horizon):
    for N in nr_factories:
        for H in horizon:
            _run(ctx.obj, get_examples_path("weatherfactory", f"weatherfactory{N}.prism"), f"P=? [ F<={H} \"allStrike\"]", "",
                 get_output_path("weatherfactory", f"weatherfactory{N}-H={H}.dice"))


@cli.command()
@click.option("--nr-queues", "-Q", type=click.Choice([8, 9, 10]), multiple=True, default=[8])
@click.option("--nr-elements", "-N", type=click.IntRange(2,None), multiple=True, default=[3])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def parqueues(ctx, nr_queues, nr_elements, horizon):
    for K in nr_queues:
         for N in nr_elements:
             for H in horizon:
                 _run(ctx.obj, get_examples_path("parqueues", f"queue-{K}.nm"), f"P=? [ F<={H} \"target\" ]", f"N={N}", get_output_path("parqueues", f"queues-{K}-{N}-H={H}.dice"), force_bounded=True)


@cli.command()
@click.option("--nr-stations", "-N", type=click.Choice([13, 15, 17, 19]), multiple=True, default=[13])
@click.option("--asym", is_flag=True, help="Are the station probabilities asymmetric?")
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def herman(ctx, nr_stations, asym, horizon):
    for N in nr_stations:
        for H in horizon:
            if asym:
                _run(ctx.obj, get_examples_path("herman", f"herman-{N}-random-input.prism"), f"P=? [ F<={H} \"stable\" ]", f"",
                     get_output_path("herman", f"herman-ri-{N}-H={H}.dice"), overlapping_guards=True)
            else:
                _run(ctx.obj, get_examples_path("herman", f"herman-{N}.prism"), f"P=? [ F<={H} \"stable\" ]", f"", get_output_path("herman", f"herman-{N}-H={H}.dice"), overlapping_guards=True)


@cli.command()
@click.option("--chunks", "-N", type=click.IntRange(2, None), multiple=True, default=[8])
@click.option("--retries", "-MAX", type=click.IntRange(2,10), multiple=True, default=[3])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def brp(ctx, chunks, retries, horizon):
    for N in chunks:
        for MAX in retries:
             for H in horizon:
                 _run(ctx.obj, get_examples_path("brp", "brp.v1.prism"), f"P=? [ F<={H} s=5 ]", f"N={N},MAX={MAX}", get_output_path("brp", f"brp-{N}-{MAX}-H={H}.dice"), make_flat=False)


@cli.command()
@click.option("--n-values", "-N", type=click.IntRange(2, None), multiple=True, default=[10])
@click.option("--k-values", "-K", type=click.IntRange(2,6), multiple=True, default=[2])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def nand(ctx, n_values, k_values, horizon):
    for N in n_values:
        for K in k_values:
            for H in horizon:
                _run(ctx.obj, get_examples_path("nand", "nand.v1.prism"), f"P=? [ F<={H} s=4 & 10*z<N ]", f"N={N},K={K}", get_output_path("nand", f"nand-{N}-{K}-H={H}.dice"))


@cli.command()
@click.option("--N-values", "-N", type=click.IntRange(2,None), multiple=True, default=[5])
@click.option("--L-values", "-L", type=click.IntRange(2,None), multiple=True, default=[2])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def egl(ctx, n_values, l_values, horizon):
    for N in n_values:
        for L in l_values:
            for H in horizon:
                _run(ctx.obj, get_examples_path("egl","egl.v1.prism"), f"P=? [ F<={H} !\"knowA\" & \"knowB\" ]", f"N={N},L={L}", get_output_path("egl", f"egl-{N}-{L}-H={H}.dice"), force_max_int_val=20)


@cli.command()
@click.option("--runs", "-R", type=click.IntRange(1,None), multiple=True, default=[3])
@click.option("--crowdsize", "-S", type=click.IntRange(2,20), multiple=True, default=[3])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[1])
@click.pass_context
def crowds(ctx, runs, crowdsize, horizon):
    for R in runs:
        for S in crowdsize:
            for H in horizon:
                _run(ctx.obj, get_examples_path("crowds", "crowds.v1.prism"), f"P=? [ F<={H} observe0>1]", f"TotalRuns={R},CrowdSize={S},PF=0.8,badC=0.2", get_output_path("crowds", f"crowds-{R}-{S}-H={H}.dice"), overlapping_guards=True)


@cli.command()
@click.option("--n-values", "-N", type=click.Choice([4,6]), multiple=True, default=[4])
@click.option("--k-values", "-K", type=click.Choice([2,8]), multiple=True, default=[2])
@click.option("--horizon", "-H", type=click.IntRange(0,None), multiple=True, default=[10])
@click.pass_context
def leader(ctx, n_values, k_values, horizon):
    for N in n_values:
        for K in k_values:
            for H in horizon:
                _run(ctx.obj, get_examples_path("leader_sync", f"leader_synch_{N}_{K}.prism"), f"P=? [ F<={H} \"elected\" ]", "", get_output_path("leader_sync",  f"leader_sync_{N}_{K}-H={H}.dice"), make_flat=False, force_bounded=True)


if __name__ == "__main__":
    cli()
