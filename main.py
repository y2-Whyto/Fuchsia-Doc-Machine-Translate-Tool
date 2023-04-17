import os
import sys
import getopt
from time import time
from googletrans import Translator  # !!googletrans-py, instead of googletrans!!


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


def is_note(line: str, pos: int, check_path=False) -> bool:
    if line[pos] == '[':
        while pos < len(line) and line[pos] != ']':
            pos += 1
        if pos + 2 < len(line) and line[pos:pos + 3] == ']: ':
            if check_path:
                if pos + 3 < len(line) and line[pos + 3] in ('/', '.', 'h'):
                    return True
                else:
                    return False
            return True
    return False


def is_new(line: str) -> bool:
    '''
    Check if a new line needs wrapping
    '''
    line_mark = '+-*>'
    line_break = False
    i = 0
    while i < len(line) and line[i] == ' ':
        i += 1
    # i -> non-space: if line[i] is a md-line-mark, omit; or restore the linebreak
    if i < len(line) and tr_buf != '' and tr_buf[-1] == ' ':

        # "#...# " needs a linebreak
        if line[i] == '#':
            while i < len(line) and line[i] == '#':
                i += 1
            if i < len(line) and line[i] == ' ':
                line_break = True

        # "1. ", "2. ", etc. need a linebreak too
        elif line[i].isdigit():
            while i < len(line) and line[i].isdigit():
                i += 1
            if i + 1 < len(line) and line[i:i + 2] == '. ':
                line_break = True

        # "[...]: " needs a linebreak too
        elif is_note(line, i):
            line_break = True

        # "- ", "* ", etc. need a linebreak too
        elif len(line) - i > 1:
            for ch in line_mark:
                if line[i:i + 2] == ch + ' ':
                    line_break = True
                    break
    return line_break


def buf_add(tr_buf: str, line: str) -> str:
    '''
    Add new line from file to buf, unwrapping the linebreaks if needed
    '''
    if is_new(line):
        tr_buf = tr_buf[:-1] + '\n'
    tr_buf += line
    # For every new line, change the ending from linebreak to space
    if tr_buf[-1] == '\n':
        tr_buf = tr_buf[:-1] + ' '

    return tr_buf


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
    ot_buf = ''  # output text
    tr_buf = ''  # text to translate
    code_area = False
    ref_area = False
    comment_area = False
    trans_cnt = 1
    code_cnt = 1
    ref_cnt = 1
    comment_cnt = 1
    t1 = time()

    for line in fi:

        # Close ref area if needed before latent wrong recognitions
        if comment_area:

            comment_end = line.find('-->')
            if comment_end != -1:
                comment_end += 3
                ot_buf += line[:comment_end]
                fo.write(ot_buf)
                comment_area = False
                print('Time elapsed: {:.2f} secs'.format(time() - t1))
                ot_buf = line[comment_end:]
                if ot_buf.isspace() or ot_buf == '':
                    fo.write('\n')
                    ot_buf = ''
                else:  # Replacing 'normal start'
                    tr_buf = buf_add(tr_buf, ot_buf)
                    print('Translating Passage {}'.format(trans_cnt), end=', ')
                    t1 = time()
                continue
            ot_buf += line
            continue

        # Close ref area if needed to avoid a code block RIGHT after a ref area
        if ref_area:
            if is_note(line, pos=0, check_path=True):
                fo.write(line)
                continue
            else:
                print('Time elapsed: {:.2f} secs'.format(time() - t1))
                ref_area = False

        # Deal with html comments
        if line.startswith('<!--'):
            if not comment_area:
                comment_area = True
                print('Skipping Comment {}'.format(comment_cnt), end=', ')
                comment_cnt += 1
                t1 = time()
                # try finding inline closing mark
                comment_end = line.find('-->')
                if comment_end != -1:
                    comment_end += 3
                    ot_buf += line[:comment_end]
                    fo.write(ot_buf)
                    comment_area = False
                    print('Time elapsed: {:.2f} secs'.format(time() - t1))
                    ot_buf = line[comment_end:]
                    if ot_buf.isspace() or ot_buf == '':
                        fo.write('\n')
                        ot_buf = ''
                    else:  # Replacing 'normal start'
                        tr_buf = buf_add(tr_buf, ot_buf)
                        print('Translating Passage {}'.format(trans_cnt), end=', ')
                        t1 = time()
                    continue
            else:  # Should not be triggered
                print('Comment Area Exception')

        # Deal with code blocks wrapped in "```"
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

        # Deal with ref area:
        if is_note(line, pos=0, check_path=True):
            if tr_buf != '':
                trans_write(ot_buf, tr_buf)
                trans_cnt += 1
                ot_buf = ''
                tr_buf = ''
            if not ref_area:
                ref_area = True
                print('Skipping Ref Block {}'.format(ref_cnt), end=', ')
                ref_cnt += 1
                t1 = time()
            fo.write(line)
            continue

        # Normal lines
        # Deal with a single linebreak
        if line == '\n':
            if ot_buf == '':
                fo.write('\n')
                continue
            trans_write(ot_buf, tr_buf)
            trans_cnt += 1
            ot_buf = ''
            tr_buf = ''
            continue
        # Start of normal lines
        if ot_buf == '':
            print('Translating Passage {}'.format(trans_cnt), end=', ')
            t1 = time()
        ot_buf += line

        # for beginning with special char, restore line break
        tr_buf = buf_add(tr_buf, line)

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
