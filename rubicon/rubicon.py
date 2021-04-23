import itertools
import re
import math

import click
import stormpy
import stormpy.examples.files
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


@click.command()
@click.option('--model', help='The model to translate')
@click.option('--property', help='Property file.')
@click.option('--constants', help="Constants")
@click.option('--output', help="")
def translate_cli(model, property, constants, output):
    """Generate Dice Programs from the cli"""
    translate(model, property, constants, output)

def translate(model, property, constants, output, parameter_instantiations = dict(), overlapping_guards=True, make_flat = False, force_bounded = True, track_goal = False, force_max_int_val = 0):
    program, props = load_prism_program(model, property, constants)
    assert len(props) == 1, "One prop in, one prop out"
    if make_flat and not overlapping_guards:
        raise RuntimeError("This is likely not supported")
    if props[0].raw_formula.is_probability_operator:
        if props[0].raw_formula.subformula.is_bounded_until_formula:
            step_bound = props[0].raw_formula.subformula.upper_bound_expression.evaluate_as_int()
            prob0expressions = ["false"]
        elif force_bounded:
            step_bound, prob0expressions = compute_model_parameters(program, props, compute_prob0_expressions=False)
        else:
            step_bound, prob0expressions = compute_model_parameters(program, props)
    else:
        raise RuntimeError("Only probabilties are supported")
    if make_flat:
        program = make_program_flat(program)
    maxintval = force_max_int_val
    for m in program.modules:
        if len(m.integer_variables) > 0:
            maxintval = max(maxintval, math.ceil(math.log2(
                max([v.upper_bound_expression.evaluate_as_int() + 1 for v in m.integer_variables]))))

    translate_prism(program, props, step_bound, maxintval, prob0expressions, output, parameter_instantiations, has_overlapping_guards=overlapping_guards, track_goal=track_goal)

def load_prism_program(model_path, property_string, constants_string):
    program = stormpy.parse_prism_program(model_path)
    expr_manager = program.expression_manager
    constants = dict() if constants_string == "" else {it.split("=")[0]: it.split("=")[1] for it in constants_string.split(",")}
    constants = {program.get_constant(c).expression_variable: (expr_manager.create_integer(int(v)) if program.get_constant(c).type.is_integer else expr_manager.create_rational(stormpy.Rational(v))) for c, v in
                 constants.items()}
    program = program.define_constants(constants)
    program = program.substitute_formulas()
    program = program.substitute_constants()
    props = stormpy.parse_properties_for_prism_program(property_string, program)
    return program, props

def compute_model_parameters(program, props, compute_prob0_expressions = True):
    model = stormpy.build_symbolic_model(program.substitute_nonstandard_predicates(), props)
    model_depth = model.compute_depth()
    raw_formula_copy = props[0].raw_formula.clone()
    if raw_formula_copy.has_bound:
        raise NotImplementedError("Not implemented")
    else:
        raw_formula_copy.set_bound(stormpy.logic.ComparisonType.LEQ, program.expression_manager.create_rational(0))
    qualitative_prop = stormpy.Property("prob0", raw_formula_copy)
    result = stormpy.model_checking(model, qualitative_prop, only_initial_states=False).get_truth_values()
    expressions, mapping = result.to_expression(program.expression_manager)
    expr_manager = program.expression_manager
    subst = dict()
    for k in result.meta_variables:
        if model.dd_manager.get_meta_variable(k).type == stormpy.DdMetaVariableType.Bool:
            assert len(model.dd_manager.get_meta_variable(k).compute_indices()) == 1
            idx = model.dd_manager.get_meta_variable(k).compute_indices()[0]
            if idx not in mapping:
                continue
            subst[mapping[idx]] = expr_manager.get_variable(model.dd_manager.get_meta_variable(k).name).get_expression()
        elif model.dd_manager.get_meta_variable(k).type == stormpy.DdMetaVariableType.Int:
            max_offset = len(model.dd_manager.get_meta_variable(k).compute_indices())
            for offset, idx in enumerate(model.dd_manager.get_meta_variable(k).compute_indices()):
                if idx not in mapping:
                    continue
                pow = int(math.pow(2, max_offset - offset - 1))

                expr = stormpy.storage.Expression.Modulo(
                    stormpy.storage.Expression.Divide(stormpy.storage.Expression.Minus(
                        expr_manager.get_variable(model.dd_manager.get_meta_variable(k).name).get_expression(),
                        expr_manager.create_integer(model.dd_manager.get_meta_variable(k).lowest_value)),
                        expr_manager.create_integer(pow)),
                    expr_manager.create_integer(2))

                subst[mapping[idx]] = stormpy.storage.Expression.Eq(expr, expr_manager.create_integer(1)).simplify()
        else:
            assert False

    for k, v in subst.items():
        print("{} -> {}".format(k.name, v))

    if compute_prob0_expressions:
        prob0expressions = []
        final_res = None
        for expr in expressions:
            expr = expr.substitute(subst)
            if expr.is_variable():
                final_res = expr
            elif expr.get_operand(0).is_variable():
                prob0expressions.append((expr.get_operand(0), expr.get_operand(1)))
            elif expr.get_operand(1).is_variable():
                prob0expressions.append((expr.get_operand(1), expr.get_operand(0)))
        prob0expressions.append(final_res)
    else:
        prob0expressions = ["false"]
    return model_depth, prob0expressions

