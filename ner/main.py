import tensorflow as tf
import numpy as np
import os, argparse, time, random
from model import BiLSTM_CRF
from utils import str2bool, get_logger, get_entity
from data import read_corpus, read_dictionary, tag2label, random_embedding


# ## Session configuration
# os.environ['CUDA_VISIBLE_DEVICES'] = '0'
# # os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # default: 0

# config.gpu_options.allow_growth = True
# config.gpu_options.per_process_gpu_memory_fraction = 0.2  # need ~700MB GPU memory
#
def ner(sent):
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
    parser.add_argument('--pretrain_embedding', type=str, default='random', help='use pretrained char embedding or init it randomly')
    parser.add_argument('--embedding_dim', type=int, default=300, help='random init char embedding_dim')
    parser.add_argument('--shuffle', type=str2bool, default=False, help='shuffle training data before each epoch')
    parser.add_argument('--mode', type=str, default='demo', help='train/test/demo')
    parser.add_argument('--demo_model', type=str, default='1563773712', help='model for test and demo')
    args = parser.parse_args()


    ## get char embeddings
    word2id = read_dictionary(os.path.join('.', args.train_data, 'word2id.pkl'))
    if args.pretrain_embedding == 'random':
        embeddings = random_embedding(word2id, args.embedding_dim)
    else:
        embedding_path = 'pretrain_embedding.npy'
        embeddings = np.array(np.load(embedding_path), dtype='float32')

    ## paths setting
    paths = {}
    paths['summary_path'] = './'
    model_path = r'C:\Users\Houking\Desktop\web_api\ner\checkpoint'
    paths['model_path'] = os.path.join(model_path, "model")
    paths['result_path'] = './'
    paths['log_path'] = './'

    ckpt_file = tf.train.latest_checkpoint(model_path)
    print(ckpt_file)
    paths['model_path'] = ckpt_file
    model = BiLSTM_CRF(args, embeddings, tag2label, word2id, paths, config=config)
    model.build_graph()
    saver = tf.train.Saver()
    with tf.Session() as sess:
        saver.restore(sess, ckpt_file)
        while(1):
            print('Please input your sentence:')
            demo_sent = input()
            if demo_sent == '' or demo_sent.isspace():
                print('See you next time!')
                break
            else:
                sent = list(sent)
                data = [(sent, ['O'] * len(sent))]
                tag = model.demo_one(sess, data)
                PER, SEX, TIT, REA = get_entity(tag, sent)
                print('PER: {}\nSEX: {}\nTIT: {}\nREA: {}'.format(PER, SEX, TIT, REA))
