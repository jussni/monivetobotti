def modify_arg(arg):
    if 'x' in arg:
        return '[0,999],[0,999]'
    if '-' not in arg:
        return arg
    modified_arg = ''
    for team in arg.split(','):
        modified_arg += '[' + team.replace("-", ",") + ']' + ','
    return modified_arg


def check_results(wagers_probs_evs_wins, *args):
    """
    arg: match1 ([0,3], 0), ...
    """
    match_count = 0
    print_output = ""
    _args = []
    for arg in args:
        _arg = []
        for match in arg:
            if isinstance(match, int):
                _arg.append([match, match])
            else:
                if len(match) == 1:
                    _arg.append([match[0], match[0]])
                else:
                    _arg.append(match)
        _args.append(tuple(_arg))
    args = tuple(_args)
    valid_scores = {}
    goal_ranges = [(range(arg[0][0], arg[0][1] + 1),
                    range(arg[1][0], arg[1][1] + 1)) for arg in args]
    for multiscore, pew in wagers_probs_evs_wins.items():
        in_range = True
        for i, score in enumerate(multiscore):
            in_range = (score[0] in goal_ranges[i][0]) and (score[1] in goal_ranges[i][1])
            if not in_range:
                break
        if in_range:
            valid_scores[multiscore] = pew

    row_line = "-" * 14 * len(args) + '-' * 37 + (3 - len(args)) * '-'
    if len(args) > 3:
        row_line = row_line[:3 - len(args)]
    print_output += row_line + '\n'
    main_title = '|'
    row_width = 12
    for i, _ in enumerate(args):
        s = f'Game #{i + 1}'
        n_spaces = row_width - len(s)
        for space in range(n_spaces):
            if space % 2 == 0:
                s = s + ' '
            else:
                s = ' ' + s
        main_title += s + '|'
    for i in ['Prob (%)', 'EV', 'Win (€)']:
        s = f'{i}'
        n_spaces = row_width - len(s)
        for space in range(n_spaces):
            if space % 2 == 0:
                s = s + ' '
            else:
                s = ' ' + s
        main_title += s + '|'
    print_output += main_title + '\n'

    row_line_with_plus = [symbol if i % (len(s) + 1) != 0 else '+' for i,
                          symbol in enumerate(list(row_line))]
    print_output += ''.join(row_line_with_plus) + '\n'
    for multiscore, (prob, ev, win) in valid_scores.items():
        score_line = '|'
        for score in multiscore:
            s = f'{score[0]} - {score[1]}'
            n_spaces = row_width - len(s)
            for space in range(n_spaces):
                if space % 2 == 0:
                    s = s + ' '
                else:
                    s = ' ' + s
            score_line += s + "|"
        for i, element in enumerate((prob, ev, win)):
            if i == 0:  # Prob
                s = f'{100 * element:.6f}'
                match_count += 1
            elif i == 1:  # EV
                s = f'{element:.2f}'
            else:
                s = f'{element:.0f}'
            n_spaces = row_width - len(s)
            for space in range(n_spaces):
                if space % 2 == 0:
                    s = s + ' '
                else:
                    s = ' ' + s
            score_line += s + "|"

        print_output += score_line + '\n'
    print_output += row_line

    return print_output, match_count
