"""
py.test -v sorting_str.py

# yum install python_devel
pip install psutil memory_profiler
python -m memory_profiler sorting_str.py
"""


STR_TMPL = '{{0:0>{0}}}{{0:1>{1}}}{{0:2>{2}}}{{0:3>{3}}}{{0:4>{4}}}{{0:5>{5}}}{{0:6>{6}}}{{0:7>{7}}}{{0:8>{8}}}{{0:9>{9}}}'


def counters_to_str(counters):
    return STR_TMPL.format(*counters).format('')


def str_to_counters(incoming_str):
    counters_ = [0]*10
    for s in incoming_str:
        counters_[int(s)] += 1
    return counters_


def test_str_to_counters():
    assert str_to_counters('') == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert str_to_counters('5') == [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    assert str_to_counters('1234567890') == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    assert str_to_counters('112223') == [0, 2, 3, 1, 0, 0, 0, 0, 0, 0]


def test_counters_to_str():
    assert counters_to_str([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]) == ''
    assert counters_to_str([0, 0, 0, 0, 0, 1, 0, 0, 0, 0]) == '5'
    assert counters_to_str([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]) == '0123456789'
    assert counters_to_str([0, 2, 3, 1, 0, 0, 0, 0, 0, 0]) == '112223'


def test_sorting():
    assert counters_to_str(str_to_counters('')) == ''
    assert counters_to_str(str_to_counters('4321')) == '1234'
    assert counters_to_str(str_to_counters('002221134567890')) == '000112223456789'


if __name__ == '__main__':
    import string
    from memory_profiler import profile


    @profile
    def _sorting():
        non_sort_str = string.digits*10000000  # ~95Mb
        counters = str_to_counters(non_sort_str)
        non_sort_str = None
        res = counters_to_str(counters)
        return res


    sosted = _sorting()
