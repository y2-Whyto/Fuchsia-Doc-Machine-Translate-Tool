import os
import sys
import getopt
from time import time
from googletrans import Translator  # googletrans-py, instead of googletrans


def process_trans(translated: str) -> str:
    translated = translated.replace('＃', '#')
    if translated.startswith('#'):
        i = 0
        while i < len(translated):
            if translated[i] == '#':
                i += 1
            else:
                if translated[i] != ' ':
                    translated = translated[:i] + ' ' + translated[i:]
                break
    return translated


def trans_write(ot_buf: str, tr_buf: str) -> None:
    if tr_buf[-1] == ' ':
        tr_buf = tr_buf[:-1]
    translation = translator.translate(tr_buf, src='en', dest='zh-cn')
    translated = translation.text
    if translated == '' and tr_buf != '':
        print('Translation Exception: Empty Result (Currently at Passage {})'.format(trans_cnt))
        print('Original text:')
        print(tr_buf)
    translated = process_trans(translated)
    ot_buf = '<!--\n' + ot_buf + ' -->\n'  # add comment mark
    ot_buf += translated  # append translated text
    if ot_buf[-1] != '\n':
        ot_buf += '\n'
    fo.write(ot_buf + '\n')  # write to fo
    print('Time elapsed: {:.2f} secs'.format(time() - t1))


if __name__ == '__main__':
    t0 = time()
    # Deal with arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], '-i:-o:-p:', ['input=', 'output=', 'proxy='])
    except getopt.GetoptError:
        print('Arguments Error (Unknown arguments)')
        exit(0)
    input_path = ''
    output_path = ''
    proxies = None
    for opt, arg in opts:
        if opt in ('-i', '--input'):
            input_path = os.path.expanduser(arg)
        elif opt in ('-o', '--output'):
            output_path = os.path.expanduser(arg)
        elif opt in ('-p', '--proxy'):
            proxies = {'http': arg, 'https': arg}
    if input_path == '':
        print('Argument -i Error')
        exit(0)
    if output_path == '':
        output_path = input_path + '.tmp'
    if proxies is None:
        print('Proxy unset. If there\'s empty translation, please check\n'
              'your connection to https://translate.google.com/')

    translator = Translator(service_urls=['translate.google.com', ], proxies=proxies)

    # Deal with files
    fi = open(input_path, 'r')
    fo = open(output_path, 'w')
    ot_buf = ''  # text to output
    tr_buf = ''  # to be translated
    code_area = False
    trans_cnt = 1
    code_cnt = 1
    t1 = time()
    for line in fi:
        if line.startswith('```'):
            if not code_area:
                code_area = True
                print('Skipping Code Block {}'.format(code_cnt), end=', ')
                code_cnt += 1
                t1 = time()
            else:
                ot_buf += line
                fo.write(ot_buf)
                ot_buf = ''
                code_area = False
                print('Time elapsed: {:.2f} secs'.format(time() - t1))
                continue
        if code_area:
            ot_buf += line
            continue
        if line == '\n':
            if ot_buf == '':
                fo.write('\n')
                continue
            trans_write(ot_buf, tr_buf)
            trans_cnt += 1
            ot_buf = ''
            tr_buf = ''
            continue
        if ot_buf == '':
            print('Translating Passage {}'.format(trans_cnt), end=', ')
            t1 = time()
        ot_buf += line
        # for beginning with special char, restore line break
        if tr_buf != '' and (not line[0].isalnum() and not line[0] in "'`\"") and (tr_buf[-1] == ' '):
            tr_buf = tr_buf[:-1] + '\n'
        tr_buf += line
        if tr_buf[-1] == '\n':
            tr_buf = tr_buf[:-1] + ' '
    if ot_buf != '':  # Deal with remaining text when exiting
        trans_write(ot_buf, tr_buf)
        trans_cnt += 1
        ot_buf = ''
        tr_buf = ''
    fi.close()
    fo.close()
    if output_path == input_path + '.tmp':
        os.remove(input_path)
        os.rename(output_path, input_path)
    print('Translation completed ({} passages, skipping {} code blocks)'.format(trans_cnt - 1, code_cnt - 1))
    print('Total time elapsed: {:.5f} secs'.format(time() - t0))
    print('CAUTIONS: Please check the format of the translated file (especially punctuations),')
    print('          and correct them manually if needed.')
