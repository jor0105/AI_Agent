from collections.abc import AsyncGenerator
from typing import ClassVar

from ...domain import (
    Agent,
    ChatException,
    ChatMetrics,
    LoggerInterface,
    NullLogger,
)
from ..dtos import ChatInputDTO, ChatOutputDTO
from ..interfaces import ChatRepository


class ChatWithAgentUseCase:
    """Use case for handling chat interactions with an AI agent.

    This class orchestrates the process of sending a user message to an agent,
    receiving the response, sanitizing the output, and updating the agent's
    conversation history. It also handles error management and logging during
    the interaction.
    """

    #: Maps a data-shape failure to its `(log label, caller-facing message)`.
    #: Keyed by exact type; a subclass falls back to the generic entry below.
    __DATA_ERRORS: ClassVar[dict[type[Exception], tuple[str, str]]] = {
        ValueError: ('Validation error', 'Validation error during chat'),
        TypeError: ('Type error', 'Type error during chat'),
        KeyError: (
            'Error processing response',
            'Error processing AI response',
        ),
        AttributeError: ('Attribute error', 'Attribute error during chat'),
    }
    __DEFAULT_DATA_ERROR = ('Error', 'Error during chat')

    def __init__(
        self,
        chat_repository: ChatRepository,
        logger: LoggerInterface | None = None,
    ) -> None:
        """Initialize the use case with its dependencies.

        Args:
            chat_repository: Repository for AI communication.
            logger: Optional logger injected by the composition root.

        """
        self.__chat_repository = chat_repository
        self.__logger = logger or NullLogger()

    async def execute(
        self, agent: Agent, input_dto: ChatInputDTO
    ) -> ChatOutputDTO | AsyncGenerator[str, None]:
        """Send a message to the agent and return the response.

        Args:
            agent: The agent instance.
            input_dto: DTO with the user's message.

        Returns:
            Union[ChatOutputDTO, AsyncGenerator[str, None]]: The agent's response.
                - ChatOutputDTO: Complete response (if stream=False)
                - AsyncGenerator: Token stream (if stream=True)

        Raises:
            ValueError: If the input data is invalid.
            ChatException: If an error occurs during AI communication.

        """
        input_dto.validate()

        self.__logger.info(
            "Running chat with agent '%s' (model: %s)", agent.name, agent.model
        )
        self.__logger.debug('User message: %s...', input_dto.message[:100])

        try:
            response = await self.__chat_repository.chat(
                model=agent.model,
                instructions=agent.instructions,
                config=agent.config,
                tools=agent.tools,
                history=agent.history.to_dict_list(),
                user_ask=input_dto.message,
            )

            if isinstance(response, AsyncGenerator):
                return self.__handle_streaming(agent, input_dto, response)

            # Standard non-streaming response
            if not response:
                self.__logger.error('Empty response received from repository')
                raise ChatException('Empty response received from repository')

            output_dto = ChatOutputDTO(response=response)

            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(response)

            self.__logger.info('Chat executed successfully')
            self.__logger.debug(
                'Response (first 100 chars): %s...', response[:100]
            )

            return output_dto

        except ChatException:
            self.__logger.exception('ChatException during chat execution')
            raise
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            log_label, user_message = self.__DATA_ERRORS.get(
                type(e), self.__DEFAULT_DATA_ERROR
            )
            self.__logger.exception('%s', log_label)
            raise ChatException(f'{user_message}: {e!s}') from e
        except Exception as e:
            self.__logger.exception('Unexpected error')
            raise ChatException(
                f'Unexpected error during communication with AI: {e!s}',
                original_error=e,
            ) from e

    async def __handle_streaming(
        self,
        agent: Agent,
        input_dto: ChatInputDTO,
        stream: AsyncGenerator[str, None],
    ) -> AsyncGenerator[str, None]:
        """Handle streaming responses by yielding tokens and preserving chat history.

        This method creates a wrapper generator that:
        1. Yields tokens as they arrive from the underlying stream
        2. Accumulates the complete response
        3. Updates the agent's conversation history after streaming completes

        Args:
            agent: The agent instance.
            input_dto: DTO with the user's message.
            stream: The token generator from the repository.

        Yields:
            str: Individual tokens from the model's response.

        Raises:
            ChatException: If an error occurs during streaming.

        """
        full_response = []

        try:
            self.__logger.info(
                'Starting streaming response for agent: %s', agent.name
            )
            async for token in stream:
                full_response.append(token)
                yield token

            # Streaming completed successfully
            complete_text = ''.join(full_response)
            if not complete_text:
                self.__logger.error('Empty response received from stream')
                raise ChatException('Empty response received from stream')

            # Update agent's conversation history
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(complete_text)
            self.__logger.info('Streaming chat executed successfully')
            self.__logger.debug(
                'Complete response (first 100 chars): %s...',
                complete_text[:100] if complete_text else '',
            )

        except ChatException:
            self.__logger.exception('ChatException during streaming')
            raise
        except Exception as e:
            self.__logger.exception('Error during streaming')
            raise ChatException(
                f'Error during streaming: {e!s}',
                original_error=e,
            ) from e

    def get_metrics(self) -> list[ChatMetrics]:
        """Return the metrics collected by the chat repository.

        Returns:
            A list of metrics collected during interactions.

        """
        return self.__chat_repository.get_metrics()
