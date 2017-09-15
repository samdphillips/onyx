
def test_lookup_self_from_block():
    from onyx.vm.env import BlockEnv, MethodEnv
    klass = object()
    obj = object()
    m_env = MethodEnv(klass, obj)
    env = BlockEnv(m_env)
    v = env.lookup('self').value
    assert v == obj

def test_lookup_super_from_block():
    from onyx.vm.env import BlockEnv, MethodEnv
    cls = object()
    obj = object()
    m_env = MethodEnv(cls, obj)
    env = BlockEnv(m_env)
    v = env.lookup('super').value
    assert v.receiver == obj
    assert v.cls == cls
