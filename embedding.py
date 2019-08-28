import os
import pickle
import numpy as np
# word2id = pickle.load(open(r'C:\Users\Houking\Desktop\web_api\ner\word2id.pkl', 'rb'))

lines = open(r'C:\Users\Houking\Desktop\sgns.financial.char', encoding='utf-8').readlines()[1:]
embeddings = []
# for word, id in word2id.items():
#     for each in lines:
#         tmp = each.split()
#         if len(tmp)>0 and tmp[0]==word:
#             embeddings.append(each.strip('\n'))
#             print(word)
#             break

# pre = open(r'C:\Users\Houking\Desktop\web_api\embedding.npy', encoding='utf-8').readlines()
# a=[]
# for each in pre:
#     each = each.split()
#     if len(each)>0:
#         a.append(a)
word = {}
e = [[0.0 for _ in range(300)]]
i = 1
word['<PAD>'] = 0

a=set()

x = 1
for line in lines:
    each = line.split()
    if len(each) > 0 and len(each[0]) == 1 and each[0] not in word:
        word[each[0]] = i
        x = each[0]
        a.add(x)
        print(each[0])
        i += 1
        each = each[1:]
        y = [float(mm) for mm in each]
        e.append(y)
word['<NUM>'] = i
tmp = np.random.uniform(-0.01, 0.01, (1, 300))
tmp = np.float32(tmp)
e.append([float(mm) for mm in list(tmp[0])])
i+=1
word['<ENG>'] = i
tmp = np.random.uniform(-0.01, 0.01, (1, 300))
tmp = np.float32(tmp)
e.append([float(mm) for mm in list(tmp[0])])
i+=1
word['<UNK>'] = i
print(word)
e.append([0.0 for _ in range(300)])

print(i)
print(len(e))
print(len(word.items()))
print(len(a))
pickle.dump(word, open('word2id.pkl', 'wb'))


np.save('embedding.npy', e)
# with open('embedding.npy','a+',encoding='utf-8') as f:
#     f.write(''.join(e))
