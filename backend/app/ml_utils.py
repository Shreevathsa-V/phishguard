import numpy as np
import tensorflow as tf

def clean_text(text: str) -> str:
    return text.lower().strip()

def load_model(path: str):
    return tf.keras.models.load_model(path)

def load_tokenizer(path: str):
    """Load tokenizer from JSON"""
    from tensorflow.keras.preprocessing.text import tokenizer_from_json
    with open(path, "r") as f:
        data = f.read()   # read as string
    return tokenizer_from_json(data)


def predict_texts(model, tokenizer, texts, max_len: int = 200):
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    sequences = tokenizer.texts_to_sequences(texts)
    padded = pad_sequences(sequences, maxlen=max_len, padding="post", truncating="post")
    predictions = model.predict(padded, verbose=0)
    return np.squeeze(predictions)
