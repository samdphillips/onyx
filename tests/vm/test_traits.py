
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


def test_trait_rename():
    import onyx.objects as o
    m1 = object()
    m2 = object()
    ta = o.Trait('TA', {'a': m1, 'b': m2}, {})
    ta.rename(['a', 'b'], ['b', 'a'])
    assert ta.method_dict['a'] == m2
    assert ta.method_dict['b'] == m1
