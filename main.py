'''
AnimeManager v1.4 release
By fecwaqw
'''
import re
from time import sleep
from urllib.parse import *
from lxml import etree
import requests
import json
import webbrowser
from faker import Faker
import os
import urllib3
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait

max_thrand = 10


config = []
search_list = [[]] * 10
urllib3.disable_warnings()
header = {
    'User-Agent': Faker().user_agent()
}
welcome_content = '''
    _          _                __  __                                   
   / \   _ __ (_)_ __ ___   ___|  \/  | __ _ _ __   __ _  __ _  ___ _ __ 
  / _ \ | '_ \| | '_ ` _ \ / _ \ |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
 / ___ \| | | | | | | | | |  __/ |  | | (_| | | | | (_| | (_| |  __/ |   
/_/   \_\_| |_|_|_| |_| |_|\___|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|   
                                                         |___/           
'''
help_content = '''
添加番剧:
 add <番剧名称> (会帮你自动搜索,所以名称可以不用输入完整)
获取新番:
 hot
下载番剧:
 get <番剧序号>
列出番剧列表:
 list --- ls
用浏览器打开番剧页面:
 open <番剧序号> --- opn <番剧序号>
删除番剧:
 remove / delete <番剧序号>(多选) --- rm / del <番剧序号>(多选)
编辑番剧信息:
 edit <番剧序号> <name|url> <修改值> --- ed <番剧序号> <name|url> <修改值>
ffmpeg设置:
 ffmpegpath [<路径>] --- ffp [<路径>] (不输入路径则显示ffmpeg路径)
帮助:
 help --- ?
退出:
 exit / quit --- q

多选可用方法:
 1 2 3 多选
 1-3   选择范围
 A/a   全选
 可混用(除A/a) eg: 1-3 5 7
'''
exit_content = '''
Bye!
'''


class Download():
    def __init__(self, url, path, filename, max_thrand):
        m3u8_data = requests.get(url).text
        m3u8_data = m3u8_data.split('\n')
        if m3u8_data[-1] == '':
            m3u8_data.pop(-1)
        url_list = []
        for i in m3u8_data:
            if i[0] != '#':
                url_list.append(i)
        try:
            os.mkdir('temp')
        except:
            pass
        pbar = tqdm(total=len(url_list), initial=0, unit=' file',
                    unit_scale=True, desc=filename, unit_divisor=1)
        '''
        for i in range(len(url_list)):
            ts_filename = str(i + 1)
            if not os.path.exists(f'temp/{ts_filename}'):
                while True:
                    data = requests.get(url_list[i]).content
                    if len(data) != 0:
                        with open(f'temp/{ts_filename}', 'wb') as f:
                            f.write(self.ts_unpack(data))
                        break
            pbar.update(1)
        '''
        pool = ThreadPoolExecutor(max_workers=max_thrand)
        task = []
        for i in range(len(url_list)):
            ts_filename = str(i + 1)
            task.append(pool.submit(
                self.download, url_list[i], f'temp/{ts_filename}', pbar))
        wait(task, return_when=ALL_COMPLETED)
        pbar.close()
        with open('temp/temp.txt', 'w+') as f:
            for i in range(len(url_list)):
                ts_filename = str(i + 1)
                f.write(f'file {ts_filename}\n')
        ffmpeg_path = config['ffmpeg_path']
        os.system(
            f'{ffmpeg_path} -f concat -safe 0 -i temp/temp.txt -c copy "{Path(path) / filename}"')
        os.remove('temp/temp.txt')
        for i in range(len(url_list)):
            ts_filename = str(i + 1)
            os.remove(f'temp/{ts_filename}')

    def download(self, url, path, pbar):
        if not os.path.exists(path):
            try:
                data = requests.get(url)
                if not (200 <= data.status_code < 400):
                    print(f'{url}, status_code: {data.status_code}')
                    raise Exception('Bad request!')
                with open(path, 'wb') as f:
                    f.write(self.ts_unpack(data.content))
            except:
                self.download(url, path, pbar)
        pbar.update(1)

    def ts_unpack(self, data):  # 将ts文件头上的图片伪装去掉
        last_pos = 0
        for i in range(len(data)):
            if data[i] == 71:
                if i - last_pos == 188:
                    data = data[last_pos:]
                    break
                last_pos = i
        return data


