import os
import re
import traceback

from bs4 import BeautifulSoup


def iter_files(path):
    """Walk through all files located under a root path."""
    if os.path.isfile(path):
        yield path
    elif os.path.isdir(path):
        for dir_path, _, file_names in os.walk(path):
            for f in file_names:
                yield os.path.join(dir_path, f)
    else:
        raise RuntimeError('Path %s is invalid' % path)


def format_row(columns):
    name = columns[0].replace('\n', '').strip()
    appendix = re.sub('\s', '', columns[1])
    num1 = columns[2].replace('\n', '').strip()
    num2 = columns[3].replace('\n', '').strip()

    if appendix == '-' or appendix == '—':
        appendix = ''

    if (name.endswith('：') or name.endswith(':')):
        if num1 in ['-', '', '—', '--'] and num2 in ['-', '', '—', '--']:
            num1 = None
            num2 = None
    else:
        if num1 in ['-', '', '—', '--']:
            num1 = '0.00'
        if num2 in ['-', '', '—', '--']:
            num2 = '0.00'
    return {"名称": name,
            "附注": appendix,
            "年初至报告期末": num1,
            "上年年初至报告期末": num2
            }


def find_unit(text):
    text = re.sub('\s', '', text)
    units = ["单位：元", "单位:元", "单位：美元", "单位:美元", "单位：港元", "单位:港元",
             "单位：欧元", "单位:欧元", "单位：日元", "单位:日元", "单位：英镑", "单位:英镑",
             "单位：加元", "单位:加元", "单位：澳元", "单位:澳元", "单位：卢布", "单位:卢布",
             "单位：韩元", "单位:韩元"]
    for unit in units:
        if unit in text:
            return unit[3:]
    return ''


def find_name(node):
    text_num = 3
    unit = ''
    names = ['母公司资产负债表', '合并资产负债表', '母公司利润表', '合并利润表', '母公司现金流量表', '合并现金流量表']
    for element in node.previous_elements:
        if text_num < 0:
            return None
        if isinstance(element, str):
            element = element.replace('\n', '')
            if element == '':
                continue
            if unit == '':
                unit = find_unit(element)
            for name in names:
                if name in element:
                    if "母公司" in name:
                        return unit, name[3:] + "（母公司）"
                    else:
                        return unit, name[2:] + "（合并）"
            if "利润表" in element:
                return unit, "利润表（合并）"
            if "流量表" in element:
                return unit, "流量表（合并）"
            text_num -= 1


def get_flags(name):
    if "负债表" in name:
        tails = ['负债和所有者权益']
    elif "利润表" in name:
        tails = ['稀释每股收益']
    else:
        tails = ['等价物余额', '期末现金']

    return tails


def check_name(table, index):
    tmp = ' '.join([each["名称"] for each in table])

    # 资产负债表（合并）
    cnt = 0
    flags = ['归属于母公司所有者权益合计', '少数股东权益']
    for flag in flags:
        if flag in tmp:
            cnt += 1
    if cnt >= 1:
        return "资产负债表（合并）"

    flags = ['固定资产', '应付债券', '短期借款', '应付职工薪酬', '资本公积', '递延所得税资产', '递延所得税负债', '应交税费', '盈余公积',
             '资产总计', '长期借款', '负债合计', '可供出售金融资产', '无形资产']
    cnt = 0
    for flag in flags:
        if flag in tmp:
            cnt += 1
    if cnt >= 3:
        return "资产负债表（母公司）"

    names = ['资产负债表（合并）', '资产负债表（母公司）', '利润表（合并）', '利润表（母公司）', '现金流量表（合并）', '现金流量表（母公司）']
    return names[index]


def extract(table, start=1):
    rows = table.find_all('tr')
    table = []
    for row in rows[start:]:
        columns = row.find_all('th') + row.find_all('td')
        columns = [each.text for each in columns]

        if len(columns) > 4:
            columns = columns[:4]
        elif len(columns) < 4:
            for _ in range(4 - len(columns)):
                columns.append('')
        table.append(format_row(columns))

    # 确定是合格的表格
    global names_str
    cnt = 0
    names = []
    for each in table:
        names.append(each['名称'])
        if each['名称'] in names_str:
            cnt += 1
    if cnt < int(0.8 * len(table)):
        table = []

    return table


def end(name, tails, head):
    for flag in tails:
        if flag not in name:
            if start(head):
                return True
            return False
    return True


def start(head):
    if head:
        title = re.sub('\s', '', head.text)
        if '项目附注' in title:
            info = find_name(head)
            if info:
                return info
    return None


def extract_table(file):
    global names_str
    names_str = open('names.txt', encoding='utf-8').read()
    try:
        res = dict()
        name = os.path.basename(file)
        name, _ = os.path.splitext(name)
        index = [i.start() for i in re.finditer('-', name)]
        code = name[:index[0]]
        company = name[index[0] + 1:index[1]]
        res[name] = dict()
        res[name]['证券代码'] = code
        res[name]['证券简称'] = company
        res[name]['现金流量表（母公司）'] = {'单位': '', '项目': []}
        res[name]['现金流量表（合并）'] = {'单位': '', '项目': []}
        res[name]['利润表（母公司）'] = {'单位': '', '项目': []}
        res[name]['利润表（合并）'] = {'单位': '', '项目': []}
        res[name]['资产负债表（母公司）'] = {'单位': '', '项目': []}
        res[name]['资产负债表（合并）'] = {'单位': '', '项目': []}

        soup = BeautifulSoup(open(file, encoding='utf-8'), "lxml")

        tables = soup.find_all('table')
        i = 0
        index = -1
        while i < len(tables):
            head = tables[i].tr
            info = start(head)

            if info:
                index += 1
                unit, table_name = info
                res[name][table_name]['单位'] = unit
                tails = get_flags(table_name)
                table = extract(tables[i], start=1)

                i += 1
                while i < len(tables):
                    if table != []:
                        attribute = table[-1]["名称"]
                        head = tables[i].tr
                        if end(attribute, tails, head):
                            res[name][table_name]['项目'] = table
                            break
                    tmp = extract(tables[i], start=0)
                    table.extend(tmp)
                    i += 1

                continue

            i += 1
        return res

    except Exception as e:
        print(file,'task1',e)
        return res
