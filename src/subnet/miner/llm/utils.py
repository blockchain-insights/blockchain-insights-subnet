from langchain_core.messages import AIMessage
from transformers import GPT2Tokenizer

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")


def split_messages_into_chunks(messages, max_tokens: int = 1024):
    chunks = []
    current_chunk = []
    current_tokens = 0

    for message in messages:
        message_tokens = tokenizer.encode(message.content, truncation=False)

        # If adding this message exceeds max_tokens, split the message
        while current_tokens + len(message_tokens) > max_tokens:
            # Calculate the remaining tokens space in the current chunk
            remaining_tokens = max_tokens - current_tokens

            # Split the message content to fit into the remaining tokens
            split_message_content = tokenizer.decode(message_tokens[:remaining_tokens],
                                                     clean_up_tokenization_spaces=False)
            current_chunk.append(AIMessage(split_message_content))
            chunks.append(current_chunk)

            # Prepare for the next chunk
            current_chunk = []
            current_tokens = 0
            message_tokens = message_tokens[remaining_tokens:]

        # Add the rest of the message to the current chunk
        current_chunk.append(AIMessage(tokenizer.decode(message_tokens, clean_up_tokenization_spaces=False)))
        current_tokens += len(message_tokens)

    # Add the last chunk if it has any messages
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def get_message_token_count(message):
    tokens = tokenizer.encode(message)
    
    print(f'gpt2 tokens {len(tokens)}')
    
    return len(tokens)