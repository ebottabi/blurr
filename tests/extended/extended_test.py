from datetime import datetime, timezone

from blurr.core.store_key import Key, KeyType
from blurr.runner.local_runner import LocalRunner


def test_extended_runner():
    local_runner = LocalRunner('tests/extended/stream.yml')
    local_runner.execute(
        local_runner.get_identity_records_from_json_files(['tests/extended/raw.json']))

    assert len(local_runner._per_user_data) == 1
    assert len(local_runner._per_user_data['user-1'][0]) == 4

    result_state = local_runner._per_user_data['user-1'][0][Key(KeyType.DIMENSION, 'user-1',
                                                                'state')]
    expected_state = {
        '_identity': 'user-1',
        'country': 'US',
        'build': 245,
        'is_paid': True,
        'os_name': 'ios',
        'os_version': '7.1.1',
        'max_level_completed': 7,
        'offers_purchased': {
            'offer1': 1
        },
        'badges': {'silver', 'bronze', 'gold'},
        'signin_method': 'other'
    }
    # Assert the badges is a list and then convert to set for unordered comparison.
    # badges in BTS is a set but we encode it into a list when creating a snapshot. The creation of
    # the list cant result in a non-deterministic element order in the list.
    assert result_state['badges']
    assert isinstance(result_state['badges'], list)
    result_state['badges'] = set(result_state['badges'])

    assert result_state == expected_state

    result_session = local_runner._per_user_data['user-1'][0][Key(KeyType.DIMENSION, 'user-1',
                                                                  'session', ['session-3'])]
    expected_session = {
        '_identity': 'user-1',
        '_start_time': datetime(2016, 2, 12, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        '_end_time': datetime(2016, 2, 13, 0, 1, 25, tzinfo=timezone.utc).isoformat(),
        'session_id': 'session-3',
        'events': 11,
        'games_won': 2,
        'levels_played': [6, 6, 7, 8],
        'badges': {
            'bronze': 1,
            'gold': 1
        },
        'start_score': 18,
        'end_score': 71
    }
    assert result_session == expected_session

    result_session_10 = local_runner._per_user_data['user-1'][0][Key(KeyType.DIMENSION, 'user-1',
                                                                     'session', ['session-1'])]
    expected_session_10 = {
        '_identity': 'user-1',
        '_start_time': datetime(2016, 2, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        '_end_time': datetime(2016, 2, 10, 0, 1, 47, tzinfo=timezone.utc).isoformat(),
        'session_id': 'session-1',
        'events': 4,
        'games_won': 1,
        'levels_played': [1, 5],
        'badges': {
            'bronze': 1
        },
        'start_score': 0,
        'end_score': 57
    }

    assert result_session_10 == expected_session_10

    result_session_11 = local_runner._per_user_data['user-1'][0][Key(KeyType.DIMENSION, 'user-1',
                                                                     'session', ['session-2'])]
    expected_session_11 = {
        '_identity': 'user-1',
        '_start_time': datetime(2016, 2, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
        '_end_time': datetime(2016, 2, 11, 0, 0, 28, tzinfo=timezone.utc).isoformat(),
        'session_id': 'session-2',
        'events': 7,
        'games_won': 1,
        'levels_played': [5, 6],
        'badges': {
            'silver': 1
        },
        'start_score': 0,
        'end_score': 18
    }

    assert result_session_11 == expected_session_11
