from collections.abc import AsyncGenerator, Iterable

import pytest

from createagents.application.dtos.streaming_response_dto import (
    StreamingResponseDTO,
)


async def mock_generator(tokens: Iterable[str]) -> AsyncGenerator[str, None]:
    for token in tokens:
        yield token


@pytest.mark.unit
class TestStreamingResponseDTO:
    @pytest.mark.asyncio
    async def test_scenario_initialization_success(self):
        gen = mock_generator(['token1', 'token2'])
        dto = StreamingResponseDTO(gen)
        assert dto._consumed is False
        assert dto._full_response == ''

    @pytest.mark.asyncio
    async def test_scenario_async_iteration_success(self):
        tokens = ['Hello', ' ', 'World']
        gen = mock_generator(tokens)
        dto = StreamingResponseDTO(gen)

        collected = [token async for token in dto]

        assert collected == tokens
        assert dto._consumed is True
        assert dto._full_response == 'Hello World'

    @pytest.mark.asyncio
    async def test_scenario_async_iteration_empty_generator(self):
        gen = mock_generator([])
        dto = StreamingResponseDTO(gen)

        collected = [token async for token in dto]

        assert collected == []
        assert dto._consumed is True
        assert dto._full_response == ''

    @pytest.mark.asyncio
    async def test_scenario_await_consumes_all_tokens(self):
        tokens = ['Token', '1', ' ', 'Token', '2']
        gen = mock_generator(tokens)
        dto = StreamingResponseDTO(gen)

        result = await dto
        assert result == 'Token1 Token2'
        assert dto._consumed is True

    @pytest.mark.asyncio
    async def test_scenario_await_on_already_consumed(self):
        tokens = ['Test']
        gen = mock_generator(tokens)
        dto = StreamingResponseDTO(gen)

        first_result = await dto
        second_result = await dto

        assert first_result == 'Test'
        assert second_result == 'Test'
        assert dto._consumed is True

    @pytest.mark.asyncio
    async def test_scenario_iteration_after_consumed_raises_stop(self):
        tokens = ['A', 'B']
        gen = mock_generator(tokens)
        dto = StreamingResponseDTO(gen)

        await dto

        collected = [token async for token in dto]

        assert collected == []

    @pytest.mark.asyncio
    async def test_scenario_str_unconsumed(self):
        gen = mock_generator(['test'])
        dto = StreamingResponseDTO(gen)

        result = str(dto)
        assert 'not consumed' in result

    @pytest.mark.asyncio
    async def test_scenario_str_consumed(self):
        gen = mock_generator(['Hello', ' ', 'World'])
        dto = StreamingResponseDTO(gen)

        await dto
        result = str(dto)
        assert result == 'Hello World'

    @pytest.mark.asyncio
    async def test_scenario_repr_active(self):
        gen = mock_generator(['test'])
        dto = StreamingResponseDTO(gen)

        result = repr(dto)
        assert 'active' in result

    @pytest.mark.asyncio
    async def test_scenario_repr_consumed(self):
        gen = mock_generator(['Test', 'ing'])
        dto = StreamingResponseDTO(gen)

        await dto
        result = repr(dto)
        assert 'consumed' in result
        assert 'length=7' in result

    @pytest.mark.asyncio
    async def test_scenario_partial_iteration_then_await(self):
        tokens = ['A', 'B', 'C', 'D']
        gen = mock_generator(tokens)
        dto = StreamingResponseDTO(gen)

        first_item = await dto.__anext__()
        assert first_item == 'A'
        assert dto._full_response == 'A'

        result = await dto
        assert result == 'ABCD'
        assert dto._consumed is True
