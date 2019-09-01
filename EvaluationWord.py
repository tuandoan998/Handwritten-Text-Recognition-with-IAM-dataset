from Parameter import *
from Utils import *
from CRNN_Model import word_model
from ImageGenerator import TextImageGenerator
from sklearn.model_selection import train_test_split
import tensorflow as tf
from keras import backend as K
import editdistance
from Spell import correction

sess = tf.Session()
K.set_session(sess)

def F_score(p, r):
	return float(2*p*r)/(p+r)

if __name__=='__main__':
	paths_and_texts = get_paths_and_texts(is_words=True)
	print('number of image: ', len(paths_and_texts))

	paths_and_texts_train, paths_and_texts_test = train_test_split(paths_and_texts, test_size=0.4, random_state=1707)
	paths_and_texts_val, paths_and_texts_test = train_test_split(paths_and_texts_test, test_size=0.5, random_state=1707)
	print('number of train image: ', len(paths_and_texts_train))
	print('number of valid image: ', len(paths_and_texts_val))
	print('number of test image: ', len(paths_and_texts_test))

	model, _ = word_model()
	model.load_weights('Resource/iam_words--15--1.791.h5')

	test_set = TextImageGenerator(paths_and_texts_test, 128, 64, 8, 30, 16)
	test_set.build_data()

	net_inp = model.get_layer(name='the_input').input
	net_out = model.get_layer(name='softmax').output

	ed_chars = num_chars_gt = num_chars_pred = 0
	ed_words = num_words = 0
	batch = 0
	num_batch = int(test_set.n/32)
	for inp_value, _ in test_set.next_batch():
		if batch>num_batch:
			break
		print('batch: %s/%s' % (batch, str(num_batch)))
		batch = batch+1
		bs = inp_value['the_input'].shape[0]
		X_data = inp_value['the_input']
		net_out_value = sess.run(net_out, feed_dict={net_inp:X_data})
		pred_texts = decode_batch(net_out_value)

		labels = inp_value['the_labels']
		label_len = inp_value['label_length']
		gt_texts = []
		for label in labels:
			gt_text = ''.join(list(map(lambda x: letters[int(x)], label)))
			gt_texts.append(gt_text)

		for i in range(bs):
			gt_texts[i] = gt_texts[i][:int(inp_value['label_length'].item(i))]
			ed_chars += editdistance.eval(gt_texts[i], pred_texts[i])
			if gt_texts[i]!=pred_texts[i]:
				ed_words += 1
			num_chars_gt += len(gt_texts[i])
			num_chars_pred += len(pred_texts[i])
			num_words += 1
	
	num_chars_correct = num_chars_gt - ed_chars
	micro_ap = float(num_chars_correct)/num_chars_pred
	micro_ar = float(num_chars_correct)/num_chars_gt
	print('CER: ', ed_chars / num_chars_gt)
	print('WER: ', ed_words / num_words)
	print('Micro-average precision: ', micro_ap)
	print('Micro-average recall: ', micro_ar)
	print('F-score: ', F_score(micro_ap, micro_ar))