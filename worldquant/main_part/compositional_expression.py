def create_alpha_list(alpha_expressions):
    alpha_list = []
    for alpha_expression in alpha_expressions:
        # print('正在將alpha表达式与setting封装')
        # print(alpha_expression)
        simulation_data = {
        'type': 'REGULAR',
        'settings' :{
            'instrumentType':'EQUITY',
            'region':'USA',
            'universe': 'TOP3000',
            'delay' : 1,
            'decay' : 0,
            'neutralization' : 'SUBINDUSTRY',
            'truncation':  0.01,
            'pasteurization': 'ON',
            'unitHandling' : 'VERIFY',
            'nanHandling' : 'ON',
            'language' : 'FASTEXPR',
            'visualization': False,
            },
        'regular':alpha_expression
        }
        alpha_list.append(simulation_data)
    return alpha_list