import os
import time
import itertools
from tqdm import tqdm
import threading
from datetime import datetime, timedelta
from optparse import OptionParser

class DictMaker:
    """
    python -l 指定長度製作
    python dict_maker.py -l 4 -n -a
    result: 0000 -> zzzz

    python -p 透過 pattern 製作
    python dict_maker.py -p 022******* -n
    result: 0220000000 -> 0229999999

    python -s 指定符號 製作
    python dict_maker.py -4 -n -e @#-
    result: 0000 -> @999 -> ###
    """
    _PROGRESS_BAR = None

    _DEFAULT_DIR = './tmp'

    _DEFAULT_PREFIX = 'dict'

    _DEFAULT_DELIMITER = '-'

    _DEFAULT_MARK = '*'

    _DEFAULT_EXT = 'txt'

    _LENGTH_LIMIT = 50

    _PROCEED_DAYS_LIMIT = 7

    _NUMERIC_SET = {chr(_) for _ in range(ord('0'), ord('9') + 1)}  # 48-57

    _UPPER_CASE_SET = {chr(_) for _ in range(ord('A'), ord('Z') + 1)}  # 65-90

    _LOWER_CASE_SET = {chr(_) for _ in range(ord('a'), ord('z') + 1)}  # 97-122

    _SYMBOL_SET = set("~!@#$%^&_+-=,.?'")

    @staticmethod
    def _get_args():
        option = OptionParser()
        option.add_option('-f', '--file-path', action='store', type='string', dest='file_path', default=None)
        option.add_option('-l', '--length', action='store', type='int', dest='length', default=0)
        option.add_option('-p', '--pattern', action='store', type='string', dest='pattern', default=None)
        option.add_option('-m', '--mark', action='store', type='string', dest='mark', default=None)
        option.add_option('-R', '--reference', action='store', type='string', dest='reference', default=None)
        option.add_option('-N', '--number', action='store_true', dest='has_number', default=False)
        option.add_option('-U', '--upper-case-letter', action='store_true', dest='has_upper_case', default=False)
        option.add_option('-L', '--lower-case-letter', action='store_true', dest='has_lower_case', default=False)
        option.add_option('-S', '--symbol', action='store_true', dest='has_symbol', default=False)
        return option.parse_args()[0]

    @classmethod
    def _is_auto_create_file(cls, filename):
        return filename.startswith(f'{cls._DEFAULT_PREFIX}-') and filename.endswith(f'.{cls._DEFAULT_EXT}')

    @classmethod
    def _get_default_pathname(cls):
        os.makedirs(cls._DEFAULT_DIR, exist_ok=True)
        files = list(filter(cls._is_auto_create_file, os.listdir(cls._DEFAULT_DIR)))
        numbers = sorted([int(_.replace(f'.{cls._DEFAULT_EXT}', '').split(cls._DEFAULT_DELIMITER)[-1]) for _ in files])
        number = 1 if not numbers else numbers[-1] + 1
        return os.path.abspath(f'{cls._DEFAULT_DIR}/'
                               f'{cls._DEFAULT_PREFIX}{cls._DEFAULT_DELIMITER}{number}.'
                               f'{cls._DEFAULT_EXT}')

    @classmethod
    def _parse_pathname(cls, file_path):
        pathname = cls._get_default_pathname() if not file_path else os.path.abspath(file_path)
        if os.path.isfile(pathname):
            print(f'[{"WARNING":8}] [ * {pathname} is already exist!, overwrite? (y/n)]')
            if not input('>>> ').lower() in {'y', 'yes'}:
                exit(f'[{"WARNING":8}] [ * Program has been terminated!]')
        os.makedirs(os.path.split(pathname)[0], exist_ok=True)
        return pathname

    @classmethod
    def _parse_mark(cls, mark):
        if not mark:
            return cls._DEFAULT_MARK
        if len(mark) > 1:
            raise ValueError('-m, --mark, Single character only!')
        return mark

    @classmethod
    def _parse_pattern(cls, pattern, mark):
        if not pattern:
            return None
        if mark not in pattern:
            raise ValueError(f'-p, --pattern, Must contain the mark [-m, --mark, default: \"{cls._DEFAULT_MARK}\"].')
        return pattern

    @classmethod
    def _parse_length(cls, length):
        if length > cls._LENGTH_LIMIT:
            error_info = (f'-l, --length, Over the length limit: {cls._LENGTH_LIMIT}.\n'
                          f'Add the following lines after import module to increase the limitation up to 100:\n\n'
                          f'from dict_maker import DictMaker\n'
                          f'DictMaker._LENGTH_LIMIT = 100\n')
            raise ValueError(error_info)
        return length if length > 0 else 0

    @staticmethod
    def _parse_reference(reference):
        if not reference:
            return set()
        return set(reference)

    # @staticmethod
    # def _sort_elements(elements):
        # """
        # [0-9][a-z][A-Z][SYMBOLS]
        # :param elements: elements to create dict
        # :type elements: set
        # """
        # ascii_upper = {_ for _ in elements if _.isascii() and _.islower()}
        # ascii_lower = {_ for _ in elements if _.isascii() and _.isupper()}
        # ascii_numbers = {_ for _ in elements if _.isascii() and _.isdigit()}
        # symbols = elements - ascii_upper - ascii_lower - ascii_numbers
        # return sorted(ascii_numbers) + sorted(ascii_upper) + sorted(ascii_lower) + sorted(symbols)

    @classmethod
    def _get_elements(cls, reference, has_number, has_upper_case, has_lower_case, has_symbol):
        """
        number: [0-9] -> length: 10
        upper case letter: [A-Z] -> length = 26
        lower case letter: [a-z] -> length = 26
        default symbol: [~!@#$%^&_+-=,.?'] -> length = 16
        """
        elements = cls._parse_reference(reference=reference)
        if has_number:
            elements |= cls._NUMERIC_SET
        if has_upper_case:
            elements |= cls._UPPER_CASE_SET
        if has_lower_case:
            elements |= cls._LOWER_CASE_SET
        if has_symbol:
            elements |= cls._SYMBOL_SET
        return elements
        # return cls._sort_elements(elements)

    # @classmethod
    # def _estimate(cls, amount, pattern, elements, test_amount=10000, test_number=10):
        # os.makedirs('/tmp', exist_ok=True)
        # if amount < test_amount:
            # return
        # temps = list()
        # for i in range(test_number):
            # start = time.time()
            # text = ''.join(f'{pattern}\n' for _ in range(test_amount))
            # with open('/tmp/dict_maker_estimate.temp', 'w') as fw:
                # fw.write(text)
            # temps.append(time.time() - start)
        # consume = int(sum(temps)/len(temps) * amount/test_amount /len(elements))
        # print(len(elements))
        # if consume > 60 * 60 * 24 * cls._PROCEED_DAYS_LIMIT:
            # raise Exception(f'[{"ERROR":8}] [ * Too large to proceed! '
                            # f'It will take over {cls._PROCEED_DAYS_LIMIT} days.]')
        # estimate = datetime.now() + timedelta(seconds=consume)
        # print(f'[{"INFO":8}] [ * Estimate finished at {estimate.strftime("%Y-%m-%d %H:%M:%S")}]')
        # if consume > 30 * 60:
            # print(f'[{"WARNING":8}] [ * It will take over 30 minutes, Move on? (y/n)]')
            # if not input('>>> ').lower() in {'y', 'yes'}:
                # exit(f'[{"WARNING":8}] [ * Program has been terminated!]')

    @staticmethod
    def _get_mask(pattern, mark):
        return {k: v for k, v in enumerate(pattern) if v != mark}

    @classmethod
    def _generate_dict(cls, pattern, elements, mark):
        mask = cls._get_mask(pattern, mark)
        results = set()
        for comb in tqdm(list(itertools.product(elements, repeat=len(pattern))), ascii=True):
            # yield ''.join(mask[k] if k in mask else v for k, v in enumerate(comb))
            results.add(''.join(mask[k] if k in mask else v for k, v in enumerate(comb)))
        return results

    @classmethod
    def _create_dict(cls, pathname, pattern, mark, elements):
        amount = pow(len(elements), pattern.count(mark))
        # cls._estimate(amount, pattern, elements)
        start = time.time()
        results = cls._generate_dict(pattern, elements, mark)
        with open(pathname, 'w') as fw:
            fw.write(''.join(f'{_}\n' for _ in sorted(results)))
        print(f'[{"INFO":8}] [ * Consume {round(time.time() - start, 3)} seconds]')
        print(f'[{"INFO":8}] [ * saved to {pathname}]')

    @classmethod
    def run(cls):
        args = cls._get_args()
        pathname = cls._parse_pathname(args.file_path)
        mark = cls._parse_mark(args.mark)
        length = cls._parse_length(length=args.length)
        pattern = cls._parse_pattern(pattern=args.pattern, mark=mark) or (mark * length)
        print(pattern)
        if not pattern:
            raise ValueError('[-p, --pattern] [-l, --length], either one of them is required!')
        elements = cls._get_elements(reference=args.reference,
                                     has_number=args.has_number,
                                     has_upper_case=args.has_upper_case,
                                     has_lower_case=args.has_lower_case,
                                     has_symbol=args.has_symbol)
        if not elements:
            error_info = ('[-N, --number] [-U, --upper-case-letter] [-L, --lower-case-letter] '
                          '[-S, --symbol] [-R, --reference], either one of them is required!')
            raise ValueError(error_info)
        cls._create_dict(pathname=pathname, pattern=pattern, mark=mark, elements=elements)
        print('DONE!')

if __name__ == '__main__':
    DictMaker.run()