def make_program_flat(program):
    flat_program = program.flatten().simplify()
    flat_program = flat_program.substitute_formulas().substitute_constants().simplify()
    return flat_program

class ActionIndex:
    def __init__(self, index):
        self.index = index

class CommandIndex:
    def __init__(self, index, command):
        self.index = index
        self.command = command

class SymbDistribution:
    def __init__(self, probs):
        self._probs = probs

    def __eq__(self, other):
        return [str(p) for p in self._probs] == [str(p) for p in other._probs]

    def __hash__(self):
        return hash(tuple([str(p) for p in self._probs]))

    def __len__(self):
        return len(self._probs)

    def __getitem__(self, item):
        return self._probs[item]


class DiceVariable:
    def __init__(self, name):
        self.name = name


def translate_prism(flat_program, props, step_bound, maxintval, prob0expressions, output_path, parameter_instantiations, has_overlapping_guards=True, track_goal = False, include_goal_in_step = False):
    expression_translator = stormpy.storage.DiceStringVisitor(maxintval)
    expr_manager = flat_program.expression_manager

    expression_variables_to_bounds = dict()
    for m in flat_program.modules:
        for integer in m.integer_variables:
            expression_variables_to_bounds[integer.expression_variable] = (integer.lower_bound_expression.evaluate_as_int(), integer.upper_bound_expression.evaluate_as_int())

    def create_symbolic_transitions():
        prob_parameters = dict()
        for c in flat_program.constants:
            if c.defined:
                continue
            if not c.type.is_rational:
                continue
            prob_parameters[c.name] = c.expression_variable

        prob_parameters_set = set(prob_parameters.values())

        symbolic_probabilities = {}
        for m in flat_program.modules:
            for cmd in m.commands:
                has_symbolic_transition = False
                for update in cmd.updates:
                    probvariables = update.probability_expression.get_variables()
                    if len(probvariables) == 0:
                        continue
                    if len(probvariables.intersection(prob_parameters_set)) == 0:
                        continue
                    if len(probvariables.difference(prob_parameters_set)) > 0:
                        raise NotImplementedError(
                            "We do not support probabilities that combine state variables and probability parameters")
                    has_symbolic_transition = True

                if has_symbolic_transition:
                    transitions = SymbDistribution([update.probability_expression for update in cmd.updates])
                    if transitions in symbolic_probabilities:
                        symbolic_probabilities[transitions].append(cmd.global_index)
                    else:
                        symbolic_probabilities[transitions] = [cmd.global_index]

            dice_declarations = []
            cmd_to_pardist = dict()
            cardinality = dict()
            for id, entry in enumerate(symbolic_probabilities.items()):
                probs, cmds = entry
                dice_declarations.append(f"//contains: discrete_sym(pardist{id}, {math.ceil(math.log2(len(probs)))}))")
                for cmd in cmds:
                    cmd_to_pardist[cmd] = f"pardist{id}"
                cardinality[f"pardist{id}"] = math.ceil(math.log2(len(probs)))

            if parameter_instantiations is None or len(parameter_instantiations) == 0:
                pass
            elif isinstance(parameter_instantiations, dict):
                for assignment in itertools.product(*parameter_instantiations.values()):
                    with open(output_path + "." + "-".join([f"{p}-{v:.3f}" for p,v in zip(parameter_instantiations.keys(), assignment)]) + ".eval", 'w') as file:
                        #print(assignment)
                        evaluation_dict = {prob_parameters[p]: expr_manager.create_rational(stormpy.Rational(v)) for p,v in zip(parameter_instantiations.keys(), assignment)}
                        comments = False
                        if comments:
                            file.write("\n".join([f"//{p}={v}" for p,v in zip(parameter_instantiations.keys(), assignment)]))
                            file.write("\n")
                        for id, probs in enumerate(symbolic_probabilities.keys()):
                            if len(probs) == 2:
                                file.write(f"pardist{id}\t" + str(float(probs[0].substitute(evaluation_dict).evaluate_as_rational())) + "\n")
                            else:
                                file.write(f"pardist{id}\t" + "\t".join([str(float(prob.substitute(evaluation_dict).evaluate_as_rational())) for prob in probs]) + "\n")
            elif isinstance(parameter_instantiations, list):

                for id, assignment in enumerate(parameter_instantiations):
                    indexname = "-".join([f"{p}-{v:.3f}" for p, v in assignment.items()])
                    if len(indexname) > 20:
                        indexname = str(id)
                    with open(output_path + "." + indexname + ".eval", 'w') as file:
                        print(assignment)
                        evaluation_dict = {prob_parameters[p]: expr_manager.create_rational(stormpy.Rational(v)) for p,v in assignment.items()}
                        comments = False
                        if comments:
                            file.write("\n".join([f"//{p}={v}" for p,v in assignment.items()]))
                            file.write("\n")
                        for id, probs in enumerate(symbolic_probabilities.keys()):
                            if len(probs) == 2:
                                file.write(f"pardist{id}\t" + str(float(probs[0].substitute(evaluation_dict).evaluate_as_rational())) + "\n")
                            else:
                                file.write(f"pardist{id}\t" + "\t".join([str(float(prob.substitute(evaluation_dict).evaluate_as_rational())) for prob in probs]) + "\n")


        return dice_declarations, cardinality, cmd_to_pardist

    def from_storm_to_dice_expr_string(expr):
        if isinstance(expr, stormpy.logic.Formula):
            # TODO this is volatile
            expr_string = str(expr)
            expr_string = re.sub("(\(|\s|/|^)(\d+)(\)|\s|/|$)", r"\1int({}, \2)\3".format(maxintval), expr_string)
            return expr_string.replace(" & ", " && ").replace(" = ", " == ").replace("\"", "").replace(" | ", " || ")
        return expression_translator.to_string(expr)

    def from_storm_update_to_dice_result_string(update, arguments, constants=dict()):
        assignments_dict = dict()
        for assignment in update.assignments:
            assignments_dict[assignment.variable] = assignment.expression.substitute(constants)
        results = []
        for var in arguments:
            if var in assignments_dict:
                results.append(from_storm_to_dice_expr_string(assignments_dict[var]))
            else:
                results.append(var.name)

        return pack(results)

    def split_values_and_add_updates( map, command, arguments, constants=dict(), indent=""):
        if len(map) > 0:
            key, bounds = map[0]
            map = map[1:]
            lower_bound, upper_bound = bounds
            dice_command_str = ""
            new_indent = indent + "\t"
            indent = indent + "\t"
            for i in range(lower_bound, upper_bound):
                constants[key] = expr_manager.create_integer(i)

                dice_command_str += f"{indent}if {key.name} == int({maxintval},{i}) then\n{split_values_and_add_updates(map, command, arguments, constants, new_indent)} \n{new_indent}else "
                indent = ""
            i = upper_bound
            constants[key] = expr_manager.create_integer(i)
            dice_command_str += f"\n{split_values_and_add_updates(map, command, arguments, constants, new_indent)} \n"
        else:
            simplified_guard = command.guard_expression.substitute(constants).simplify()
            if not simplified_guard.contains_variables():
                guard_val = simplified_guard.evaluate_as_bool()
                if not guard_val:
                    results = []
                    for var in step_arguments:
                        results.append(var.name)
                    return f"\t{indent}// Case should not be reachable\n\t{indent}{pack(results)}"

            dice_result_string_0 = from_storm_update_to_dice_result_string(command.updates[0], step_arguments, constants)
            dice_result_string_1 = from_storm_update_to_dice_result_string(command.updates[1], step_arguments, constants)
            prob = float(command.updates[0].probability_expression.substitute(constants).evaluate_as_rational())
            if prob < 0 or prob > 1:
                results = []
                for var in step_arguments:
                    results.append(var.name)
                dice_command_str = f"\t{indent}// Case should not be reachable\n\t{indent}{pack(results)}"
            elif prob == 0.0:
                dice_command_str = f"{indent}{dice_result_string_1}"
            elif prob == 1.0:
                dice_command_str = f"{indent}{dice_result_string_0}"
            else:
                dice_command_str = f"{indent}\tif flip {prob} then\n{indent}\t\t {dice_result_string_0}\n{indent}\telse\n{indent}\t\t {dice_result_string_1}\n"

        return dice_command_str

    if props[0].raw_formula.subformula.is_eventually_formula:
        goal_condition = from_storm_to_dice_expr_string(props[0].raw_formula.subformula.subformula)
    elif props[0].raw_formula.subformula.is_bounded_until_formula:
        goal_condition = from_storm_to_dice_expr_string(props[0].raw_formula.subformula.right_subformula)
    else:
        assert False

    with open(output_path, 'w') as file:
        def pack(args):
            assert len(args)>0
            if len(args) == 1:
                return args[0]
            if len(args) > 2:
                return f"( {args[0]}, {pack(args[1:])})"
            return f"({args[0]}, {args[1]})"

        def unpack_to_file(variable, variable_names, indent, suffix=""):
            currenttuple = variable
            if len(variable_names) == 1:
                file.write(f"{indent}let {str(variable_names[0].name)}{suffix} = {variable} in \n")
            else:
                for arg in variable_names[:-2]:
                    file.write(f"{indent}let {str(arg.name)}{suffix} = fst {currenttuple} in \n")
                    currenttuple = f"(snd {currenttuple})"
                file.write(f"{indent}let {str(variable_names[-2].name)}{suffix} = fst {currenttuple} in \n")
                file.write(f"{indent}let {str(variable_names[-1].name)}{suffix} = snd {currenttuple}  in \n")

        step_arguments = []
        step_argument_strings = []
        step_argument_types = []
        step_initial_values = []
        if maxintval > 0:
            file.write(f"fun min(a : int({maxintval}), b: int({maxintval}))")
            file.write("{\n")
            file.write("\tif a < b then a else b\n")
            file.write("}\n")
            file.write(f"fun max(a : int({maxintval}), b: int({maxintval}))")
            file.write("{\n")
            file.write("\tif a > b then a else b\n")
            file.write("}\n")


        decls, cardinality, cmd_to_symb = create_symbolic_transitions()

        file.write("\n".join(decls))
        file.write("\n")

        for m in flat_program.modules:
            for v in m.boolean_variables:
                step_arguments.append(v.expression_variable)
                step_argument_strings.append(f"{v.expression_variable.name} : bool")
                step_argument_types.append("bool")
                step_initial_values.append(f"{v.initial_value_expression}")
            for v in m.integer_variables:
                step_arguments.append(v.expression_variable)
                #TODO handle non-zero lower bounds
                step_argument_strings.append(f"{v.expression_variable.name} : int({v.upper_bound_expression})")
                step_argument_types.append(f"int({maxintval})")
                step_initial_values.append(f"int({maxintval},{v.initial_value_expression})")
        if track_goal:
            step_arguments.append(DiceVariable("__goal"))
            step_argument_types.append("bool")
            step_initial_values.append("false")

        results = []
        for var in step_arguments:
            results.append(var.name)

        if not include_goal_in_step:
            file.write("fun hit(packedstate : ")
            file.write(pack(step_argument_types))
            file.write(") {\n")
            currenttuple = "packedstate"
            for arg in step_arguments[:-2]:
                file.write(f"\tlet {str(arg.name)} = fst {currenttuple} in \n")
                currenttuple = f"(snd {currenttuple})"
            file.write(f"\tlet {str(step_arguments[-2].name)} = fst {currenttuple} in \n")
            file.write(f"\t let {str(step_arguments[-1].name)} = snd {currenttuple} in \n\n")
            for l in flat_program.labels:
                file.write(f"\tlet {l.name} = {from_storm_to_dice_expr_string(l.expression)} in\n")
            file.write(f"{goal_condition}\n")
            file.write("}\n")
        file.write("fun step(packedstate : ")

        file.write(pack(step_argument_types))
        file.write(") {\n")

        currenttuple = "packedstate"
        for arg in step_arguments[:-2]:
            file.write(f"\tlet {str(arg.name)} = fst {currenttuple} in \n")
            currenttuple = f"(snd {currenttuple})"
        file.write(f"\tlet {str(step_arguments[-2].name)} = fst {currenttuple} in \n")
        file.write(f"\t let {str(step_arguments[-1].name)} = snd {currenttuple} in \n\n")
        for l in flat_program.labels:
            file.write(f"\tlet {l.name} = {from_storm_to_dice_expr_string(l.expression)} in\n")

        if include_goal_in_step:
            if track_goal:
                file.write(f"let __goal = __goal || {goal_condition} in\n")
            else:
                file.write(f"\tif {goal_condition} then \n\t\t")
                file.write(pack(results))

                file.write("\n")
                file.write("\telse\n")

        else_str = " "
        if has_overlapping_guards:
            actions = dict()
            logger.info(f"Program has {len(flat_program.modules)}  modules.")
            if len(flat_program.modules) > 1:
                # We run this analysis as we currently do not want to support awkward weight-counting
                oga = stormpy.storage.OverlappingGuardAnalyser(flat_program, stormpy.utility.Z3SmtSolverFactory())
                if (oga.has_module_with_inner_action_overlapping_guard()):
                    raise RuntimeError("Modules with sync actions that have overlapping guards within a module are not supported")
                action_indices = flat_program.get_synchronizing_action_indices()
                for action_index in action_indices:
                    common_guard = expr_manager.create_boolean(True)
                    for module_indices in flat_program.get_module_indices_by_action_index(action_index):
                        module = flat_program.modules[module_indices]

                        module_guard = expr_manager.create_boolean(False)
                        for command_index in module.get_command_indices_by_action_index(action_index):
                            command = module.commands[command_index]
                            module_guard = stormpy.Expression.Or(module_guard, command.guard_expression)
                        common_guard = stormpy.Expression.And(common_guard, module_guard)
                    common_guard = common_guard.simplify()
                    dice_guard_string = from_storm_to_dice_expr_string(common_guard)
                    file.write(f"\t\tlet _cmd_act_{action_index} = {dice_guard_string} in\n")
                    actions[ActionIndex(action_index)] = f"_cmd_act_{action_index}"
                for module in flat_program.modules:
                    for command in module.commands:
                        if command.action_index == 0:
                            #This means it is not synchronizing
                            dice_guard_string = from_storm_to_dice_expr_string(command.guard_expression)
                            file.write(f"\t\tlet _cmd_{command.global_index} = {dice_guard_string} in\n")
                            actions[CommandIndex(command.global_index, command)] = f"_cmd_{command.global_index}"


            else:
                module = flat_program.modules[0]
                for index, command in enumerate(module.commands):
                    dice_guard_string = from_storm_to_dice_expr_string(command.guard_expression)
                    file.write(f"\t\tlet _cmd{index + 1} = {dice_guard_string} in\n")
                    actions[CommandIndex(index, command)] = f"_cmd{index + 1}"
            file.write("\t\tlet _count = \n")
            sumlist = []
            max_nr_parallel_actions = len(actions)
            countbitsize = math.ceil(math.log2(max_nr_parallel_actions+1))
            for action in actions.values():
                sumlist.append(f"\t\t\t(if {action} then int({countbitsize}, 1) else int({countbitsize}, 0))")
            file.write(" +\n ".join(sumlist))
            file.write(" in \n")
            file.write(f"\t\tif _count == int({countbitsize},0) then\n\t\t\t")

            file.write(pack(results))
            file.write("\n\t\telse\n")
            file.write("\t\t\tlet _sel_act =\n")
            file.write(f"\t\t\t\tif _count == int({countbitsize}, 1) then int({countbitsize}, 1) else ")
            for i in range(2,len(actions)):
                file.write(f"if _count == int({countbitsize}, {i}) then\n\t\t\t\t\t discrete(0.0, ")
                file.write(", ".join([str(1.0/i) for _ in range(i)] + ["0.0" for _ in range(len(actions) - i)]))
                file.write(f") + int({countbitsize}, 1)\n\t\t\t\telse ")
            file.write(f"\n\t\t\t\t\tdiscrete(0.0, ")
            file.write(", ".join([str(1.0 / len(actions)) for _ in range(len(actions))]))
            file.write(f")\n")
            file.write("\t\t\t\t\tin\n")
            file.write("\t\t\tlet _offset0 = _sel_act in \n")
            take_indices = dict()
            for index, action_id in enumerate(actions.keys()):
                action = actions[action_id]
                index = index + 1
                file.write(f"\t\t\tlet _take{index} = ((_offset{index-1} == int({countbitsize}, 1)) && {action}) in \n")
                if index < len(actions.values()):
                    file.write(f"\t\t\tlet _offset{index} = \n\t\t\t\tif ({action} && _offset{index-1} > int({countbitsize}, 0)) then \n\t\t\t\t\t_offset{index-1} - int({countbitsize},1) \n\t\t\t\telse\n\t\t\t\t\t_offset{index-1}\n\t\t\tin\n")
                take_indices[action_id] = index
            else_str = ""

        if len(flat_program.modules) == 1:
            module = flat_program.modules[0]
            for index, command in enumerate(module.commands):
                if not has_overlapping_guards:
                    dice_guard_string = from_storm_to_dice_expr_string(command.guard_expression)
                else:
                    dice_guard_string = f"_take{index + 1}"

                symb_distr = None
                if command.global_index in cmd_to_symb:
                    symb_distr = cmd_to_symb[command.global_index]
                if len(command.updates) == 1:
                    assert symb_distr is None
                    dice_result_string = from_storm_update_to_dice_result_string(command.updates[0], step_arguments)
                    dice_command_str = f"\t{else_str}if {dice_guard_string} then\n\t {dice_result_string}\n"
                    file.write(dice_command_str)
                elif symb_distr is None and len(command.updates) == 2:
                    vars = command.updates[0].probability_expression.get_variables()
                    if len(vars) == 0:
                        dice_result_string_0 = from_storm_update_to_dice_result_string(command.updates[0], step_arguments)
                        dice_result_string_1 = from_storm_update_to_dice_result_string(command.updates[1], step_arguments)
                        prob = float(command.updates[0].probability_expression.evaluate_as_rational())

                        dice_command_str = f"\t{else_str}if {dice_guard_string} then\n\t\tif flip {prob} then\n\t\t\t {dice_result_string_0}\n\t\telse\n\t\t\t {dice_result_string_1}\n"
                        file.write(dice_command_str)
                    else:
                        assert command.updates[1].probability_expression.get_variables() == vars
                        dice_result_str = split_values_and_add_updates([(key, expression_variables_to_bounds[key]) for key in vars], command, step_arguments)
                        dice_command_str = f"\t{else_str}if {dice_guard_string} then\n\t {dice_result_str}\n"
                        file.write(dice_command_str)
                else:
                    vars = command.updates[0].probability_expression.get_variables()
                    if symb_distr or len(vars) == 0:
                        file.write(f"\t{else_str}if {dice_guard_string} then\n\t\t")
                        if symb_distr is not None:
                            file.write(f"let _sel_update = discrete_sym({symb_distr}, {cardinality[symb_distr]}) \n\t\tin \n\t\t")
                        else:
                            probs = [str(float(u.probability_expression.evaluate_as_rational())) for u in command.updates]
                            file.write("let _sel_update = discrete(" + ", ".join(probs) + ") \n\t\tin \n\t\t")
                        sel_update_size = math.ceil(math.log2(len(command.updates)))
                        for i in range(len(command.updates)-1):
                            res_string = from_storm_update_to_dice_result_string(command.updates[i], step_arguments)
                            file.write(f"if _sel_update == int({sel_update_size}, {i}) then\n\t\t\t{res_string}\n\t\t else ")
                        res_string = from_storm_update_to_dice_result_string(command.updates[-1], step_arguments)
                        file.write(f"{res_string}\n")

                    else:
                        raise NotImplementedError("Combination of variable-dependent probabilties and n-ary updates not implemented")
                else_str = "else "
            file.write("\telse ")
            file.write(pack(results))
            file.write("\n}\n\n")
        else:
            for action_id, takeindex in take_indices.items():
                if isinstance(action_id, ActionIndex):
                    index = action_id.index
                    file.write(f"\t\t\t{else_str} if _take{takeindex} then\n")
                    updated = set()
                    for module_index in flat_program.get_module_indices_by_action_index(index):
                        updated_by_module = set()
                        for command_index in flat_program.modules[module_index].get_command_indices_by_action_index(index):
                            command = flat_program.modules[module_index].commands[command_index]
                            for update in command.updates:
                                for assignment in update.assignments:
                                    updated_by_module.add(assignment.variable)
                        if len(updated.intersection(updated_by_module)) > 0:
                            raise RuntimeError("Some variables are written to by multiple modules and we are unsure how to handle the situation.")
                        if len(updated_by_module) == 0:
                            continue
                        updated.update(updated_by_module)
                        file.write(f"\t\t\t\tlet _result_{module_index} =\n")
                        inner_else_str = ""
                        for command_index in flat_program.modules[module_index].get_command_indices_by_action_index(index):
                            command = flat_program.modules[module_index].commands[command_index]
                            file.write(f"\t\t\t\t\t{inner_else_str} if {from_storm_to_dice_expr_string(command.guard_expression)} then \n")
                            inner_else_str = "else"
                            command = flat_program.modules[module_index].commands[command_index]
                            updated_by_command = set()
                            for update in command.updates:
                                for assignment in update.assignments:
                                    updated_by_command.add(assignment.variable)
                            vars = command.updates[0].probability_expression.get_variables()
                            updated_by_command = list(updated_by_command)
                            symb_distr = None
                            if command.global_index in cmd_to_symb:
                                symb_distr = cmd_to_symb[command.global_index]
                            if symb_distr or len(vars) == 0:
                                sel_update_size = math.ceil(math.log2(len(command.updates)))
                                file.write(f"\t\t\t\t\t\tlet _sel_update_{module_index} = ")
                                if symb_distr is not None:
                                    file.write(f"discrete_sym({symb_distr}, {cardinality[symb_distr]})")
                                else:
                                    probs = [f"{float(u.probability_expression.evaluate_as_rational()):.9f}" for u in
                                             command.updates]

                                    file.write("discrete(" + ", ".join(probs) + ")")
                                file.write(" in \n\t\t\t\t\t\t\t")

                                for i in range(len(command.updates) - 1):
                                    update = command.updates[i]
                                    res = []
                                    for up in updated_by_module:
                                        found = False
                                        for a in update.assignments:
                                            if a.variable == up:
                                                res.append(from_storm_to_dice_expr_string(a.expression))
                                                found = True
                                        if not found:
                                            res.append(up.name)


                                    file.write(
                                        f"if _sel_update_{module_index} == int({sel_update_size}, {i}) then\n\t\t\t\t\t\t\t\t(")
                                    file.write(pack(res))
                                    file.write(")\n\t\t\t\t\t\t\telse\n")
                                update = command.updates[-1]
                                res = []
                                for up in updated_by_module:
                                    found = False
                                    for a in update.assignments:
                                        if a.variable == up:
                                            res.append(from_storm_to_dice_expr_string(a.expression))
                                            found = True
                                    if not found:
                                        res.append(up.name)
                                file.write("\t\t\t\t\t\t\t\t(")
                                file.write(pack(res))
                                file.write(")\n")

                            else:

                                assert(False)
                        file.write("\t\t\t\t\telse\n")
                        #file.write("\t\t\t\t\t\t//Not reachable.\n")
                        found = False
                        for up in updated_by_module:
                            res.append(up.name)
                        updated_by_module = list(updated_by_module)
                        file.write("\t\t\t\t\t\t")
                        file.write(pack([var.name for var in updated_by_module]))
                        file.write(f"\n\t\t\t\tin\n")
                        assert len(updated_by_module) > 0
                        unpack_to_file(f"_result_{module_index}", updated_by_module, "\t\t\t\t", suffix="_prime")



                    primed_vars = [x.name + ("_prime" if x in updated else "") for x in step_arguments]
                    file.write(f"\t\t\t\t{pack(primed_vars)}\n")
                    else_str = "else "
                else:
                    assert(isinstance(action_id, CommandIndex))
                    command = action_id.command
                    dice_guard_string = f"_take{takeindex}"

                    symb_distr = None
                    if command.global_index in cmd_to_symb:
                        symb_distr = cmd_to_symb[command.global_index]
                    if len(command.updates) == 1:
                        assert symb_distr is None
                        dice_result_string = from_storm_update_to_dice_result_string(command.updates[0], step_arguments)
                        dice_command_str = f"\t{else_str}if {dice_guard_string} then\n\t {dice_result_string}\n"
                        file.write(dice_command_str)
                    elif symb_distr is None and len(command.updates) == 2:
                        vars = command.updates[0].probability_expression.get_variables()
                        if len(vars) == 0:
                            dice_result_string_0 = from_storm_update_to_dice_result_string(command.updates[0],
                                                                                           step_arguments)
                            dice_result_string_1 = from_storm_update_to_dice_result_string(command.updates[1],
                                                                                           step_arguments)
                            prob = float(command.updates[0].probability_expression.evaluate_as_rational())

                            dice_command_str = f"\t{else_str}if {dice_guard_string} then\n\t\tif flip {prob} then\n\t\t\t {dice_result_string_0}\n\t\telse\n\t\t\t {dice_result_string_1}\n"
                            file.write(dice_command_str)
                        else:
                            assert command.updates[1].probability_expression.get_variables() == vars
                            dice_result_str = split_values_and_add_updates(
                                [(key, expression_variables_to_bounds[key]) for key in vars], command, step_arguments)
                            dice_command_str = f"\t{else_str}if {dice_guard_string} then\n\t {dice_result_str}\n"
                            file.write(dice_command_str)
                    else:
                        vars = command.updates[0].probability_expression.get_variables()
                        if symb_distr or len(vars) == 0:
                            file.write(f"\t{else_str}if {dice_guard_string} then\n\t\t")
                            if symb_distr is not None:
                                file.write(
                                    f"let _sel_update = discrete_sym({symb_distr}, {cardinality[symb_distr]}) \n\t\tin \n\t\t")
                            else:
                                probs = [str(float(u.probability_expression.evaluate_as_rational())) for u in
                                         command.updates]
                                file.write("let _sel_update = discrete(" + ", ".join(probs) + ") \n\t\tin \n\t\t")
                            sel_update_size = math.ceil(math.log2(len(command.updates)))
                            for i in range(len(command.updates) - 1):
                                res_string = from_storm_update_to_dice_result_string(command.updates[i], step_arguments)
                                file.write(
                                    f"if _sel_update == int({sel_update_size}, {i}) then\n\t\t\t{res_string}\n\t\t else ")
                            res_string = from_storm_update_to_dice_result_string(command.updates[-1], step_arguments)
                            file.write(f"{res_string}\n")

                        else:
                            raise NotImplementedError(
                                "Combination of variable-dependent probabilties and n-ary updates not implemented")
            file.write("\t\t\telse ")
            file.write(pack(results))
            file.write("\n}\n")

        initial_values_string = pack(step_initial_values)
        use_iterate = False
        if use_iterate:
            assert include_goal_in_step, "Step function must handle goal"
            file.write(f"let res = iterate(step, ({initial_values_string}), {step_bound}) in\n")
        else:
            if not include_goal_in_step:
                file.write(f"let _goal = false in \n")
            file.write(f"let res = {initial_values_string} in\n")

            for i in range(step_bound):
                if not include_goal_in_step:
                    file.write(f"let _goal = if !_goal then hit(res) else _goal in\n")
                    file.write(f"let res = if !_goal then step(res) else res in\n")
                else:
                    file.write(f"let res = step(res) in\n")

        if include_goal_in_step:
            currenttuple = "res"
            for arg in step_arguments[:-2]:
                file.write(f"\tlet {str(arg.name)} = fst {currenttuple} in \n")
                currenttuple = f"(snd {currenttuple})"
            file.write(f"\tlet {str(step_arguments[-2].name)} = fst {currenttuple} in \n")
            file.write(f"\tlet {str(step_arguments[-1].name)} = snd {currenttuple} in \n")
            for l in flat_program.labels:

                file.write(f"\tlet {l.name} = {from_storm_to_dice_expr_string(l.expression)} in\n")
            for line in prob0expressions[:-1]:
                file.write("let {} = {} in \n".format(line[0],from_storm_to_dice_expr_string(line[1])))
            goal_condition_str = goal_condition
            if track_goal:
                goal_condition_str = "__goal || " + goal_condition_str
            file.write("({}, {})".format(goal_condition_str,prob0expressions[-1]))
        else:
            file.write("(hit(res), {})".format(prob0expressions[-1]))

if __name__ == '__main__':
    translate_cli()
