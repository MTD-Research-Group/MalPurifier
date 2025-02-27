from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path as path
import argparse
import time

from core.defense import Dataset
from core.defense import MalwareDetectionDT
from tools.utils import save_args, get_group_args, dump_pickle

cmd_md = argparse.ArgumentParser(description='Arguments for malware detection using decision trees')

feature_argparse = cmd_md.add_argument_group(title='feature')
feature_argparse.add_argument('--proc_number', type=int, default=2,
                              help='Number of threads for feature extraction')
feature_argparse.add_argument('--number_of_smali_files', type=int, default=1000000,
                              help='Maximum number of smali files to represent each app')
feature_argparse.add_argument('--max_vocab_size', type=int, default=10000,
                              help='Maximum vocabulary size')
feature_argparse.add_argument('--update', action='store_true',
                              help='Update existing features')

detector_argparse = cmd_md.add_argument_group(title='detector')
detector_argparse.add_argument('--seed', type=int, default=0, help='Random state for reproducibility')
detector_argparse.add_argument('--max_depth', type=int, default=None, help='Maximum depth of the tree')
detector_argparse.add_argument('--batch_size', type=int, default=128, help='Mini-batch size')

dataset_argparse = cmd_md.add_argument_group(title='data_producer')
detector_argparse.add_argument('--cache', action='store_true', default=False,
                               help='Use cached data')

mode_argparse = cmd_md.add_argument_group(title='mode')
mode_argparse.add_argument('--mode', type=str, default='train', choices=['train', 'test'],
                           help='Train a model or test it')
mode_argparse.add_argument('--model_name', type=str, default='xxxxxxxx-xxxxxx',
                           help='Suffix date of a tested model name')

def _main():
    args = cmd_md.parse_args()
    dataset = Dataset(feature_ext_args=get_group_args(args, cmd_md, 'feature'))
    train_dataset_producer = dataset.get_input_producer(*dataset.train_dataset, batch_size=args.batch_size, name='train', use_cache=args.cache)
    val_dataset_producer = dataset.get_input_producer(*dataset.validation_dataset, batch_size=args.batch_size, name='val')
    test_dataset_producer = dataset.get_input_producer(*dataset.test_dataset, batch_size=args.batch_size, name='test')
    assert dataset.n_classes == 2

    model_name = args.model_name if args.mode == 'test' else time.strftime("%Y%m%d-%H%M%S")
    
    model = MalwareDetectionDT(max_depth=args.max_depth,
                               random_state=args.seed,
                               name=model_name)

    if args.mode == 'train':
        model.fit(train_dataset_producer, val_dataset_producer)
        save_args(path.join(path.dirname(model.model_save_path), "hparam"), vars(args))
        dump_pickle(vars(args), path.join(path.dirname(model.model_save_path), "hparam.pkl"))

    model.load()
    model.predict(test_dataset_producer)

if __name__ == '__main__':
    _main()
