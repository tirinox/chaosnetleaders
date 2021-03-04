import pytest

from helpers.config import Config


@pytest.fixture
def example_config1():
    return Config(data={
        'test': {
            'foo': 10,
            'bar': '3344str'
        },
        'sub': {
            'arr': [
                20,
                30,
                {'gamma': 33},
                40,
                50,
                60
            ]
        },
        'key': 'val134'
    })


def test_sub_config(example_config1):
    cfg = example_config1
    assert cfg.get('key', default='nothing') == 'val134'
    assert str(cfg.get('key')) == 'val134'
    assert isinstance(cfg.get(), dict)
    assert cfg.get('no_key', default=42) == 42

    assert int(cfg.get('test . foo')) == 10
    assert cfg.get('test . foo', 15) == 10
    assert cfg.get('test . baz', 15) == 15

    assert cfg.get('sub.arr.0', 0) == 20
    assert cfg.get('sub.arr.1', 0) == 30
    assert cfg.get('sub.arr.6', 0) == 0
    assert cfg.get('sub.arr.100', 0) == 0

    sub = cfg.get('sub')
    assert isinstance(sub.get(), dict)
    assert sub.get('arr.2.gamma', 0) == 33
    assert sub.get('arr.3', 0) == 40
