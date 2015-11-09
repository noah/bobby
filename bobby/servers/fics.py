from re import sub, split

PRELIMINARY_COMMANDS    = """\
set seek 0
set bell off
set style 12
iset nowrap 1
iset ms 1
iset gameinfo 1
set provshow 1
set interface 'BOBBY (http://github.com/noah/bobby)'\
""".split('\n')

def fen_from_style12(s):
    #
    fen = []
    for i in xrange(1, 9):
        fen.append(s['row{}'.format(i)])
    fen = '/'.join(fen)
    #
    foo = '9' # <- fen format known not to contain this char
    fen = fen.replace('-', foo)
    fen_split = split(r'\D', fen)
    for fs in fen_split:
        l = len(fs)
        if l > 0:
            fen = sub('9+', str(l), fen, count=1)
    return fen

def is_style12(s):
    return s[:4] == '<12>'

def is_g1(s):
    return s[:4] == '<g1>'

def parse_style12(s):
    # http://www.freechess.org/Help/HelpFiles/style12.html
    keys = "s12 row1 row2 row3 row4 row5 row6 row7 row8 turn_color\
        double_push_file white_castle_short white_castle_long\
        black_castle_short black_castle_long moves_since_irreversible\
        game_number white_name black_name my_relation initial_time_mins\
        increment_time_secs white_strength black_strength white_time_remain\
        black_time_remain next_move_number coordinate_notation\
        previous_move_time pretty_notation_previous flip_field"
    return dict(zip(keys.split(), s.split(' ')))

def parse_g1(s):
    # http://www.freechess.org/Help/HelpFiles/iv_gameinfo.html
    keys = "g1 game_number private type rated wb_registered\
        wb_initial_time wb_initial_increment partners_game_number\
        wb_rating wb_timeseal"
    g1_values = s.split(' ')
    for i in range(2, len(g1_values)):
        g1_values[i] = g1_values[i].split('=')[1]

    g1 = dict(zip(keys.split(), g1_values))

    # separate out g1 white/black tuples
    g1_with_combined = {}
    for k,v in g1.iteritems():
        if k[:2] == 'wb':
            w,b = v.split(',')
            _, key = k.split('wb_')
            g1_with_combined['white_{}'.format(key)] = w
            g1_with_combined['black_{}'.format(key)] = b
        else:
            g1_with_combined[k] = v

    return g1_with_combined

def s12_state(s12_line):
    # the cleaned-up board data object for the client to digest
    # defaults
    s12 = parse_style12(s12_line)
    s12.update({
        'orientation'   : 'white',
        'fen'           : fen_from_style12(s12),
    })
    if s12['flip_field'] == 1: s12['orientation'] = 'black'

    #
    return s12

def g1_state(g1_line):
    g1 = parse_g1(g1_line)
    if int(g1['rated']) == 1:
        g1['rated'] = 'rated'
    else:
        g1['unrated'] = 'unrated'
    return g1
