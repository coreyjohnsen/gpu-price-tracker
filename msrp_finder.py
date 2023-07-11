import requests
from bs4 import BeautifulSoup

def validate_title(name, target, ti):
    name = name.split()
    target = target.split()
    inTarget = 0
    for w1 in target:
        for w2 in name:
            if w1.lower() in w2.lower():
                inTarget += 1
    return inTarget >= len(target) and (bool(list(map(lambda w: 'ti' in w.lower() or 'xt' in w.lower(), name)).count(True)) == ti)

def get_msrp(gpu_str):

    ti = False
    for w in gpu_str.split():
        if 'ti' in w.lower() or 'xt' in w.lower():
            ti = True

    page = requests.get('https://www.tomshardware.com/news/gpu-pricing-index',headers={"User-Agent":"Defined"})
    soup = BeautifulSoup(page.content, 'html.parser')

    rows = list(soup.find_all('tr'))
    headers = list(soup.find_all('th'))

    gpu_col_index = list(map(lambda th: bool(th.find(string='GPU')), headers)).index(True)
    msrp_col_index = list(map(lambda th: bool(th.find(string='Retail Price')), headers)).index(True)

    clean_rows = []

    for row in rows:
        if len(row.find_all('td')) > 0 and validate_title(row.find_all('td')[gpu_col_index].text, gpu_str, ti):
            clean_rows.append(row)

    clean_rows.sort(key=lambda r: float(r.find_all("td")[msrp_col_index].text.replace(',', '')[1:]))

    try:
        return float(clean_rows[0].find_all("td")[msrp_col_index].text.replace(',', '')[1:])
    except:
        raise ValueError('GPU not found. Check inputs and try again.')