def search(name):
    name = quote(name)
    page = requests.get(
        f'https://omofun.tv/vod/search.html?wd={name}')
    page = etree.HTML(page.text)
    search_xpath_result = page.xpath(
        '//div[@class="module-card-item module-item"]')
    search_result = []
    for i in search_xpath_result:
        anime_name = i.xpath(
            'div[@class="module-card-item-info"]/div[@class="module-card-item-title"]/a/strong/text()')[0]
        temp = i.xpath(
            'div[@class="module-card-item-info"]/div[@class="module-info-item"][1]/div[@class="module-info-item-content"]/text()')
        anime_year = temp[0]
        anime_kind = ''
        for j in range(1, len(temp)):
            anime_kind += temp[j]
        anime_status = i.xpath(
            'a[@class="module-card-item-poster"]/div[@class="module-item-cover"]/div[@class="module-item-note"]/text()')[0]
        anime_url = 'https://omofun.tv' + \
            i.xpath('a[@class="module-card-item-poster"]/@href')[0]
        search_result.append({'name': anime_name, 'year': anime_year,
                             'kind': anime_kind, 'status': anime_status, 'url': anime_url})
    return search_result


def hot():
    page = requests.get('https://omofun.tv/')
    page = etree.HTML(page.text)
    hot_xpath_result = page.xpath(
        '//div[@class="module-items module-poster-items-small scroll-content"]/a[@class="module-poster-item module-item"]')
    hot_result = []
    for i in hot_xpath_result:
        anime_name = i.xpath('@title')[0]
        anime_status = i.xpath(
            'div[@class="module-item-cover"]/div[@class="module-item-note"]/text()')[0]
        hot_result.append({'name': anime_name, 'status': anime_status})
    return hot_result


def get_download_url(url):
    def json_match(s, keyword):
        pattern = re.compile(f'"{keyword}":[\s]*".+?"')
        json_match_result = pattern.findall(s)[0]
        pattern = re.compile('".+?"')
        result = pattern.findall(json_match_result)[1]
        result = result[1:-1]
        return result
    m3u8_data = requests.get(url, headers=header)
    m3u8_data = etree.HTML(m3u8_data.text)
    m3u8_data = m3u8_data.xpath(
        '//div[@class="player-box-main"]/script/text()')[0]
    m3u8_from = json_match(m3u8_data, 'from')
    m3u8_id = json_match(m3u8_data, 'id')
    m3u8_url = json_match(m3u8_data, 'url')
    sleep(0.5)
    m3u8_data = f'https://omofun.tv/addons/dp/player/dp.php?from={m3u8_from}&id={m3u8_id}&url={m3u8_url}'
    for i in range(5):
        m3u8_data = requests.get(m3u8_data, headers=header)
        if not 200 <= m3u8_data.status_code < 400:
            print(f'网络错误,正在重试({i + 1}/5)')
        else:
            break
    m3u8_data = etree.HTML(m3u8_data.text)
    m3u8_data = m3u8_data.xpath('/html/body/script/text()')[0]
    m3u8_data = json_match(m3u8_data, 'url')
    return m3u8_data


def save_config(config):
    config['anime'] = sorted(config['anime'], key=lambda x: x['name'])
    json.dump(config, open('config.json', 'w+'))


def select_number_parse(lst, length):
    '''
    patten1: eg: 1 2 3
    patten2: eg: 1-3
    patten3: A/a
    '''
    ret = []
    if lst[0] == 'A' or lst[0] == 'a':
        return list(range(1, length + 1))
    for i in lst:
        result = re.compile('[0-9]+-[0-9]+').findall(i)
        if result != []:
            result = re.compile('[0-9]+').findall(i)
            ret.extend(list(range(int(result[0]), int(result[1]) + 1)))
            continue
        result = re.compile('[0-9]+').findall(i)
        if result != []:
            ret.append(int(result[0]))
    return list(set(ret))


