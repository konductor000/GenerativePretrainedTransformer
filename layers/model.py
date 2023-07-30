import torch
import torch.nn.functional as F
from .embeddings import TokenEmbedding, PositionalEncoding
from .decoder import DecoderStack

class Transformer(torch.nn.Module):
    def __init__(
            self,
            number_of_tokens,
            max_sequence_length=512,
            embedding_size=512,
            number_of_layers=6,
            number_of_heads=4,
            extention_factor=4,
            dropout_rate=0.1
    ):
        super().__init__()

        self.number_of_tokens = number_of_tokens
        self.max_sequence_length = max_sequence_length
        self.embedding_size = embedding_size
        self.number_of_layers = number_of_layers
        self.number_of_heads = number_of_heads
        self.extention_factor = extention_factor

        self.dropout_rate = dropout_rate

        self.token_embedding = TokenEmbedding(embedding_size, number_of_tokens)

        self.positional_encoding = PositionalEncoding(embedding_size, max_sequence_length)

        self.layer_normalization = torch.nn.LayerNorm(embedding_size)

        self.decoder = DecoderStack(
            embedding_size=embedding_size,
            number_of_layers=number_of_layers,
            number_of_heads=number_of_heads,
            extention_factor=self.extention_factor,
            dropout_rate=dropout_rate,
            max_sequence_length=max_sequence_length
        )

        self.lm_head = LMHead(embedding_size, number_of_tokens)

    def forward(self, x, mask):
        token_embeddings = self.token_embedding(x)

        positional_encoding = self.positional_encoding(token_embeddings)

        positional_encoding_normalized = self.layer_normalization(positional_encoding)

        decoder_outputs = self.decoder(positional_encoding_normalized, mask)

        lm_head_outputs = self.lm_head(decoder_outputs)

        return lm_head_outputs


class LMHead(torch.nn.Module):
    def __init__(self, embedding_size, number_of_tokens):
        super().__init__()
        self.embedding_size = embedding_size
        self.number_of_tokens = number_of_tokens
        self.linear = torch.nn.Linear(embedding_size, number_of_tokens)

    def forward(self, x):
        linear_output = self.linear(x)

        return linear_output


class AutoregressiveWrapper(torch.nn.Module):
    def __init__(self, gpt_model):
        super().__init__()
        self.model = gpt_model
        self.max_sequence_length = self.model.max_sequence_length

    def forward(self, x, mask):
        inp, target = x[:, :-1], x[:, 1:]
        mask = mask[:, :-1]

        output = self.model(inp, mask)
        return output, target

    def next_token_probabilities(self, x, mask, temperature=1.0):
        logits = self.model(x, mask)[:, -1]

        logits = logits / temperature

        probabilities = torch.softmax(logits, dim=-1)

        return probabilities
    

if __name__ == '__main__':
    model = Transformer(number_of_tokens=10)
    wrapper = AutoregressiveWrapper(model, max_sequence_length=512)
