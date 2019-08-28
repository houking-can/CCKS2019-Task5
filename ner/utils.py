import logging, sys, argparse


def str2bool(v):
    # copy from StackOverflow
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def get_entity(tag_seq, char_seq):
    PER = get_PER_entity(tag_seq, char_seq)
    TIT = get_TIT_entity(tag_seq, char_seq)
    # SEX = get_SEX_entity(tag_seq, char_seq)
    REA = get_REA_entity(tag_seq, char_seq)
    return PER, TIT, REA


def get_PER_entity(tag_seq, char_seq):
    length = len(char_seq)
    PER = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-PER':
            if 'per' in locals().keys():
                PER.append(per)
                del per
            per = char
            if i + 1 == length:
                PER.append(per)
        if tag == 'I-PER':
            if 'per' in locals().keys():
                per += char
            else:
                per = char
            if i + 1 == length:
                PER.append(per)

        if tag not in ['I-PER', 'B-PER']:
            if 'per' in locals().keys():
                PER.append(per)
                del per
            continue
    return PER


def get_TIT_entity(tag_seq, char_seq):
    length = len(char_seq)
    TIT = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-TIT':
            if 'tit' in locals().keys():
                TIT.append(tit)
                del tit
            tit = char
            if i + 1 == length:
                TIT.append(tit)
        if tag == 'I-TIT':
            if 'tit' in locals().keys():
                tit += char
            else:
                tit = char

            if i + 1 == length:
                TIT.append(tit)

        if tag not in ['I-TIT', 'B-TIT']:
            if 'tit' in locals().keys():
                TIT.append(tit)
                del tit
            continue
    return TIT


def get_SEX_entity(tag_seq, char_seq):
    length = len(char_seq)
    SEX = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-SEX':
            if 'sex' in locals().keys():
                SEX.append(sex)
                del sex
            sex = char
            if i + 1 == length:
                SEX.append(sex)
        if tag == 'I-SEX':
            if 'sex' in locals().keys():
                sex += char
            else:
                sex = char
            if i + 1 == length:
                SEX.append(sex)

        if tag not in ['I-SEX', 'B-SEX']:
            if 'sex' in locals().keys():
                SEX.append(sex)
                del sex
            continue
    return SEX


def get_REA_entity(tag_seq, char_seq):
    length = len(char_seq)
    REA = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-REA':
            if 'rea' in locals().keys():
                REA.append(rea)
                del rea
            rea = char
            if i + 1 == length:
                REA.append(rea)
        if tag == 'I-REA':
            if 'rea' in locals().keys():
                rea += char
            else:
                rea = char
            if i + 1 == length:
                REA.append(rea)
        if tag not in ['I-REA', 'B-REA']:
            if 'rea' in locals().keys():
                REA.append(rea)
                del rea
            continue
    return REA


def get_logger(filename):
    logger = logging.getLogger('logger')
    return logger
