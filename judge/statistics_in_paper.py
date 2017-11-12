# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import bisect
import codecs
import json
import matplotlib.pyplot as plt
import os
import plot_tools
import settings
import six

from collections import defaultdict
from pythonapi import anno_tools
from six.moves import urllib


def main():
    most_freq = defaultdict(lambda: {'trainval': 0, 'test': 0})
    num_char = defaultdict(lambda: {'trainval': 0, 'test': 0})
    num_uniq_char = defaultdict(lambda: {'trainval': 0, 'test': 0})
    num_image = {'trainval': 0, 'test': 0}
    sum_chinese = {'trainval': 0, 'test': 0}
    sum_not_chinese = {'trainval': 0, 'test': 0}
    sum_ignore = {'trainval': 0, 'test': 0}
    longsizes = {'trainval': list(), 'test': list()}
    props = {'trainval': {prop: 0 for prop in settings.PROPERTIES}, 'test': {prop: 0 for prop in settings.PROPERTIES}}
    with open(settings.TRAIN) as f, open(settings.VAL) as f2:
        for line in f.read().splitlines() + f2.read().splitlines():
            anno = json.loads(line.strip())
            num = 0
            uniq = set()
            for char in anno_tools.each_char(anno):
                if char['is_chinese']:
                    most_freq[char['text']]['trainval'] += 1
                    num += 1
                    uniq.add(char['text'])
                    sum_chinese['trainval'] += 1
                    longsizes['trainval'].append(max(char['adjusted_bbox'][2], char['adjusted_bbox'][3]))
                    for prop in char['properties']:
                        props['trainval'][prop] += 1
                else:
                    sum_not_chinese['trainval'] += 1
            assert 0 < len(uniq)
            num_char[num]['trainval'] += 1
            num_uniq_char[len(uniq)]['trainval'] += 1
            num_image['trainval'] += 1
            sum_ignore['trainval'] += len(anno['ignore'])
    with open(settings.TEST_CLASSIFICATION_GT) as f:
        for line in f:
            gt = json.loads(line.strip())['ground_truth']
            num = 0
            uniq = set()
            for char in gt:
                most_freq[char['text']]['test'] += 1
                num += 1
                uniq.add(char['text'])
                sum_chinese['test'] += 1
                longsizes['test'].append(max(*char['size']))
                for prop in char['properties']:
                    props['test'][prop] += 1
            assert 0 < len(uniq)
            num_char[num]['test'] += 1
            num_uniq_char[num]['test'] += 1
            num_image['test'] += 1
    with open(settings.TEST_DETECTION_GT) as f:
        for line in f:
            anno = json.loads(line.strip())
            num = 0
            uniq = set()
            for char in anno_tools.each_char(anno):
                if char['is_chinese']:
                    most_freq[char['text']]['test'] += 1
                    num += 1
                    uniq.add(char['text'])
                    sum_chinese['test'] += 1
                    longsizes['test'].append(max(char['adjusted_bbox'][2], char['adjusted_bbox'][3]))
                    for prop in char['properties']:
                        props['test'][prop] += 1
                else:
                    sum_not_chinese['test'] += 1
            assert 0 < len(uniq)
            num_char[num]['test'] += 1
            num_uniq_char[len(uniq)]['test'] += 1
            num_image['test'] += 1
            sum_ignore['test'] += len(anno['ignore'])
    most_freq = [{
        'text': k,
        'trainval': v['trainval'],
        'test': v['test'],
    } for k, v in most_freq.items()]
    most_freq.sort(key=lambda o: (-o['trainval'] - o['test'], o['text']))
    print('50_most_frequent_characters')
    for i, o in enumerate(most_freq[:50]):
        print(i + 1, o['text'], o['trainval'], o['test'])
    print('total_number_of_characters_in_each_image')
    for i in range(1, 61):
        print(i, num_char[i]['trainval'], num_char[i]['test'])
    print('number_of_different_characters_per_image')
    for i in range(1, 61):
        print(i, num_uniq_char[i]['trainval'], num_uniq_char[i]['test'])
    print('over_all')
    print('uniq_chinese', len(most_freq))
    print('num_image', num_image['trainval'], num_image['test'])
    print('sum_chinese', sum_chinese['trainval'], sum_chinese['test'])
    print('sum_not_chinese', sum_not_chinese['trainval'], sum_not_chinese['test'])
    print('sum_ignore', sum_ignore['trainval'], sum_ignore['test'])

    if not os.path.isdir(settings.PLOTS_DIR):
        os.makedirs(settings.PLOTS_DIR)
    chinese_ttf = os.path.join(settings.PRODUCTS_ROOT, 'SimHei.ttf')
    if not os.path.isfile(chinese_ttf):
        urllib.request.urlretrieve('http://fonts.cooltext.com/Downloader.aspx?ID=11120',
                                   chinese_ttf)

    # most_freq
    meta = most_freq[:50]
    data = [
        [
            {
                'legend': 'training set',
                'data': [o['trainval'] for o in meta],
            }, {
                'legend': 'testing set',
                'data': [o['test'] for o in meta],
            },
        ],
    ]
    labels = [o['text'] for o in meta]
    with plt.style.context({
        'figure.subplot.left': .06,
        'figure.subplot.right': .96,
        'figure.subplot.top': .96,
    }):
        plt.figure(figsize=(10, 3))
        plt.xlim((0, len(labels) + 1))
        plt.grid(which='major', axis='y', linestyle='dotted')
        plot_tools.draw_bar(data, labels, xticks_font_fname=chinese_ttf)
        plt.savefig(os.path.join(settings.PLOTS_DIR, 'stat_most_freq.svg'))
        plt.close()

    # num_char
    meta = [num_char[i] for i in range(1, 61)]
    data = [
        [
            {
                'legend': 'training set',
                'data': [o['trainval'] for o in meta],
            }, {
                'legend': 'testing set',
                'data': [o['test'] for o in meta],
            },
        ],
    ]
    labels = [i + 1 if (i + 1) % 10 == 0 else None for i, _ in enumerate(meta)]
    with plt.style.context({
        'figure.subplot.left': .14,
        'figure.subplot.right': .96,
        'figure.subplot.bottom': .16,
        'figure.subplot.top': .96,
    }):
        plt.figure(figsize=(5, 3))
        plt.xlim((0, len(labels) + 1))
        plt.grid(which='major', axis='y', linestyle='dotted')
        plot_tools.draw_bar(data, labels)
        plt.xlabel('Total number of characters in each image')
        plt.ylabel('Number of images')
        plt.savefig(os.path.join(settings.PLOTS_DIR, 'stat_num_char.svg'))
        plt.close()

    # num_uniq_char
    meta = [num_uniq_char[i] for i in range(1, 61)]
    data = [
        [
            {
                'legend': 'training set',
                'data': [o['trainval'] for o in meta],
            }, {
                'legend': 'testing set',
                'data': [o['test'] for o in meta],
            },
        ],
    ]
    labels = [i + 1 if (i + 1) % 10 == 0 else None for i, _ in enumerate(meta)]
    with plt.style.context({
        'figure.subplot.left': .14,
        'figure.subplot.right': .96,
        'figure.subplot.bottom': .16,
        'figure.subplot.top': .96,
    }):
        plt.figure(figsize=(5, 3))
        plt.xlim((0, len(labels) + 1))
        plt.grid(which='major', axis='y', linestyle='dotted')
        plot_tools.draw_bar(data, labels)
        plt.xlabel('Number of different characters in each image')
        plt.ylabel('Number of images')
        plt.savefig(os.path.join(settings.PLOTS_DIR, 'stat_num_uniq_char.svg'))
        plt.close()

    # instance size
    longsizes['trainval'].sort()
    longsizes['test'].sort()
    ranges = list(range(0, 65, 4))
    data = [
        [
            {
                'legend': 'training set',
                'data': [bisect.bisect_left(longsizes['trainval'], hi) - bisect.bisect_left(longsizes['trainval'], lo) for lo, hi in zip(ranges, ranges[1:] + [float('inf')])],
            }, {
                'legend': 'testing set',
                'data': [bisect.bisect_left(longsizes['test'], hi) - bisect.bisect_left(longsizes['test'], lo) for lo, hi in zip(ranges, ranges[1:] + [float('inf')])],
            },
        ],
    ]
    labels = ['[{}, {})'.format(lo, hi) for lo, hi in zip(ranges, ranges[1:] + ['+∞'])]
    with plt.style.context({
        'figure.subplot.left': .14,
        'figure.subplot.right': .96,
        'figure.subplot.bottom': .21,
        'figure.subplot.top': .96,
    }):
        plt.figure(figsize=(5, 3))
        plt.xlim((0, len(labels) + 1))
        plt.grid(which='major', axis='y', linestyle='dotted')
        plot_tools.draw_bar(data, labels)
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.savefig(os.path.join(settings.PLOTS_DIR, 'stat_instance_size.svg'))
        plt.close()

    # properties percentage
    data = [
        [
            {
                'legend': 'training set',
                'data': [props['trainval'][prop] / sum_chinese['trainval'] * 100 for prop in settings.PROPERTIES],
            },
        ],
        [
            {
                'legend': 'testing set',
                'data': [props['test'][prop] / sum_chinese['test'] * 100 for prop in settings.PROPERTIES],
            },
        ],
    ]
    labels = settings.PROPERTIES
    with plt.style.context({
        'figure.subplot.left': .09,
        'figure.subplot.right': .96,
        'figure.subplot.bottom': .10,
        'figure.subplot.top': .96,
    }):
        plt.figure(figsize=(6, 3))
        plt.xlim((.3, .7 + len(labels)))
        plt.grid(which='major', axis='y', linestyle='dotted')
        plot_tools.draw_bar(data, labels)
        plt.ylabel('Percentage of characters (%)')
        plt.savefig(os.path.join(settings.PLOTS_DIR, 'stat_properties.svg'))
        plt.close()


if __name__ == '__main__':
    main()
