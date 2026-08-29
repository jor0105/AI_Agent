from typing import cast

import pytest

from createagents.domain import History, Message, MessageRole


@pytest.mark.unit
class TestHistory:
    def test_create_empty_history(self):
        history = History()

        assert len(history) == 0
        assert bool(history) is False
        assert history.get_messages() == []

    def test_history_default_max_size(self):
        history = History()
        assert history.max_size == 10

    def test_create_history_with_custom_max_size(self):
        history = History(max_size=5)

        assert history.max_size == 5

    def test_add_message_object(self):
        history = History()
        message = Message(role=MessageRole.USER, content='Hello')

        history.add(message)

        assert len(history) == 1
        assert history.get_messages()[0] == message

    @pytest.mark.parametrize(
        'method,expected_role,content',
        [
            ('add_user_message', MessageRole.USER, 'User message'),
            (
                'add_assistant_message',
                MessageRole.ASSISTANT,
                'Assistant response',
            ),
            ('add_system_message', MessageRole.SYSTEM, 'System instruction'),
        ],
    )
    def test_add_role_messages_via_helpers(
        self, method, expected_role, content
    ):
        history = History()
        getattr(history, method)(content)

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == expected_role
        assert messages[0].content == content

    def test_add_invalid_type_raises_error(self):
        history = History()

        with pytest.raises(
            TypeError, match='Only Message objects can be added'
        ):
            history.add(cast(Message, 'Not a message'))

    def test_add_user_message(self):
        history = History()

        history.add_user_message('User message')

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == 'User message'

    def test_add_assistant_message(self):
        history = History()

        history.add_assistant_message('Assistant response')

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == 'Assistant response'

    def test_add_system_message(self):
        history = History()

        history.add_system_message('System instruction')

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == 'System instruction'

    def test_add_multiple_messages(self):
        history = History()

        history.add_user_message('Message 1')
        history.add_assistant_message('Response 1')
        history.add_user_message('Message 2')
        history.add_assistant_message('Response 2')

        assert len(history) == 4

    def test_clear_history(self):
        history = History()
        history.add_user_message('Message 1')
        history.add_user_message('Message 2')

        assert len(history) == 2

        history.clear()

        assert len(history) == 0
        assert bool(history) is False

    def test_get_messages_returns_copy(self):
        history = History()
        history.add_user_message('Test')

        messages1 = history.get_messages()
        messages2 = history.get_messages()

        assert messages1 == messages2
        assert messages1 is not messages2

    def test_to_dict_list_empty(self):
        history = History()

        result = history.to_dict_list()

        assert result == []
        assert isinstance(result, list)

    def test_to_dict_list_with_messages(self):
        history = History()
        history.add_user_message('Hello')
        history.add_assistant_message('Hi there!')

        result = history.to_dict_list()

        assert len(result) == 2
        assert result[0] == {'role': 'user', 'content': 'Hello'}
        assert result[1] == {'role': 'assistant', 'content': 'Hi there!'}

    def test_from_dict_list_empty(self):
        data: list[dict[str, str]] = []
        history = History.from_dict_list(data, max_size=5)

        assert len(history) == 0

    def test_from_dict_list_with_messages(self):
        data = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi!'},
        ]

        history = History.from_dict_list(data, max_size=5)

        assert len(history) == 2
        messages = history.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == 'Hello'
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == 'Hi!'

    def test_from_dict_list_with_custom_max_size(self):
        data = [{'role': 'user', 'content': 'Test'}]
        history = History().from_dict_list(data, max_size=5)

        assert history.max_size == 5

    def test_history_max_size_limit(self):
        history = History(max_size=3)

        history.add_user_message('Msg 1')
        history.add_user_message('Msg 2')
        history.add_user_message('Msg 3')
        history.add_user_message('Msg 4')
        history.add_user_message('Msg 5')

        assert len(history) == 3
        messages = history.get_messages()
        assert messages[0].content == 'Msg 3'
        assert messages[1].content == 'Msg 4'
        assert messages[2].content == 'Msg 5'

    def test_history_invalid_max_size_raises(self):
        with pytest.raises(
            ValueError,
            match="The history's max size must be greater than zero",
        ):
            History(max_size=cast(int, None))
        with pytest.raises(
            ValueError,
            match="The history's max size must be greater than zero",
        ):
            History(max_size=0)
        with pytest.raises(
            ValueError,
            match="The history's max size must be greater than zero",
        ):
            History(max_size=-1)

    def test_history_trim_keeps_most_recent(self):
        history = History(max_size=10)

        for i in range(15):
            history.add_user_message(f'Message {i}')

        assert len(history) == 10
        messages = history.get_messages()
        assert messages[0].content == 'Message 5'
        assert messages[-1].content == 'Message 14'

    def test_history_bool_true_when_has_messages(self):
        history = History()
        history.add_user_message('Test')

        assert bool(history) is True

    def test_history_bool_false_when_empty(self):
        history = History()

        assert bool(history) is False

    def test_history_len_returns_correct_count(self):
        history = History()

        assert len(history) == 0

        history.add_user_message('Msg 1')
        assert len(history) == 1

        history.add_assistant_message('Msg 2')
        assert len(history) == 2

        history.clear()
        assert len(history) == 0

    def test_to_dict_list_and_from_dict_list_roundtrip(self):
        original = History(max_size=10)
        original.add_user_message('User msg')
        original.add_assistant_message('Assistant msg')
        original.add_system_message('System msg')

        dict_list = original.to_dict_list()
        reconstructed = History.from_dict_list(dict_list, max_size=10)

        assert len(original) == len(reconstructed)
        original_messages = original.get_messages()
        reconstructed_messages = reconstructed.get_messages()

        for orig, recon in zip(
            original_messages, reconstructed_messages, strict=True
        ):
            assert orig == recon

    def test_history_with_alternating_messages(self):
        history = History(max_size=20)

        for i in range(5):
            history.add_user_message(f'User {i}')
            history.add_assistant_message(f'Assistant {i}')

        assert len(history) == 10
        messages = history.get_messages()

        for i in range(0, 10, 2):
            assert messages[i].role == MessageRole.USER
            assert messages[i + 1].role == MessageRole.ASSISTANT

    def test_history_preserves_message_order(self):
        history = History()

        history.add_user_message('First')
        history.add_assistant_message('Second')
        history.add_user_message('Third')

        messages = history.get_messages()

        assert messages[0].content == 'First'
        assert messages[1].content == 'Second'
        assert messages[2].content == 'Third'

    def test_history_with_special_characters(self):
        history = History(max_size=1)
        special_content = 'Hello! 你好 🎉 @#$%'

        history.add_user_message(special_content)

        messages = history.get_messages()
        assert messages[0].content == special_content

    def test_history_with_multiline_content(self):
        history = History()
        multiline = 'Line 1\nLine 2\nLine 3'

        history.add_user_message(multiline)

        messages = history.get_messages()
        assert messages[0].content == multiline

    def test_history_from_dict_list_preserves_order(self):
        data = [
            {'role': 'user', 'content': 'First'},
            {'role': 'assistant', 'content': 'Second'},
            {'role': 'user', 'content': 'Third'},
        ]
        history = History.from_dict_list(data, max_size=10)

        messages = history.get_messages()
        assert len(messages) == 3
        assert messages[0].content == 'First'
        assert messages[1].content == 'Second'
        assert messages[2].content == 'Third'

    def test_history_add_multiple_same_type(self):
        history = History()

        history.add_user_message('User 1')
        history.add_user_message('User 2')
        history.add_user_message('User 3')

        messages = history.get_messages()
        assert len(messages) == 3
        assert all(msg.role == MessageRole.USER for msg in messages)

    def test_history_clear_on_empty_history(self):
        history = History()
        history.clear()

        assert len(history) == 0
        assert bool(history) is False

    def test_history_max_size_boundary(self):
        history = History(max_size=5)

        for i in range(5):
            history.add_user_message(f'Msg {i}')

        assert len(history) == 5

        history.add_user_message('Msg 5')

        assert len(history) == 5
        messages = history.get_messages()
        assert messages[0].content == 'Msg 1'

    def test_history_to_dict_list_empty(self):
        history = History()
        result = history.to_dict_list()

        assert result == []
        assert isinstance(result, list)


