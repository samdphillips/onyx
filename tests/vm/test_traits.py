
def test_merge_trait_to_class():
    import onyx.objects as o
    a = object()
    b = object()
    c = o.Class('Test', None, [], {}, {})
    t = o.Trait('TTest', {'method': a}, {'classmethod': b})
    c.merge_trait(t)
    assert 'method' in c.method_dict
    assert 'classmethod' in c.class_method_dict
    assert c.method_dict['method'] == a
    assert c.class_method_dict['classmethod'] == b


def test_merge_trait_to_trait():
    import onyx.objects as o
    m1_1 = object()
    m1_2 = object()
    m2_1 = object()
    m2_2 = object()
    ta = o.Trait('A', {'a': m1_1}, {'b': m1_2})
    tb = o.Trait('B', {'c': m2_1}, {'d': m2_2})
    ta.merge_trait(tb)
    assert ta.method_dict['a'] == m1_1
    assert ta.method_dict['c'] == m2_1
    assert ta.class_method_dict['b'] == m1_2
    assert ta.class_method_dict['d'] == m2_2


def test_trait_rename():
    import onyx.objects as o
    m1 = object()
    m2 = object()
    m3 = object()
    m4 = object()
    ta = o.Trait('TA', {'a': m1, 'b': m2, 'e': m4}, {'c': m3})
    ta.rename(['a', 'b', 'c'], ['b', 'a', 'd'])
    assert ta.method_dict['a'] == m2
    assert ta.method_dict['b'] == m1
    assert ta.method_dict['e'] == m4
    assert ta.class_method_dict['d'] == m3
    assert 'c' not in ta.class_method_dict
