import argparse
import os

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request, make_response, abort

from converter import Converter
from ner.data import read_dictionary, tag2label, random_embedding
from ner.model import BiLSTM_CRF
from sub_task1 import extract_table
from sub_task2 import extract_event
from ner.utils import str2bool

config = tf.ConfigProto()
parser = argparse.ArgumentParser(description='BiLSTM-CRF for Chinese NER task')
parser.add_argument('--train_data', type=str, default='data_path', help='train data source')
parser.add_argument('--test_data', type=str, default='data_path', help='test data source')
parser.add_argument('--batch_size', type=int, default=64, help='#sample of each minibatch')
parser.add_argument('--epoch', type=int, default=10, help='#epoch of training')
parser.add_argument('--hidden_dim', type=int, default=300, help='#dim of hidden state')
parser.add_argument('--optimizer', type=str, default='Adam', help='Adam/Adadelta/Adagrad/RMSProp/Momentum/SGD')
parser.add_argument('--CRF', type=str2bool, default=True, help='use CRF at the top layer. if False, use Softmax')
parser.add_argument('--lr', type=float, default=0.001, help='learning rate')
parser.add_argument('--clip', type=float, default=5.0, help='gradient clipping')
parser.add_argument('--dropout', type=float, default=0.5, help='dropout keep_prob')
parser.add_argument('--update_embedding', type=str2bool, default=True, help='update embedding during training')
parser.add_argument('--pretrain_embedding', type=str, default='random',
                    help='use pretrained char embedding or init it randomly')
parser.add_argument('--embedding_dim', type=int, default=300, help='random init char embedding_dim')
parser.add_argument('--shuffle', type=str2bool, default=False, help='shuffle training data before each epoch')
parser.add_argument('--mode', type=str, default='demo', help='train/test/demo')
parser.add_argument('--demo_model', type=str, default='1563773712', help='model for test and demo')
args = parser.parse_args()

## get char embeddings
word2id = read_dictionary('./ner/word2id.pkl')
if args.pretrain_embedding == 'random':
    embeddings = random_embedding(word2id, args.embedding_dim)
else:
    embedding_path = './ner/embedding.npy'
    embeddings = np.array(np.load(embedding_path), dtype='float32')

## paths setting
paths = {}
paths['summary_path'] = './'
model_path = './ner/checkpoint'
paths['model_path'] = os.path.join(model_path, "model")
paths['result_path'] = './'
paths['log_path'] = './'

ckpt_file = tf.train.latest_checkpoint(model_path)
print(ckpt_file)
paths['model_path'] = ckpt_file
model = BiLSTM_CRF(args, embeddings, tag2label, word2id, paths, config=config)
model.build_graph()
saver = tf.train.Saver()
sess = tf.Session()
saver.restore(sess, ckpt_file)

app = Flask(__name__)

api_root = '/ccks_pdf/'
save_path = r'C:\Users\Houking\Desktop\web_api\test'
exe_path = r'C:\Users\Houking\Desktop\web_api\pdf2html.exe'


@app.route(api_root + 'annualreport/', methods=['POST'])
def annualreport():
    if not request.files:
        abort(404)
    file = request.files['file']
    pdf_path = os.path.join(save_path, file.filename)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    file.save(pdf_path)
    converter = Converter(input=pdf_path, exe=exe_path, output=save_path)
    xml_path = converter.convert()
    if xml_path:
        res = extract_table(xml_path)
        return jsonify(res)
    else:
        return jsonify('{}')


@app.route(api_root + 'hrreport/', methods=['POST'])
def hrreport():
    if not request.files:
        abort(404)
    file = request.files['file']
    pdf_path = os.path.join(save_path, file.filename)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    file.save(pdf_path)
    converter = Converter(input=pdf_path, exe=exe_path, output=save_path)
    xml_path = converter.convert()
    if xml_path:
        res = extract_event(xml_path, model, sess)
        return jsonify(res)
    else:
        return jsonify('{}')


# 404处理
@app.errorhandler(404)
def not_found(_):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port='80')
