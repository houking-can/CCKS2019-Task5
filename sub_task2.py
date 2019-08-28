import os
import re

from bs4 import BeautifulSoup

from ner.utils import get_entity


def get_paragraph(soup):
    ps = soup.find_all('sect') + soup.find_all('part')
    text = ''
    for each in ps:
        text += each.text + ' '
    ps = text.split('\n')
    tmp = ''
    for p in ps:
        text = re.sub('\s', '', p)
        tmp += text + ' '
        if "特此公告" in text:
            break
    tmp = re.split('。|！|\!|？|\?|;|；', tmp)
    sentences = []
    for sent in tmp:
        sent = re.sub('\s', '', sent)
        if sent != '':
            sentences.append(sent)
    return sentences


def fire_format(name, sex, title, reason):
    return {
        "离职高管姓名": name,
        "离职高管性别": sex,
        "离职高管职务": title,
        "离职原因": reason,
        "继任者姓名": None,
        "继任者性别": None,
        "继任者职务": None
    }


def hire_format(name, sex, title):
    return {
        "离职高管姓名": None,
        "离职高管性别": None,
        "离职高管职务": None,
        "离职原因": None,
        "继任者姓名": name,
        "继任者性别": sex,
        "继任者职务": title
    }


def get_fire(sent, PER, TIT, REA):
    name = ''
    sex = ''
    title = ''
    reason = ''
    events = []
    if len(REA) == 0 and len(PER) == 0:
        return None
    if len(REA) == 0:
        rea = re.findall('(因|由于)(.*)(原因|，|。|！|？|\!|\?|；|;|（|$)')
        if len(rea) > 0:
            reason = rea[0][1]
    if len(REA) > 0:
        reason = REA[0]
    flag = ''
    for f in ["申请辞去", "辞去", "不在担任", "不再担任"]:
        index = sent.find(f)
        min_i = -1
        max_i = len(sent)
        if index > 0:
            flag = f
            # 确定最近的那个人名和性别
            for p in PER:
                p_i = sent[:index].find(p)
                if p_i > min_i:
                    min_i = p_i
                    name = p
            if min_i != -1:
                if "先生" in sent[min_i:min_i + len(name) + 4]:
                    sex = "先生"
                elif "女士" in sent[min_i:min_i + len(name) + 4]:
                    sex = "女士"

            # 确定最近的职位
            for t in TIT:
                t_i = sent[index:].find(t)
                if t_i + index < max_i:
                    max_i = index + t_i
            if max_i != len(sent):
                tmp = re.findall('(%s.*?)(的职务|的职位|等职|职务|等职务|等职位|职位|一职|，|。|！|？|\!|\?|；|;|（|$)' % title, sent[max_i:])
                if len(tmp) > 0:
                    title = tmp[0][0]
            break

    if title == '' and flag != '':
        tmp = re.findall('%s(.*?)(的职务|的职位|等职|职务|等职务|等职位|职位|一职|，|。|！|？|\!|\?|；|;|（|$)' % flag, sent)
        if len(tmp) > 0:
            title = tmp[0][0]
    if title.startswith('公司'):
        title = title[2:]
    elif title.startswith('本公司'):
        title = title[3:]

    if reason.endswith('等原因'):
        reason = reason[:-3]
    if reason == '' and ("任何" in title or "其他" in title or "一切" in title):
        return None

    tmp_per = set(PER)
    events.append(fire_format(name, sex, title, reason))
    if len(tmp_per) > 1:
        if name != '':
            tmp_per.remove(name)
        for p in tmp_per:
            index = sent.find(p)
            if "先生" in sent[index:index + len(p) + 4]:
                sex = "先生"
            elif "女士" in sent[index:index + len(p) + 4]:
                sex = "女士"
            events.append(fire_format(p, sex, title, reason))

    return events


def get_hire(sent, PER, TIT):
    events = []
    tmp = re.findall('(聘任|提名|选举|增补)(.*)(为|担任|出任)', sent)
    info = tmp[0][1]
    tmp_per = []
    tmp_sex = []
    for p in PER:
        if p in info and p not in tmp_per:
            tmp_per.append(p)
            index = info.find(p)
            if "先生" in info[index:index + len(p) + 4]:
                tmp_sex.append("先生")
            elif "女士" in info[index:index + len(p) + 4]:
                tmp_sex.append("女士")
    index = sent.find(info)
    for t in TIT:
        if len(TIT) == len(tmp_per):
            for i in range(len(TIT)):
                tmp = re.findall(
                    '%s.*?(为|担任|出任).*?(%s.*?)(的职务|的职位|等职|职务|等职务|等职位|职位|一职|，|。|！|？|\!|\?|；|;|（|$)' % (tmp_per[i], t),
                    sent[index:])
                if len(tmp) > 0:
                    events.append(hire_format(tmp_per[i], tmp_sex[i], tmp[0][1]))

    if events == []:
        return None
    return events


def extract_event(file, model, sess):
    res = dict()
    name = os.path.basename(file)
    name, _ = os.path.splitext(name)
    index = [i.start() for i in re.finditer('-', name)]
    code = name[:index[0]]
    company = name[index[0] + 1:index[1]]
    res[name] = dict()
    res[name]['证券代码'] = code
    res[name]['证券简称'] = company
    res[name]['人事变动'] = []
    print(name)
    resignation = []
    appointment = []
    soup = BeautifulSoup(open(file, encoding='utf-8'), "lxml")
    sentences = get_paragraph(soup)
    for i, sent in enumerate(sentences):
        try:
            if len(re.findall('(因|由于).*?(申请辞去|辞去|不在担任|不再担任)', sent)) > 0:
                words = list(sent)
                data = [(words, ['O'] * len(words))]
                tag = model.demo_one(sess, data)
                PER, TIT, REA = get_entity(tag, words)
                events = get_fire(sent, PER, TIT, REA)
                if events:
                    resignation.extend(events)

            if len(re.findall('(聘任|提名|选举|增补).*(为|担任|出任)', sentences[i])) > 0:
                words = list(sent)
                data = [(words, ['O'] * len(words))]
                tag = model.demo_one(sess, data)
                PER, TIT, _ = get_entity(tag, words)
                events = get_hire(sent, PER, TIT)
                if events:
                    appointment.extend(events)
        except Exception as e:
            print(file, 'task2', e)
            continue

    tmp = [0 for _ in range(len(appointment))]
    for r in resignation:
        flag = True
        for i, a in enumerate(appointment):
            if tmp[i] == 0 and r["离职高管职务"] == a["继任者职务"]:
                r["继任者姓名"] = a["继任者姓名"]
                r["继任者性别"] = a["继任者性别"]
                r["继任者职务"] = a["继任者职务"]
                res[name]['人事变动'].append(r)
                flag = False
                tmp[i] = 1
                break
        if flag:
            res[name]['人事变动'].append(r)
    for i in range(len(tmp)):
        if tmp[i] == 0:
            res[name]['人事变动'].append(appointment[i])

    return res