if __name__ == '__main__':
    # begin init

    try:
        config = json.load(open('config.json', 'r'))
        if 'ffmpeg_path' not in config.keys():
            raise ValueError
    except:
        config = {'ffmpeg_path': input('请输入你的ffmpeg路径:'), 'anime': []}
        save_config(config)

    print(welcome_content)
    print('输入"help (?)"以获得帮助')

    # end init
    while True:
        command = input('>>> ').split()
        try:
            if command[0] == 'help' or command[0] == '?':
                print(help_content)
            elif command[0] == 'exit' or command[0] == 'quit' or command[0] == 'q':
                break
            elif command[0] == 'add':
                anime_name = ''
                for i in range(1, len(command)):
                    anime_name += f'{command[i]} '
                anime_name = anime_name[:-1]
                search_result = search(anime_name)
                for i in range(len(search_result)):
                    anime_name = search_result[i]['name']
                    anime_year = search_result[i]['year']
                    anime_kind = search_result[i]['kind']
                    anime_status = search_result[i]['status']
                    print(
                        f'{i + 1}.{anime_name} {anime_year} {anime_kind} {anime_status}')
                select_anime = input(
                    '请输入选择的序号(没有需要的番剧则直接回车):')
                if select_anime == '':
                    name = input('请输入番剧全名(若输入本是全名则直接回车):')
                    if name != '':
                        anime_name = name
                    anime_url = input('请输入番剧网址:')
                    config['anime'].append(
                        {'name': anime_name, 'url': anime_url})
                else:
                    select_anime = select_anime.split()
                    select_anime = select_number_parse(
                        select_anime, len(search_result))
                    if len(select_anime) > len(search_result):
                        raise IndexError
                    for i in select_anime:
                        i = int(i) - 1
                        anime_name = search_result[i]['name']
                        anime_url = search_result[i]['url']
                        config['anime'].append(
                            {'name': anime_name, 'url': anime_url})
                save_config(config)
            elif command[0] == 'hot':
                hot_result = hot()
                for i in hot_result:
                    anime_name = i['name']
                    anime_status = i['status']
                    print(f'{anime_name} {anime_status}')
            elif command[0] == 'get':
                anime_name = config['anime'][int(
                    command[1]) - 1]['name']
                anime_url = config['anime'][int(command[1]) - 1]['url']
                r = requests.get(anime_url)
                html = etree.HTML(r.text)
                player_name_list = html.xpath(
                    '//div[@class="module-tab-items-box hisSwiper"]/div/span/text()')
                if len(player_name_list) > 1:
                    for i in range(len(player_name_list)):
                        print(f'{i + 1}.{player_name_list[i]}')
                    player_select = int(input('选择要使用的播放源:')) - 1
                else:
                    player_select = 0
                episode_name_list = html.xpath(
                    '//div[@class="module-play-list-content module-play-list-base"]')[player_select].xpath('a[@class="module-play-list-link"]/span/text()')
                episode_url_list = html.xpath(
                    '//div[@class="module-play-list-content module-play-list-base"]')[player_select].xpath('a[@class="module-play-list-link"]/@href')
                for i in range(len(episode_name_list)):
                    print(f'{i + 1}.{episode_name_list[i]}')
                episode_select = input('选择要下载的集(A / a为全选,用空格隔开):')
                if (episode_select == 'A' or episode_select == 'a'):
                    episode_select = range(1, len(episode_name_list) + 1)
                else:
                    episode_select = episode_select.split()
                try:
                    os.mkdir(anime_name)
                except:
                    pass
                for i in episode_select:
                    url = get_download_url(
                        'https://omofun.tv' + episode_url_list[int(i) - 1])
                    url = url.replace('///', '/')
                    url = url.replace('\\', '')
                    if (url == ''):
                        print('没有资源!')
                    else:
                        Download(url, anime_name,
                                 episode_name_list[int(i) - 1] + '.mp4', max_thrand)
            elif command[0] == 'list' or command[0] == 'ls':
                for i in range(len(config['anime'])):
                    anime_name = config['anime'][i]['name']
                    anime_url = config['anime'][i]['url']
                    print(
                        f'{i + 1}.{anime_name} {anime_url}')
            elif command[0] == 'remove' or command[0] == 'rm' or command[0] == 'delete' or command[0] == 'del':
                select_anime = select_number_parse(
                    command[1:], len(config['anime']))
                for i in select_anime:
                    config['anime'][i - 1]['url'] = False
                config['anime'] = [
                    x for x in config['anime'] if x['url'] != False]
                save_config(config)
            elif command[0] == 'open' or command[0] == 'opn':
                webbrowser.open_new_tab(
                    config['anime'][int(command[1]) - 1]['url'])
            elif command[0] == 'edit' or command[0] == 'ed':
                if command[2] == 'name':
                    config['anime'][int(
                        command[1]) - 1]['name'] = command[3]
                elif command[2] == 'url':
                    config['anime'][int(
                        command[1]) - 1]['url'] = command[3]
                save_config(config)
            elif command[0] == 'find' or command[0] == 'fnd':
                anime_name = ''
                for i in range(1, len(command)):
                    anime_name += f' command[i]'
                search_result = search(anime_name)
            elif command[0] == 'ffmpegpath' or command[0] == 'ffp':
                path = ''
                for i in range(1, len(command)):
                    path += command[i]
                if path == '':
                    print(config['ffmpeg_path'])
                else:
                    config['ffmpeg_path'] = path
                    save_config(config)
            else:
                raise NameError
        except:
            print('错误!')
    print(exit_content)
