searchscope = {'region':'USA','delay':'1','universe':'TOP3000','instrumentType':'EQUITY'}

def get_datafields(
        s,
        searchScope,
        dataset_id:str = '',
        search: str = ''
):
    import pandas as pd
    instrument_type = searchScope['instrumentType']
    region = searchScope['region']
    delay = searchScope['delay']
    universe = searchScope['universe']
    if len(search) == 0:
        url_template = 'https://api.worldquantbrain.com/data-fields?' +\
            f"instrumentType={instrument_type}&region={region}&delay={delay}&universe={universe}&dataset.id={dataset_id}&limit=50"+\
            "&offset={x}"
        count = s.get(url_template.format(x=0)).json()['count']
    else:
        url_template = 'https://api.worldquantbrain.com/data-fields/search?' +\
            f"instrumentType={instrument_type}"+\
            f"&region={region}&delay={str(delay)}&universe={universe}&dataset.id={dataset_id}&limit=50"+\
            f"&search={search}"+\
            "&offset={x}"
        count = 100

    datafields_list = []
    for x in range(0, count, 50):
        datafields = s.get(url_template.format(x=x))
        datafields_list.append(datafields.json()['results'])
    datafields_list_flat = [item for sublist in datafields_list for item in sublist]
    datafields_df = pd.DataFrame(datafields_list_flat)
    return datafields_df