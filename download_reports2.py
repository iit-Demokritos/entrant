import requests

with open('./excel_urls_list.csv') as fp:
    lines = fp.readlines()
    for line in lines:
        url = line.split(';')[-1]
        url = url.replace('\n', '')
        if 'http' in url:
            myfile = requests.get(url, allow_redirects=True)
            filename = url.split('/')[-2]
            open(f'./output/{filename}.xlsx', 'wb').write(myfile.content)