@pytest.mark.unit
class TestHistoryDequePerformance:
    def test_history_uses_deque_internally(self):
        from collections import deque

        history = History(max_size=5)
        assert isinstance(history._messages, deque)

    def test_deque_maxlen_is_set_correctly(self):
        history = History(max_size=5)
        assert history._messages.maxlen == 5

    def test_deque_auto_removes_old_messages(self):
        history = History(max_size=3)

        history.add_user_message('Msg 1')
        history.add_user_message('Msg 2')
        history.add_user_message('Msg 3')
        history.add_user_message('Msg 4')
        messages = history.get_messages()
        assert len(messages) == 3
        assert messages[0].content == 'Msg 2'
        assert messages[1].content == 'Msg 3'
        assert messages[2].content == 'Msg 4'

    def test_get_messages_returns_list_not_deque(self):
        history = History(max_size=5)
        history.add_user_message('Test')

        messages = history.get_messages()
        assert isinstance(messages, list)
        assert not isinstance(messages, type(history._messages))


@pytest.mark.unit
class TestHistoryConcurrency:
    def test_history_concurrent_additions_basic(self):
        import threading

        history = History(max_size=100)
        num_threads = 10
        messages_per_thread = 20

        def add_messages(thread_id):
            for i in range(messages_per_thread):
                history.add_user_message(f'Thread {thread_id} - Message {i}')

        threads = [
            threading.Thread(target=add_messages, args=(i,))
            for i in range(num_threads)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(history) == 100

        messages = history.get_messages()
        for msg in messages:
            assert msg.role == MessageRole.USER
            assert 'Thread' in msg.content

    def test_history_concurrent_additions_respects_max_size(self):
        import threading

        max_size = 50
        history = History(max_size=max_size)
        num_threads = 5
        messages_per_thread = 30

        def add_messages(thread_id):
            for i in range(messages_per_thread):
                history.add_user_message(f'T{thread_id}-M{i}')

        threads = [
            threading.Thread(target=add_messages, args=(i,))
            for i in range(num_threads)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(history) == max_size

    def test_history_concurrent_reads_and_writes(self):
        import threading
        import time

        history = History(max_size=100)
        num_writers = 5
        num_readers = 5
        messages_per_writer = 20
        reads_per_reader = 30
        read_results = []
        read_lock = threading.Lock()

        def writer(thread_id):
            for i in range(messages_per_writer):
                history.add_user_message(f'Writer {thread_id} - Msg {i}')
                time.sleep(0.001)

        def reader(thread_id):
            for _ in range(reads_per_reader):
                messages = history.get_messages()
                with read_lock:
                    read_results.append(len(messages))
                time.sleep(0.001)

        writer_threads = [
            threading.Thread(target=writer, args=(i,))
            for i in range(num_writers)
        ]
        reader_threads = [
            threading.Thread(target=reader, args=(i,))
            for i in range(num_readers)
        ]

        all_threads = writer_threads + reader_threads
        for thread in all_threads:
            thread.start()
        for thread in all_threads:
            thread.join()

        assert len(read_results) == num_readers * reads_per_reader
        for result in read_results:
            assert 0 <= result <= 100
        assert len(history) <= 100

    def test_history_concurrent_clear_and_add(self):
        import threading
        import time

        history = History(max_size=50)
        num_adders = 3
        num_clearers = 2
        operations_per_thread = 20

        def adder(thread_id):
            for i in range(operations_per_thread):
                history.add_user_message(f'Adder {thread_id} - {i}')
                time.sleep(0.001)

        def clearer(thread_id):
            for _ in range(operations_per_thread):
                history.clear()
                time.sleep(0.002)

        adder_threads = [
            threading.Thread(target=adder, args=(i,))
            for i in range(num_adders)
        ]
        clearer_threads = [
            threading.Thread(target=clearer, args=(i,))
            for i in range(num_clearers)
        ]

        all_threads = adder_threads + clearer_threads
        for thread in all_threads:
            thread.start()
        for thread in all_threads:
            thread.join()

        assert len(history) <= 50
        messages = history.get_messages()
        assert isinstance(messages, list)

    def test_history_concurrent_different_message_types(self):
        import threading

        history = History(max_size=90)
        messages_per_thread = 30

        def add_user_messages():
            for i in range(messages_per_thread):
                history.add_user_message(f'User {i}')

        def add_assistant_messages():
            for i in range(messages_per_thread):
                history.add_assistant_message(f'Assistant {i}')

        def add_system_messages():
            for i in range(messages_per_thread):
                history.add_system_message(f'System {i}')

        threads = [
            threading.Thread(target=add_user_messages),
            threading.Thread(target=add_assistant_messages),
            threading.Thread(target=add_system_messages),
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(history) == 90

        messages = history.get_messages()
        roles = {msg.role for msg in messages}
        assert len(roles) >= 1
        assert all(
            role
            in [MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM]
            for role in roles
        )

    def test_history_concurrent_to_dict_list(self):
        import threading

        history = History(max_size=100)
        dict_results = []
        dict_lock = threading.Lock()

        def add_and_convert(thread_id):
            for i in range(10):
                history.add_user_message(f'Thread {thread_id} - {i}')
                dict_list = history.to_dict_list()
                with dict_lock:
                    dict_results.append(len(dict_list))

        threads = [
            threading.Thread(target=add_and_convert, args=(i,))
            for i in range(5)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(dict_results) == 50
        for result in dict_results:
            assert 0 <= result <= 100

    def test_history_concurrent_stress_test(self):
        import threading

        history = History(max_size=200)
        num_threads = 20
        operations_per_thread = 50
        errors = []

        def stress_operations(thread_id):
            try:
                for i in range(operations_per_thread):
                    if i % 4 == 0:
                        history.add_user_message(f'T{thread_id}-{i}')
                    elif i % 4 == 1:
                        history.add_assistant_message(f'T{thread_id}-{i}')
                    elif i % 4 == 2:
                        _ = history.get_messages()
                    else:
                        _ = history.to_dict_list()
            # Capture worker failures for the assertion after all threads finish.
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=stress_operations, args=(i,))
            for i in range(num_threads)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0, f'Errors found: {errors}'
        assert len(history) <= 200

        messages = history.get_messages()
        assert len(messages) == len(history)
        for msg in messages:
            assert isinstance(msg, Message)
            assert msg.content is not None
            assert len(msg.content) > 0
